"""
The Siddhivinayak agent: a LangGraph tool-calling agent with persistent memory.

Graph:   user ─▶ model ─▶ (tools ─▶ model)* ─▶ answer
Memory:  SQLite checkpointer → every conversation thread survives restarts.
Fallback: with no LLM configured, answers come straight from hybrid retrieval.
"""

import re
import sqlite3

from .config import CHECKPOINT_DB, resolve_llm
from .scenes import detect_scene
from .store import kb
from .tools import ALL_TOOLS

SYSTEM_PROMPT = """You are Siddhivinayak — the AI twin of Siddhivinayak, a core manufacturing engineer \
who also codes. You are Siddhivinayak's engineering assistant for life: practical, precise, shop-floor aware.

How you work:
- For any engineering question, FIRST call search_knowledge to ground yourself in the learned notes and \
modules (notes = the Mechanical Engineering handbook PDF; screws; welding; memory = things you were taught). \
Search with specific technical terms; search again with different wording if results are thin.
- For numbers about threads, bolts, torque, joints, welding heat input, carbon equivalent or fillet welds, \
ALWAYS use the calculator tools. Never compute these in your head.
- When the user teaches you something, corrects you, or states a preference/plant practice, call remember.
- Be economical: usually ONE search_knowledge call is enough, at most two. Call each calculator once.
- Cite knowledge sources inline like (notes p.123) or (welding_reference.md). Do not cite tool names. \
If the knowledge base does not cover something, say so and answer from general engineering knowledge, marked clearly.
- Write formulas in LaTeX: $...$ inline and $$...$$ for display equations.
- Formulas in the PDF text are often garbled by extraction; reconstruct them carefully in clean notation \
and point to the page so the original can be checked.

Answer style (systematic):
1. One-line direct answer.
2. Key points / steps / formula with units.
3. Practical shop-floor note (failure modes, standards, rules of thumb) when relevant.
Keep it tight. Use Markdown. Speak like a confident senior engineer, warm but not chatty."""

_agent = None
_provider = None

# Free tiers (e.g. Groq: 8k tokens/minute) and small local models can't take a growing
# history, so for these providers older turns are compacted to plain question/answer text.
SMALL_CONTEXT_PROVIDERS = {"groq", "ollama", "google_genai"}
KEEP_PAST_MESSAGES = 6
PAST_MESSAGE_CHARS = 600


def _compact(messages):
    from langchain_core.messages import AIMessage, HumanMessage

    last_human = max((i for i, m in enumerate(messages) if m.type == "human"), default=0)
    past, current = messages[:last_human], messages[last_human:]
    kept = []
    for m in past:
        if m.type == "human":
            kept.append(HumanMessage(content=_text_of(m)[:PAST_MESSAGE_CHARS]))
        elif m.type == "ai" and not getattr(m, "tool_calls", None) and _text_of(m).strip():
            kept.append(AIMessage(content=_text_of(m)[:PAST_MESSAGE_CHARS]))
    kept = kept[-KEEP_PAST_MESSAGES:]
    while kept and kept[0].type != "human":
        kept.pop(0)
    return kept + current


def _make_compact_history():
    from langchain.agents.middleware import wrap_model_call

    @wrap_model_call
    def compact_history(request, handler):
        return handler(request.override(messages=_compact(request.messages)))

    return compact_history


def get_agent():
    global _agent, _provider
    provider, model = resolve_llm()
    if provider is None:
        return None
    if _agent is not None and _provider == (provider, model):
        return _agent

    from langchain.agents import create_agent
    from langchain.agents.middleware import ModelCallLimitMiddleware
    from langchain.chat_models import init_chat_model
    from langgraph.checkpoint.sqlite import SqliteSaver

    kwargs = {"max_tokens": 4096}
    if provider == "groq":
        # Groq's free tier counts the requested max_tokens against an 8k tokens/minute budget,
        # so keep each call small and keep reasoning short on reasoning models.
        kwargs = {"max_tokens": 1024, "max_retries": 3, "request_timeout": 90}
        if "gpt-oss" in model or "qwen" in model:
            kwargs["reasoning_effort"] = "low"
    elif provider == "ollama":
        kwargs = {"num_predict": 2048}
    llm = init_chat_model(model, model_provider=provider, **kwargs)
    conn = sqlite3.connect(str(CHECKPOINT_DB), check_same_thread=False)
    middleware = [ModelCallLimitMiddleware(run_limit=8, exit_behavior="end")]
    if provider in SMALL_CONTEXT_PROVIDERS:
        middleware.append(_make_compact_history())
    _agent = create_agent(llm, tools=ALL_TOOLS, system_prompt=SYSTEM_PROMPT,
                          checkpointer=SqliteSaver(conn), middleware=middleware)
    _provider = (provider, model)
    print(f"[brain] agent ready: {provider}/{model}")
    return _agent


def _text_of(msg) -> str:
    c = msg.content
    if isinstance(c, str):
        return c
    return "".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")


SOURCE_RE = re.compile(r"\[([^\]\n]+?) p\.(\d+)\] \(module=([\w-]+), doc_id=([\w-]+)\)")


def chat(message: str, thread_id: str = "default") -> dict:
    agent = get_agent()
    if agent is None:
        return _retrieval_only(message)

    from langchain_core.messages import ToolMessage

    result = agent.invoke({"messages": [{"role": "user", "content": message}]},
                          config={"configurable": {"thread_id": thread_id}, "recursion_limit": 25})
    msgs = result["messages"]
    # Only look at the messages produced in this turn (after the last human message).
    last_human = max(i for i, m in enumerate(msgs) if m.type == "human")
    turn = msgs[last_human + 1:]

    tools_used, sources = [], {}
    for m in turn:
        if isinstance(m, ToolMessage):
            tools_used.append(m.name)
            for file, page, module, doc_id in SOURCE_RE.findall(str(m.content)):
                sources.setdefault(f"{doc_id}:{page}", {"file": file, "page": int(page), "module": module, "doc_id": doc_id})
    answer = _text_of(turn[-1]) if turn else ""
    return {
        "answer": answer,
        "sources": list(sources.values())[:8],
        "tools": tools_used,
        "scene": detect_scene(message + " " + answer, tools_used),
        "llm": "/".join(_provider),
    }


def _retrieval_only(message: str) -> dict:
    hits = kb.search(message, k=4)
    if not hits:
        answer = ("I haven't learned anything about that yet. Drop a PDF/DOCX/notes file into a module folder "
                  "or upload it with the 📎 button and I'll learn it.")
    else:
        parts = ["**Offline mode** (no LLM key in `server/.env`), so here is what I found in your knowledge base:\n"]
        for h in hits:
            snippet = h["text"][:500].strip()
            parts.append(f"**{h['heading'] or h['file']}** — *{h['file']} p.{h['page']}*\n\n> {snippet.replace(chr(10), ' ')}\n")
        answer = "\n".join(parts)
    return {
        "answer": answer,
        "sources": [{"file": h["file"], "page": h["page"], "module": h["module"], "doc_id": h["doc_id"]} for h in hits],
        "tools": ["search_knowledge"],
        "scene": detect_scene(message + " " + " ".join(h["module"] for h in hits), []),
        "llm": None,
    }
