"""
app_workflow.py — LangGraph research pipeline (deep & RAG modes).

  deep → Gemma 3   (thorough research with web + KB)
  rag  → Phi 3.5   (KB-first, web as supplement)
"""
import os
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from src.state import AgentState
from src.agent_tools import retrieve_documents, search_web
from src.models import get_rag_llm, get_deep_llm, MODEL_RAG, MODEL_DEEP

load_dotenv()

# ── System Prompts ────────────────────────────────────────────────────────────

_DEEP_SYS = """You are Sentinel, an advanced AI research assistant powered by Gemma 3.
- Answer thoroughly with deep analysis and multiple viewpoints.
- Use Knowledge Base excerpts and Web Results as primary sources.
- Format with markdown: headers, bullets, bold, code blocks.
- Cite web sources when used (e.g. "According to [Source 1]...").
- Never say "the context does not provide" — use your knowledge if sources are thin."""

_RAG_SYS = """You are Sentinel, an intelligent research assistant powered by Phi 3.5.
- Treat Knowledge Base excerpts as your PRIMARY source of truth.
- Use Web Results only when the KB doesn't cover the topic.
- Always reference the source document when citing KB content.
- Be concise, accurate, and well-cited."""

# ── Shared retrieval ──────────────────────────────────────────────────────────

def _retrieve_and_search(state: AgentState) -> AgentState:
    q = state["question"]
    return {"context": retrieve_documents.invoke(q), "web_results": search_web.invoke(q)}

def _web_only(state: AgentState) -> AgentState:
    return {"web_results": search_web.invoke(state["question"])}

# ── Build human message ───────────────────────────────────────────────────────

def _build_human(state: AgentState) -> str:
    parts = []
    history = "\n".join((state.get("chat_history") or [])[-6:])
    if history:
        parts.append(f"**Previous Conversation:**\n{history}")

    fc = state.get("file_content", "")
    if fc:
        parts.append(f"**Attached File:**\n{fc[:3000]}")

    real_ctx = [c for c in (state.get("context") or [])
                if not c.startswith("No knowledge base") and not c.startswith("Knowledge base is empty")]
    if real_ctx:
        parts.append("**Knowledge Base (RAG):**\n" + "\n\n".join(real_ctx))

    web = state.get("web_results") or []
    if web:
        parts.append("**Web Search Results:**\n" + "\n\n".join(web))

    parts.append(f"**Question:** {state['question']}\n\nProvide a comprehensive, well-structured answer:")
    return "\n\n---\n\n".join(parts)

# ── Generator nodes ───────────────────────────────────────────────────────────

def _generate_deep(state: AgentState) -> AgentState:
    chain = ChatPromptTemplate.from_messages([("system", _DEEP_SYS), ("human", "{input}")]) | get_deep_llm()
    return {"report": chain.invoke({"input": _build_human(state)}).content, "model_used": MODEL_DEEP}

def _generate_rag(state: AgentState) -> AgentState:
    chain = ChatPromptTemplate.from_messages([("system", _RAG_SYS), ("human", "{input}")]) | get_rag_llm()
    return {"report": chain.invoke({"input": _build_human(state)}).content, "model_used": MODEL_RAG}

# ── Router ────────────────────────────────────────────────────────────────────

def _route(state: AgentState) -> Literal["fetch_rag", "fetch_deep", "fetch_web"]:
    mode = state.get("mode", "deep")
    if mode == "rag":
        return "fetch_rag"
    if os.path.exists("./qdrant_db"):
        return "fetch_deep"
    return "fetch_web"

# ── Graph ─────────────────────────────────────────────────────────────────────

workflow = StateGraph(AgentState)

workflow.add_node("fetch_deep", _retrieve_and_search)
workflow.add_node("fetch_rag",  _retrieve_and_search)
workflow.add_node("fetch_web",  _web_only)
workflow.add_node("gen_deep",   _generate_deep)
workflow.add_node("gen_rag",    _generate_rag)

workflow.add_conditional_edges(START, _route, {
    "fetch_deep": "fetch_deep",
    "fetch_rag":  "fetch_rag",
    "fetch_web":  "fetch_web",
})

workflow.add_edge("fetch_deep", "gen_deep")
workflow.add_edge("fetch_rag",  "gen_rag")
workflow.add_edge("fetch_web",  "gen_deep")
workflow.add_edge("gen_deep",   END)
workflow.add_edge("gen_rag",    END)

app = workflow.compile()
