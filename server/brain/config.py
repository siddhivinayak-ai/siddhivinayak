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
    "google_genai": "gemini-3.5-flash",
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

# ── Vision (teardown) ────────────────────────────────────────────────
# VISION_PROVIDER: groq | google_genai | anthropic   (default groq)
TEARDOWN_DIR = DATA_DIR / "teardowns"
DEFAULT_VISION_MODELS = {
    "groq": "qwen/qwen3.8-27b",
    "google_genai": "gemini-3.5-flash",
    "anthropic": "claude-opus-5-5",
}
VISION_KEYS = {"groq": "GROQ_API_KEY", "google_genai": "GOOGLE_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}


def resolve_vision():
    """Return (provider, model) for the teardown vision model, or (None, None) if its key is missing."""
    provider = os.getenv("VISION_PROVIDER", "").strip().lower() or "groq"
    if provider not in DEFAULT_VISION_MODELS or not os.getenv(VISION_KEYS[provider]):
        return None, None
    model = os.getenv("VISION_MODEL", "").strip() or DEFAULT_VISION_MODELS[provider]
    return provider, model


def vision_chain():
    """Primary vision model followed by fallbacks, keeping only those whose API key is set.

    Free tiers are shared capacity (Gemini answers 503 "high demand" at peak times, Groq caps tokens
    per minute), so a teardown walks this list until one model answers.
    VISION_FALLBACKS: comma-separated provider:model pairs.
    """
    chain = []
    primary = resolve_vision()
    if primary[0]:
        chain.append(primary)
    raw = os.getenv("VISION_FALLBACKS", "google_genai:gemini-flash-latest,groq:qwen/qwen3.8-27b")
    for item in raw.split(","):
        provider, _, model = item.strip().partition(":")
        provider = provider.strip().lower()
        if (provider in DEFAULT_VISION_MODELS and os.getenv(VISION_KEYS[provider])
                and (provider, model.strip()) not in chain):
            chain.append((provider, model.strip() or DEFAULT_VISION_MODELS[provider]))
    return chain


for d in (KNOWLEDGE_DIR, DATA_DIR, INDEX_DIR, PAGE_CACHE_DIR, TEARDOWN_DIR):
    d.mkdir(parents=True, exist_ok=True)
