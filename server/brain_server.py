"""
Siddhivinayak brain server (port 5060).

  POST /api/chat          {message, thread_id}  → {answer, sources, tools, scene, llm}
  POST /api/learn         multipart file (+ module)  → saves into knowledge/<module>/ and learns it
  GET  /api/knowledge     modules, files and indexing status
  GET  /api/page          ?doc_id=..&page=N  → PNG render of the original page (real formulas)
  GET  /api/health

A background watcher re-scans knowledge folders, so files you copy in by hand are learned too.

Run:  venv\\Scripts\\python server\\brain_server.py
"""

import re
import threading
import time
import traceback

from flask import Flask, abort, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from brain.agent import chat
from brain.config import (BRAIN_PORT, KNOWLEDGE_DIR, PAGE_CACHE_DIR, SUPPORTED_EXTS,
                          WATCH_INTERVAL_SEC, resolve_llm)
from brain.store import kb

app = Flask(__name__)
CORS(app)


@app.get("/api/health")
def health():
    provider, model = resolve_llm()
    return jsonify({"status": "ok", "llm": f"{provider}/{model}" if provider else None,
                    "chunks": len(kb.chunks), "index": kb.status})


@app.post("/api/chat")
def api_chat():
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "empty message"}), 400
    try:
        return jsonify(chat(message, thread_id=data.get("thread_id") or "default"))
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500


@app.post("/api/learn")
def api_learn():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "no file"}), 400
    name = secure_filename(f.filename)
    if not name or "." + name.rsplit(".", 1)[-1].lower() not in SUPPORTED_EXTS:
        return jsonify({"error": f"unsupported type; use one of {sorted(SUPPORTED_EXTS)}"}), 400
    module = re.sub(r"[^a-z0-9_-]", "", (request.form.get("module") or "inbox").lower()) or "inbox"
    dest = KNOWLEDGE_DIR / module
    dest.mkdir(parents=True, exist_ok=True)
    f.save(dest / name)
    result = kb.sync()
    return jsonify({"module": module, "file": name, **result})


@app.get("/api/knowledge")
def api_knowledge():
    files = [{"doc_id": k, "file": v["file"], "module": v["module"], "chunks": v["chunks"],
              "indexed_at": v["indexed_at"]} for k, v in kb.manifest.items()]
    return jsonify({"modules": kb.modules(), "files": files, "status": kb.status})


@app.get("/api/page")
def api_page():
    doc_id = request.args.get("doc_id", "")
    page = int(request.args.get("page", "1"))
    path = kb.doc_path(doc_id)
    if not path or path.suffix.lower() != ".pdf" or not path.exists():
        abort(404)
    out = PAGE_CACHE_DIR / f"{doc_id}-{page}.png"
    if not out.exists():
        import pymupdf

        with pymupdf.open(path) as doc:
            if not 1 <= page <= len(doc):
                abort(404)
            doc[page - 1].get_pixmap(dpi=130).save(out)
    return send_file(out, mimetype="image/png", max_age=86400)


def watcher():
    while True:
        try:
            r = kb.sync()
            if r.get("added") or r.get("removed"):
                print(f"[brain] watcher: {r}")
        except Exception:
            traceback.print_exc()
        time.sleep(WATCH_INTERVAL_SEC)


if __name__ == "__main__":
    threading.Thread(target=watcher, daemon=True).start()
    provider, model = resolve_llm()
    print(f"[brain] LLM: {provider + '/' + model if provider else 'none (offline retrieval mode)'}")
    print(f"[brain] knowledge: {len(kb.chunks)} chunks; serving on http://127.0.0.1:{BRAIN_PORT}")
    app.run(host="127.0.0.1", port=BRAIN_PORT, debug=False, threaded=True)
