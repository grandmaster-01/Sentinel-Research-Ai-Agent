"""
worker.py — Celery task dispatcher for Sentinel (solo pool for Windows compat).
"""
import os, json, time
from pathlib import Path
from celery import Celery
from .models import get_fast_llm, get_coding_llm, MODEL_FAST, MODEL_CODING, detect_coding_query

REDIS_URL   = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Absolute path so results/ is always next to the project src/, regardless of cwd
RESULTS_DIR = Path(__file__).parent.parent / "results"

celery_app = Celery("sentinel_worker", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    worker_pool="solo",        # Windows + Python 3.13: prefork/billiard crashes
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

# ── Prompts ───────────────────────────────────────────────────────────────────

_FAST_PROMPT = (
    "You are Sentinel, a knowledgeable AI assistant (Llama 3.2).\n"
    "Answer directly and concisely using the web results provided.\n"
    "Use markdown formatting. Fall back on your own knowledge if web results are sparse."
)

_CODING_PROMPT = (
    "You are Sentinel Coder (Qwen 2.5). You are an expert software engineer.\n"
    "Write clean, well-commented code in fenced code blocks with the correct language tag.\n"
    "After the code, briefly explain the logic step by step."
)

# ── Mode handlers ─────────────────────────────────────────────────────────────

def _fast_mode(query, chat_history, file_content):
    from src.agent_tools import search_web
    ctx     = "\n".join(search_web.invoke(query))
    history = "\n".join(chat_history[-6:]) if chat_history else ""
    parts   = [_FAST_PROMPT]
    if history:      parts.append(f"Previous Conversation:\n{history}")
    if file_content: parts.append(f"Attached File:\n{file_content[:3000]}")
    parts.append(f"Web Results:\n{ctx}")
    parts.append(f"Question: {query}\n\nAnswer:")
    return get_fast_llm().invoke("\n\n".join(parts)).content, MODEL_FAST


def _coding_mode(query, chat_history, file_content):
    history = "\n".join(chat_history[-6:]) if chat_history else ""
    parts   = [_CODING_PROMPT]
    if history:      parts.append(f"Previous Conversation:\n{history}")
    if file_content: parts.append(f"Reference Code:\n{file_content[:3000]}")
    parts.append(f"Task: {query}\n\nSolution:")
    return get_coding_llm().invoke("\n\n".join(parts)).content, MODEL_CODING


def _workflow_mode(query, mode, chat_history, file_content):
    from .app_workflow import app as wf
    result = wf.invoke({"question": query, "chat_history": chat_history,
                        "file_content": file_content, "mode": mode})
    return result.get("report", "No report generated."), result.get("model_used", "unknown")

# ── Celery Task ───────────────────────────────────────────────────────────────

@celery_app.task
def run_research_task(query: str, mode: str = "deep",
                      chat_history: list = None, file_content: str = "",
                      session_id: str = ""):
    if chat_history is None:
        chat_history = []

    # Auto-upgrade fast/auto → coding for code-related queries
    effective_mode = mode
    if mode in ("fast", "auto") and detect_coding_query(query):
        effective_mode = "coding"

    try:
        if effective_mode == "fast":
            report, model = _fast_mode(query, chat_history, file_content)
        elif effective_mode == "coding":
            report, model = _coding_mode(query, chat_history, file_content)
        elif effective_mode in ("deep", "rag"):
            report, model = _workflow_mode(query, effective_mode, chat_history, file_content)
        else:
            report, model = _workflow_mode(query, "deep", chat_history, file_content)

        # Persist with absolute path — session_id groups follow-ups together
        task_id           = run_research_task.request.id or ""
        effective_session  = session_id if session_id else task_id
        if task_id:
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            with open(RESULTS_DIR / f"{task_id}.json", "w", encoding="utf-8") as f:
                json.dump({
                    "task_id":    task_id,
                    "session_id": effective_session,
                    "query":      query,
                    "report":     report,
                    "model":      model,
                    "timestamp":  time.time(),
                }, f, indent=2)

        return report

    except Exception as exc:
        return f"⚠️ Research failed: {exc}"
