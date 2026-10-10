"""
Central configuration for the Siddhivinayak brain.

Everything is driven by server/.env so you can swap LLM providers
without touching code. See server/.env.example.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = SERVER_DIR.parent

load_dotenv(SERVER_DIR / ".env")

# ── Knowledge locations ──────────────────────────────────────────────
# Every sub-folder of KNOWLEDGE_DIR is a "module" (screws, welding, memory, ...).
# Drop any PDF / DOCX / PPTX / TXT / MD file into a module folder and it is learned.
KNOWLEDGE_DIR = SERVER_DIR / "knowledge"

# Extra folders mapped to a module name. Your notes PDF lives in assets/notes.
EXTRA_SOURCES = {
    "notes": PROJECT_DIR / "assets" / "notes",
}

DATA_DIR = SERVER_DIR / "data"
INDEX_DIR = DATA_DIR / "index"
PAGE_CACHE_DIR = DATA_DIR / "page_cache"
CHECKPOINT_DB = DATA_DIR / "conversations.sqlite"

SUPPORTED_EXTS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".markdown", ".csv", ".json"}

# ── Retrieval ────────────────────────────────────────────────────────
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5")
CHUNK_CHARS = int(os.getenv("CHUNK_CHARS", "1100"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "180"))
WATCH_INTERVAL_SEC = int(os.getenv("WATCH_INTERVAL_SEC", "15"))

# ── LLM provider ─────────────────────────────────────────────────────
# LLM_PROVIDER: anthropic | groq | google_genai | ollama   (blank = auto-detect)
DEFAULT_MODELS = {
    "anthropic": "claude-opus-5-5",
    "groq": "openai/gpt-oss-120b",
    "google_genai": "gemini-2.5-flash",
    "ollama": "llama3.1:8b",
}


def resolve_llm():
    """Return (provider, model) or (None, None) when no LLM is configured."""
    provider = os.getenv("LLM_PROVIDER", "").strip().lower() or None
    if provider is None:
        if os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("GROQ_API_KEY"):
            provider = "groq"
        elif os.getenv("GOOGLE_API_KEY"):
            provider = "google_genai"
        elif os.getenv("OLLAMA_HOST") or os.getenv("USE_OLLAMA"):
            provider = "ollama"
    if provider is None:
        return None, None
    model = os.getenv("LLM_MODEL", "").strip() or DEFAULT_MODELS.get(provider)
    return provider, model


BRAIN_PORT = int(os.getenv("BRAIN_PORT", "5060"))

for d in (KNOWLEDGE_DIR, DATA_DIR, INDEX_DIR, PAGE_CACHE_DIR):
    d.mkdir(parents=True, exist_ok=True)
