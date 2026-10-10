"""
Local hybrid knowledge base.

- Dense search: fastembed (BAAI/bge-small, ONNX on CPU, no GPU or API needed)
- Sparse search: BM25 (catches exact terms such as "E7018", "M12", "Reynolds")
- Fusion: reciprocal-rank fusion of both lists
- Incremental: files are fingerprinted (size + mtime); only changed files are re-embedded
"""

import hashlib
import json
import re
import threading
import time
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from .config import (DATA_DIR, EMBED_MODEL, EXTRA_SOURCES, INDEX_DIR, KNOWLEDGE_DIR,
                     SUPPORTED_EXTS)
from .loaders import chunk_document

TOKEN = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN.findall(text)]


class KnowledgeBase:
    def __init__(self):
        self.lock = threading.RLock()
        self.chunks: list[dict] = []
        self.vectors = np.zeros((0, 384), dtype=np.float32)
        self.manifest: dict[str, dict] = {}
        self.bm25 = None
        self._embedder = None
        self.status = {"state": "idle", "detail": ""}
        self._load()

    # ── persistence ──────────────────────────────────────────────────
    def _load(self):
        chunks_f, vec_f, man_f = INDEX_DIR / "chunks.jsonl", INDEX_DIR / "vectors.npy", INDEX_DIR / "manifest.json"
        if chunks_f.exists() and vec_f.exists() and man_f.exists():
            with chunks_f.open(encoding="utf-8") as f:
                self.chunks = [json.loads(line) for line in f]
            self.vectors = np.load(vec_f)
            self.manifest = json.loads(man_f.read_text(encoding="utf-8"))
            if len(self.chunks) != len(self.vectors):
                self.chunks, self.vectors, self.manifest = [], np.zeros((0, 384), np.float32), {}
        self._rebuild_bm25()

    def _save(self):
        tmp = INDEX_DIR / "chunks.jsonl.tmp"
        with tmp.open("w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        tmp.replace(INDEX_DIR / "chunks.jsonl")
        np.save(INDEX_DIR / "vectors.npy", self.vectors)
        (INDEX_DIR / "manifest.json").write_text(json.dumps(self.manifest, indent=1), encoding="utf-8")

    def _rebuild_bm25(self):
        self.bm25 = BM25Okapi([tokenize(c["heading"] + " " + c["text"]) for c in self.chunks]) if self.chunks else None

    @property
    def embedder(self):
        if self._embedder is None:
            from fastembed import TextEmbedding

            self.status = {"state": "loading", "detail": f"loading embedding model {EMBED_MODEL}"}
            self._embedder = TextEmbedding(model_name=EMBED_MODEL, cache_dir=str(DATA_DIR / "models"))
            self.status = {"state": "idle", "detail": ""}
        return self._embedder

    # ── discovery & sync ─────────────────────────────────────────────
    def discover(self) -> dict[str, tuple[Path, str]]:
        """doc_id -> (path, module) for every supported file on disk."""
        found = {}
        roots = [(d, d.name) for d in KNOWLEDGE_DIR.iterdir() if d.is_dir()]
        roots += [(p, m) for m, p in EXTRA_SOURCES.items() if p.exists()]
        for root, module in roots:
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTS and not path.name.startswith("~$"):
                    doc_id = module + "-" + hashlib.sha1(str(path.resolve()).encode()).hexdigest()[:10]
                    found[doc_id] = (path, module)
        return found

    def sync(self) -> dict:
        """Index new/changed files, drop deleted ones. Safe to call repeatedly."""
        with self.lock:
            found = self.discover()
            removed = [d for d in self.manifest if d not in found]
            changed = []
            for doc_id, (path, module) in found.items():
                st = path.stat()
                fp = f"{st.st_size}-{int(st.st_mtime)}"
                if self.manifest.get(doc_id, {}).get("fingerprint") != fp:
                    changed.append((doc_id, path, module, fp))
            if not removed and not changed:
                return {"added": 0, "removed": 0}

            drop = set(removed) | {c[0] for c in changed}
            keep = [i for i, c in enumerate(self.chunks) if c["doc_id"] not in drop]
            self.chunks = [self.chunks[i] for i in keep]
            self.vectors = self.vectors[keep] if len(keep) else np.zeros((0, 384), np.float32)
            for d in removed:
                self.manifest.pop(d, None)

            added = 0
            for doc_id, path, module, fp in changed:
                self.status = {"state": "indexing", "detail": f"reading {path.name}"}
                t0 = time.time()
                new_chunks = chunk_document(path, module, doc_id)
                if new_chunks:
                    self.status = {"state": "indexing", "detail": f"embedding {len(new_chunks)} chunks of {path.name}"}
                    texts = [f"{c['heading']}\n{c['text']}" for c in new_chunks]
                    vecs = np.array(list(self.embedder.embed(texts, batch_size=64)), dtype=np.float32)
                    self.chunks.extend(new_chunks)
                    self.vectors = np.vstack([self.vectors, vecs]) if len(self.vectors) else vecs
                self.manifest[doc_id] = {
                    "path": str(path), "file": path.name, "module": module, "fingerprint": fp,
                    "chunks": len(new_chunks), "indexed_at": time.strftime("%Y-%m-%d %H:%M"),
                    "seconds": round(time.time() - t0, 1),
                }
                added += len(new_chunks)
                print(f"[brain] learned {path.name}: {len(new_chunks)} chunks in {time.time() - t0:.0f}s")
            self._rebuild_bm25()
            self._save()
            self.status = {"state": "idle", "detail": ""}
            return {"added": added, "removed": len(removed), "files": [c[1].name for c in changed]}

    # ── search ───────────────────────────────────────────────────────
    def search(self, query: str, module: str | None = None, k: int = 6) -> list[dict]:
        with self.lock:
            if not self.chunks:
                return []
            idx = np.arange(len(self.chunks))
            if module and module != "all":
                idx = np.array([i for i, c in enumerate(self.chunks) if c["module"] == module], dtype=int)
                if not len(idx):
                    return []
            qv = np.array(list(self.embedder.query_embed([query]))[0], dtype=np.float32)
            dense = self.vectors[idx] @ qv
            sparse = self.bm25.get_scores(tokenize(query))[idx]

            pool = 40
            rrf: dict[int, float] = {}
            for rank, j in enumerate(np.argsort(-dense)[:pool]):
                rrf[idx[j]] = rrf.get(idx[j], 0) + 1 / (60 + rank)
            for rank, j in enumerate(np.argsort(-sparse)[:pool]):
                if sparse[j] > 0:
                    rrf[idx[j]] = rrf.get(idx[j], 0) + 1 / (60 + rank)
            best = sorted(rrf.items(), key=lambda kv: -kv[1])[:k]
            return [{**self.chunks[i], "score": round(s, 4)} for i, s in best]

    # ── info ─────────────────────────────────────────────────────────
    def modules(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for d in self.manifest.values():
            m = out.setdefault(d["module"], {"files": 0, "chunks": 0})
            m["files"] += 1
            m["chunks"] += d["chunks"]
        for d in KNOWLEDGE_DIR.iterdir():
            if d.is_dir():
                out.setdefault(d.name, {"files": 0, "chunks": 0})
        return out

    def doc_path(self, doc_id: str) -> Path | None:
        d = self.manifest.get(doc_id)
        return Path(d["path"]) if d else None


kb = KnowledgeBase()
