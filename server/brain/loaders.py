"""
Document loaders: turn any supported file into a list of "pages"
({page: int, text: str}) and then into overlapping, heading-aware chunks.
"""

import json
import re
from pathlib import Path

from .config import CHUNK_CHARS, CHUNK_OVERLAP

# Running headers/footers that repeat on every page of the GATE handbook and add only noise.
BOILERPLATE = re.compile(
    r"^\s*(GATE WALLAH MECHANICAL HANDBOOK|PW|PEDIA|GATE)\s*$", re.IGNORECASE
)
# "5.3.2 Local/Temporal Acceleration" or "1.1 Introduction" style section headings
HEADING = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,2}){1,3})\s+([A-Z][^\n]{2,80})$")


def load_pages(path: Path) -> list[dict]:
    ext = path.suffix.lower()
    if ext == ".pdf":
        import pymupdf

        with pymupdf.open(path) as doc:
            return [{"page": i + 1, "text": p.get_text()} for i, p in enumerate(doc)]
    if ext == ".docx":
        import docx

        d = docx.Document(str(path))
        parts = [p.text for p in d.paragraphs]
        for table in d.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text.strip() for c in row.cells))
        return [{"page": 1, "text": "\n".join(parts)}]
    if ext == ".pptx":
        from pptx import Presentation

        pres = Presentation(str(path))
        pages = []
        for i, slide in enumerate(pres.slides):
            texts = [sh.text_frame.text for sh in slide.shapes if sh.has_text_frame]
            pages.append({"page": i + 1, "text": "\n".join(texts)})
        return pages
    if ext == ".json":
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        return [{"page": 1, "text": json.dumps(data, indent=1, ensure_ascii=False)}]
    return [{"page": 1, "text": path.read_text(encoding="utf-8", errors="ignore")}]


def _clean(text: str) -> str:
    lines = [ln.rstrip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln.strip() and not BOILERPLATE.match(ln)]
    text = "\n".join(lines)
    # PDF formula extraction yields lots of one-symbol lines; join them back.
    text = re.sub(r"\n(?=.{1,3}\n)", " ", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def _markdown_heading(line: str):
    m = re.match(r"^#{1,4}\s+(.+)$", line.strip())
    return m.group(1).strip() if m else None


def chunk_document(path: Path, module: str, doc_id: str) -> list[dict]:
    pages = load_pages(path)
    chunks: list[dict] = []
    heading = ""
    for pg in pages:
        text = _clean(pg["text"])
        if len(text) < 40:
            continue
        for line in text.splitlines()[:12]:
            m = HEADING.match(line)
            h = (f"{m.group(1)} {m.group(2).strip()}" if m else None) or _markdown_heading(line)
            if h:
                heading = h
                break
        # Markdown/plain files are one big "page": split on headings first.
        sections = re.split(r"\n(?=#{1,4} )", text) if path.suffix.lower() in {".md", ".markdown"} else [text]
        for section in sections:
            sec_heading = _markdown_heading(section.splitlines()[0]) or heading
            start = 0
            while start < len(section):
                end = min(len(section), start + CHUNK_CHARS)
                if end < len(section):
                    cut = section.rfind("\n", start + CHUNK_CHARS // 2, end)
                    end = cut if cut > 0 else end
                body = section[start:end].strip()
                if len(body) > 40:
                    chunks.append({
                        "id": f"{doc_id}:{pg['page']}:{len(chunks)}",
                        "doc_id": doc_id,
                        "module": module,
                        "file": path.name,
                        "page": pg["page"],
                        "heading": sec_heading,
                        "text": body,
                    })
                if end >= len(section):
                    break
                start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks
