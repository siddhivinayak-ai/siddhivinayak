"""
Teardown: photo of a product -> what it really costs to make.

  photo ─▶ vision LLM (physical facts only: parts, materials, mass, processes, retail guess)
        ─▶ engineering/costing.py (deterministic ₹ maths)
        ─▶ teardown JSON (docs/teardown-contract.md, section 3), saved in data/teardowns/

The LLM never outputs manufacturing cost; Python computes it.
"""

import base64
import io
import json
import random
import re
import threading
import time
from datetime import datetime

from .config import TEARDOWN_DIR, vision_chain

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_EDGE_PX = 1024
JPEG_QUALITY = 85
VISION_MAX_TOKENS = 1200
# Groq's free tier also caps OUTPUT tokens per minute (qwen3.8-27b: 1000 OTPM) and counts the requested
# max_tokens against it, so a request above that cap is rejected outright.
GROQ_MAX_TOKENS = 900

STANDARD_ASSUMPTIONS = [
    "Made in India/China at ~100k units per year",
    "Material prices are 2025–26 bulk averages",
    "Excludes R&D, marketing, retailer margin and GST",
]

# Rough conversion so markup is always computed in INR (costing is INR-only).
INR_PER = {"INR": 1.0, "USD": 84.0, "EUR": 91.0, "GBP": 107.0, "AED": 22.9, "JPY": 0.56, "CNY": 11.6}

ID_RE = re.compile(r"^td_\d{8}_\d{6}_[0-9a-f]{4}$")


class TeardownError(Exception):
    """Carries the HTTP status the route should answer with."""

    def __init__(self, message: str, status: int = 502, retry_after_s: float | None = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.retry_after_s = retry_after_s


def _costing():
    # Imported lazily so this module (and its tests) load even before costing.py exists.
    from .engineering import costing

    return costing


# ── Image ────────────────────────────────────────────────────────────

def prepare_image(raw: bytes) -> bytes:
    """Validate an upload (jpg/png/webp, ≤ 8 MB) and return a downscaled JPEG."""
    if not raw:
        raise TeardownError("empty image", 400)
    if len(raw) > MAX_IMAGE_BYTES:
        raise TeardownError("image too large (max 8 MB)", 400)
    from PIL import Image, ImageOps

    try:
        img = Image.open(io.BytesIO(raw))
        fmt = (img.format or "").upper()
        if fmt not in {"JPEG", "PNG", "WEBP", "MPO"}:
            raise TeardownError("unsupported image type; use jpg, png or webp", 400)
        img = ImageOps.exif_transpose(img)
    except TeardownError:
        raise
    except Exception:
        raise TeardownError("could not read image; use jpg, png or webp", 400)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((MAX_EDGE_PX, MAX_EDGE_PX), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue()


# ── Vision prompt + call ─────────────────────────────────────────────

PROMPT = """You are a manufacturing cost engineer doing a teardown from one photo.
Identify the product and estimate its PHYSICAL build only. Do NOT output any manufacturing cost.
{hint}
Return ONLY one JSON object, no prose, no markdown:
{{"object":{{"name":str,"category":str,"description":str (1 sentence),"confidence":0-1}},
"estimated_retail_inr":number (typical Indian retail price for this kind of product),
"components":[{{"name":str,"material_id":str,"mass_g":number,"qty":int,"process_ids":[str],"notes":str}}],
"assumptions":[short str],
"fun_fact":str (one engineering fact about how it is made)}}
Rules:
- List the real separate parts (usually 3 to 8, max 8; a one-piece object may have 1-2); mass_g is per piece, qty = pieces per product. A part made in one piece (moulded, cast or fired together) is ONE component; coatings/glazes go in that part's process_ids.
- If it is sold as a pair or set (shoes, earbuds...), cover the whole pair/set via qty.
- Estimate each mass physically: size from the photo x wall thickness -> volume (cm3) x density.
- material_id and process_ids MUST be ids from this catalog:
{catalog}"""

REPAIR_PROMPT = """Your previous reply was not valid JSON. Rewrite it as ONE valid JSON object with the \
same content and keys, nothing else (no markdown, no comments, no trailing commas).
Previous reply:
{reply}"""


def _make_llm(provider: str, model: str):
    from langchain.chat_models import init_chat_model

    # One attempt per model with a short timeout: on failure the next model in vision_chain() takes over.
    kwargs = {"max_tokens": VISION_MAX_TOKENS, "max_retries": 0, "timeout": 45}
    if provider == "groq":
        # Groq's free tier counts max_tokens against an 8k tokens/minute budget: keep reasoning short + hidden.
        kwargs = {"max_tokens": GROQ_MAX_TOKENS, "max_retries": 0, "request_timeout": 45}
        # Hidden reasoning still counts as output, and the whole JSON must fit in GROQ_MAX_TOKENS:
        # qwen supports turning reasoning off; gpt-oss only goes down to "low".
        if "qwen" in model:
            kwargs["reasoning_effort"] = "none"
            kwargs["reasoning_format"] = "hidden"
        elif "gpt-oss" in model:
            kwargs["reasoning_effort"] = "low"
    elif provider == "google_genai":
        # Thinking tokens count as output on Gemini, so leave headroom; quota is per-request, not max_tokens.
        kwargs = {"max_tokens": 4096, "max_retries": 0, "timeout": 45, "reasoning_effort": "low",
                  "response_mime_type": "application/json"}
    elif provider == "anthropic":
        kwargs = {"max_tokens": 2048, "max_retries": 0, "default_request_timeout": 45}
    return init_chat_model(model, model_provider=provider, **kwargs)


def _text_of(msg) -> str:
    c = getattr(msg, "content", msg)
    if isinstance(c, str):
        return c
    return "".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")


def _retry_after(e: Exception) -> float | None:
    resp = getattr(e, "response", None)
    headers = getattr(resp, "headers", None) or {}
    try:
        if headers.get("retry-after"):
            return float(headers["retry-after"])
    except (TypeError, ValueError):
        pass
    m = re.search(r"(?:try again|retry) in\s*(?:(\d+)m)?\s*([\d.]+)\s*s", str(e), re.I)
    if m:
        return round(int(m.group(1) or 0) * 60 + float(m.group(2)), 1)
    return None


def _is_rate_limit(e: Exception) -> bool:
    if getattr(e, "status_code", None) == 429 or getattr(getattr(e, "response", None), "status_code", None) == 429:
        return True
    s = f"{type(e).__name__} {e}"
    return "RateLimit" in s or "429" in s or "RESOURCE_EXHAUSTED" in s or "rate_limit" in s


def _as_teardown_error(e: Exception) -> TeardownError:
    if _is_rate_limit(e) and "request too large" in str(e).lower():
        # Not a transient limit: this request can never fit the per-minute budget.
        return TeardownError(f"vision request exceeds the model's per-minute token cap: {str(e)[:200]}", 502)
    if _is_rate_limit(e):
        ra = _retry_after(e)
        return TeardownError("vision model is rate limited, try again shortly", 429, ra if ra is not None else 30.0)
    return TeardownError(f"vision model failed: {type(e).__name__}: {str(e)[:300]}", 502)


# provider/model that answered the most recent call_vision() on this thread (for the teardown's "model" field)
_served = threading.local()


def served_model() -> str:
    return getattr(_served, "name", "")


def call_vision(content) -> str:
    """Send one human message (str or list of content parts) to the first vision model in the
    fallback chain that answers; return its text."""
    chain = vision_chain()
    if not chain:
        raise TeardownError("no vision model configured (set GOOGLE_API_KEY or GROQ_API_KEY in server/.env)", 502)
    from langchain_core.messages import HumanMessage

    errors = []
    for provider, model in chain:
        try:
            msg = _make_llm(provider, model).invoke([HumanMessage(content=content)])
        except Exception as e:
            err = _as_teardown_error(e)
            errors.append(err)
            print(f"[brain] vision {provider}/{model} failed, trying next: {err.message[:120]}")
            continue
        usage = getattr(msg, "usage_metadata", None) or {}
        print(f"[brain] vision {provider}/{model}: in={usage.get('input_tokens')} out={usage.get('output_tokens')}")
        _served.name = f"{provider}/{model}"
        return _text_of(msg)
    # Every model failed: report a rate limit if any model was merely busy, so the UI shows "try again in Ns".
    limited = [e for e in errors if e.status == 429]
    raise min(limited, key=lambda e: e.retry_after_s or 30) if limited else errors[-1]


# ── JSON extraction / validation ─────────────────────────────────────

def extract_json(text: str) -> dict:
    """Pull the outermost {...} out of a model reply; tolerate fences, <think>, trailing commas."""
    if not text:
        raise ValueError("empty reply")
    t = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    t = re.sub(r"```(?:json)?", "", t, flags=re.I)
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in reply")
    t = t[start:end + 1]
    try:
        obj = json.loads(t)
    except json.JSONDecodeError:
        obj = json.loads(re.sub(r",\s*([}\]])", r"\1", t))
    if not isinstance(obj, dict):
        raise ValueError("reply is not a JSON object")
    return obj


def _num(v, default=None):
    if isinstance(v, bool):
        return default
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        m = re.search(r"-?\d[\d,]*\.?\d*", v)
        if m:
            try:
                return float(m.group(0).replace(",", ""))
            except ValueError:
                pass
    return default


def _clean_id(v) -> str:
    return re.sub(r"[^a-z0-9_]", "_", str(v or "").strip().lower()).strip("_")


def validate(raw: dict) -> dict:
    """Clamp the model's estimate into something costing can trust."""
    obj = raw.get("object") if isinstance(raw.get("object"), dict) else {}
    conf = _num(obj.get("confidence"), 0.5)
    if conf > 1:  # model answered as a percentage
        conf /= 100
    out_obj = {
        "name": str(obj.get("name") or raw.get("name") or "Unknown object").strip()[:120],
        "category": str(obj.get("category") or "other").strip()[:60],
        "description": str(obj.get("description") or "").strip()[:300],
        "confidence": round(min(1.0, max(0.0, conf)), 2),
    }
    comps = []
    for c in raw.get("components") or []:
        if not isinstance(c, dict):
            continue
        mass = _num(c.get("mass_g"), 0.0)
        if not mass or mass <= 0:
            continue
        procs = c.get("process_ids") or []
        if isinstance(procs, str):
            procs = re.split(r"[,;/]", procs)
        procs = [p for p in (_clean_id(p) for p in procs) if p]
        comps.append({
            "name": str(c.get("name") or "Part").strip()[:80],
            "material_id": _clean_id(c.get("material_id")) or "unknown",
            "mass_g": round(min(mass, 49_999.0), 1),
            "qty": int(min(100, max(1, round(_num(c.get("qty"), 1) or 1)))),
            "process_ids": list(dict.fromkeys(procs))[:5],
            "notes": str(c.get("notes") or "").strip()[:200],
        })
    if not comps:
        raise ValueError("no usable components")
    retail = _num(raw.get("estimated_retail_inr"))
    if retail is None and isinstance(raw.get("price"), dict):
        retail = _num(raw["price"].get("estimated_retail"))
    assumptions = [str(a).strip()[:140] for a in (raw.get("assumptions") or []) if str(a).strip()][:5]
    return {
        "object": out_obj,
        "estimated_retail_inr": round(retail, 1) if retail and retail > 0 else None,
        "components": comps[:8],
        "assumptions": assumptions,
        "fun_fact": str(raw.get("fun_fact") or "").strip()[:300],
    }


def analyse_image(jpeg: bytes, hint: str = "") -> dict:
    """Vision call + robust parse with ONE text-only repair retry. Returns validate()d dict."""
    hint = (hint or "").strip()[:200]
    prompt = PROMPT.format(catalog=_costing().catalog_for_prompt(),
                           hint=f'User hint about the object: "{hint}"' if hint else "")
    b64 = base64.b64encode(jpeg).decode()
    reply = call_vision([{"type": "text", "text": prompt},
                         {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}])
    try:
        return validate(extract_json(reply))
    except (ValueError, json.JSONDecodeError):
        pass
    repaired = call_vision(REPAIR_PROMPT.format(reply=(reply or "")[:4000]))
    try:
        return validate(extract_json(repaired))
    except (ValueError, json.JSONDecodeError) as e:
        raise TeardownError(f"vision model did not return usable JSON ({e})", 502)


# ── Money + narration ────────────────────────────────────────────────

def inr(x: float) -> str:
    """₹1,499 / ₹1,49,999 (Indian grouping); paise shown only under ₹10."""
    if x < 10:
        s = f"{x:.1f}".rstrip("0").rstrip(".")
        return f"₹{s}"
    n = str(int(round(x)))
    if len(n) > 3:
        head, tail = n[:-3], n[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        n = ",".join(groups + [tail])
    return f"₹{n}"


_WORDS = {2: "twice", 3: "three times", 4: "four times", 5: "five times", 6: "six times", 7: "seven times",
          8: "eight times", 9: "nine times", 10: "ten times", 11: "eleven times", 12: "twelve times"}


def _times(multiple: float) -> str:
    if multiple < 1.95:
        return f"{multiple:.1f} times"
    n = int(multiple + 0.5)
    return _WORDS.get(n, f"{n} times")


def _short_name(name: str) -> str:
    s = re.sub(r"\s*\(.*?\)", "", name).strip()
    s = re.split(r",| with | for | - ", s, flags=re.I)[0].strip()
    words = s.split()
    if len(words) > 8:
        s = " ".join(words[:8])
    if not s:
        return "thing"
    # "Ceramic Tea Cup" -> "ceramic tea cup", but keep brand-like names ("Converse All Star") as written.
    return s.lower() if all(w[:1].isupper() or not w[:1].isalpha() for w in words) and len(words) <= 4         and not any(w.isupper() and len(w) > 1 for w in words) else s


def make_narration(name: str, total: float, price_used: float, paid: bool, multiple: float,
                   top_material: str | None) -> str:
    thing = _short_name(name)
    last = thing.split()[-1].lower() if thing.split() else ""
    plural = last.endswith("s") and not last.endswith(("ss", "us", "is"))  # sneakers, earbuds; not glass
    first = f"{'These' if plural else 'This'} {thing} {'cost' if plural else 'costs'} about {inr(total)} to make."
    price = f"You paid {inr(price_used)}" if paid else f"It usually sells for around {inr(price_used)}"
    t = _times(multiple)
    if multiple < 1.0:
        mid = f"{price}, which is less than it costs the factory."
        end = "Someone is selling this at a loss, or it was made far cheaper than I think."
    elif multiple < 2:
        mid = f"{price}, only {t} the factory cost."
        end = "That's a fair deal: most of your money is real material and work."
    elif multiple < 4:
        mid = f"{price}, about {t} what it costs to make."
        end = "That's normal retail: shipping, the shop and tax take the rest."
    elif multiple < 8:
        mid = f"{price}, roughly {t} the factory cost."
        end = "You're paying a brand premium on top of the shop and shipping."
    elif multiple < 20:
        mid = f"{price}, so roughly {t} what it costs the factory."
        mat = f"the {top_material.lower()}" if top_material else "the parts"
        end = f"Most of the money is the brand and the shop, not {mat}."
    else:
        mid = f"{price}: about {t} the cost of making it."
        end = "That price is mostly marketing and margin, not engineering."
    for text in (f"{first} {mid} {end}", f"{first} {mid}", first):
        if len(text) <= 280:
            return text
    return first[:279] + "…"


# ── Assembly ─────────────────────────────────────────────────────────

def new_id(now: datetime | None = None) -> str:
    now = now or datetime.now()
    return f"td_{now:%Y%m%d_%H%M%S}_{random.getrandbits(16):04x}"


def pick_scene(components: list[dict], cost: dict, processes_table: dict) -> str:
    """Scene of the process with the highest summed cost (breakdown first, then per-component fallback)."""
    label_to_id = {v.get("label"): k for k, v in processes_table.items()}
    sums: dict[str, float] = {}
    for b in cost.get("breakdown") or []:
        if b.get("kind") == "process":
            pid = label_to_id.get(b.get("label"))
            if pid:
                sums[pid] = sums.get(pid, 0.0) + float(b.get("amount") or 0)
    if not sums:
        for c in components:
            ids = [p for p in c.get("process_ids", []) if p in processes_table]
            for p in ids:
                sums[p] = sums.get(p, 0.0) + float(c.get("cost") or 0) / len(ids)
    for pid in sorted(sums, key=sums.get, reverse=True):
        scene = processes_table.get(pid, {}).get("scene")
        if scene:
            return scene
    return "studio"


def build_teardown(est: dict, *, price_paid: float | None = None, currency: str = "INR",
                   model_name: str = "", now: datetime | None = None) -> dict:
    costing = _costing()
    now = now or datetime.now()
    comps = [dict(c) for c in est["components"]]
    full = costing.estimate_cost([{k: c[k] for k in ("name", "material_id", "mass_g", "process_ids", "qty")}
                                  for c in comps])
    full = dict(full)
    priced = full.pop("components", None) or []
    for c, p in zip(comps, priced):
        c["cost"] = round(float(p.get("cost") or 0), 1)
        c["material_label"] = p.get("material_label") or costing.MATERIALS.get(c["material_id"], {}).get("label", c["material_id"])
        c["process_labels"] = p.get("process_labels") or [costing.PROCESSES.get(i, {}).get("label", i) for i in c["process_ids"]]
    for c in comps[len(priced):]:
        c.setdefault("cost", 0.0)
        c.setdefault("material_label", c["material_id"])
        c.setdefault("process_labels", list(c["process_ids"]))
    ordered = [{"name": c["name"], "material_id": c["material_id"], "material_label": c["material_label"],
                "mass_g": c["mass_g"], "qty": c["qty"], "process_ids": c["process_ids"],
                "process_labels": c["process_labels"], "cost": c["cost"], "notes": c["notes"]} for c in comps]

    processes, seen = [], set()
    for c in ordered:
        for pid, label in zip(c["process_ids"], c["process_labels"]):
            if pid not in seen:
                seen.add(pid)
                processes.append({"id": pid, "label": label,
                                  "scene": costing.PROCESSES.get(pid, {}).get("scene", "studio")})

    total = float(full.get("total") or 0)
    extra = []
    retail = est.get("estimated_retail_inr")
    if not retail:
        retail = round(max(total, 1.0) * 4, 1)
        extra.append("Retail price not recognised; assumed 4x factory cost")
    paid = None
    if price_paid is not None:
        rate = INR_PER.get(currency, 1.0)
        paid = round(price_paid * rate, 1)
        if currency != "INR":
            extra.append(f"Price converted from {currency} at ₹{rate:g} per unit")
    price_used = paid if paid is not None else retail
    markup = costing.build_markup(total, price_used)

    material_rows = [b for b in full.get("breakdown") or [] if b.get("kind") == "material"]
    top_material = max(material_rows, key=lambda b: b.get("amount") or 0)["label"] if material_rows else None

    assumptions = list(dict.fromkeys(est.get("assumptions", []) + STANDARD_ASSUMPTIONS + extra))
    return {
        "id": new_id(now),
        "created_at": now.isoformat(timespec="seconds"),
        "object": est["object"],
        "price": {"paid": paid, "estimated_retail": retail, "currency": "INR"},
        "components": ordered,
        "processes": processes,
        "cost": full,
        "markup": markup,
        "assumptions": assumptions,
        "fun_fact": est.get("fun_fact", ""),
        "narration": make_narration(est["object"]["name"], total, float(markup.get("price_used") or price_used),
                                    paid is not None, float(markup.get("multiple") or 0), top_material),
        "scene": pick_scene(ordered, full, costing.PROCESSES),
        "model": model_name,
    }


def run_teardown(raw_image: bytes, *, price_paid: float | None = None, currency: str = "INR",
                 hint: str = "") -> dict:
    jpeg = prepare_image(raw_image)
    currency = (currency or "INR").strip().upper()
    if currency not in INR_PER:
        raise TeardownError(f"unsupported currency; use one of {sorted(INR_PER)}", 400)
    if price_paid is not None and not (0 < price_paid < 1e8):
        raise TeardownError("price_paid must be a positive number", 400)
    t0 = time.perf_counter()
    est = analyse_image(jpeg, hint)
    td = build_teardown(est, price_paid=price_paid, currency=currency, model_name=served_model())
    print(f"[brain] teardown {td['id']}: {td['object']['name']} -> {inr(td['cost']['total'])} "
          f"({time.perf_counter() - t0:.1f}s)")
    save(td, jpeg)
    return td


# ── Persistence ──────────────────────────────────────────────────────

def save(td: dict, jpeg: bytes) -> None:
    TEARDOWN_DIR.mkdir(parents=True, exist_ok=True)
    (TEARDOWN_DIR / f"{td['id']}.jpg").write_bytes(jpeg)
    (TEARDOWN_DIR / f"{td['id']}.json").write_text(json.dumps(td, ensure_ascii=False, indent=1), encoding="utf-8")


def get(td_id: str) -> dict | None:
    if not ID_RE.match(td_id or ""):
        return None
    p = TEARDOWN_DIR / f"{td_id}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def image_path(td_id: str):
    if not ID_RE.match(td_id or ""):
        return None
    p = TEARDOWN_DIR / f"{td_id}.jpg"
    return p if p.exists() else None


def list_teardowns(limit: int = 20) -> list[dict]:
    files = sorted(TEARDOWN_DIR.glob("td_*.json"), key=lambda p: p.name, reverse=True)
    items = []
    for p in files[:max(1, min(limit, 200))]:
        try:
            td = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        price = td.get("price") or {}
        items.append({
            "id": td.get("id"),
            "object": {"name": (td.get("object") or {}).get("name")},
            "cost": {"total": (td.get("cost") or {}).get("total")},
            "price": {"paid": price.get("paid"), "estimated_retail": price.get("estimated_retail"),
                      "used": price.get("paid") if price.get("paid") is not None else price.get("estimated_retail")},
            "markup": {"multiple": (td.get("markup") or {}).get("multiple")},
            "created_at": td.get("created_at"),
        })
    return items
