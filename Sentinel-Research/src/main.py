from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from celery.result import AsyncResult
from .worker import celery_app, run_research_task
from typing import List, Optional
from pathlib import Path
import json, os, shutil

app = FastAPI(title="Sentinel-Research API", version="3.0")

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

DATA_DIR    = Path(os.path.dirname(__file__)) / ".." / "data"
RESULTS_DIR = Path("results")
DATA_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

# ── Research ──────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    query:        str
    mode:         str           = "fast"   # fast | deep | rag | coding | auto
    chat_history: List[str]     = []
    file_content: Optional[str] = None
    session_id:   Optional[str] = None     # first message omits this; follow-ups send it

@app.post("/research", status_code=202)
async def start_research(request: ResearchRequest):
    task = run_research_task.delay(
        request.query,
        request.mode,
        request.chat_history,
        request.file_content or "",
        request.session_id or "",
    )
    return {"task_id": task.id, "status": "processing"}

@app.get("/research/{task_id}")
async def get_research_status(task_id: str):
    # Check persisted result first
    f = RESULTS_DIR / f"{task_id}.json"
    if f.exists():
        data = json.loads(f.read_text(encoding="utf-8"))
        return {"task_id": task_id, "status": "completed",
                "result": data.get("report"), "session_id": data.get("session_id")}

    result = AsyncResult(task_id, app=celery_app)
    if result.state == "PENDING":
        return {"task_id": task_id, "status": "pending"}
    if result.state == "SUCCESS":
        return {"task_id": task_id, "status": "completed", "result": result.result}
    if result.state == "FAILURE":
        return {"task_id": task_id, "status": "failed", "error": str(result.result)}
    return {"task_id": task_id, "status": result.state}

# ── Session (grouped conversation) ────────────────────────────────────────────

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Returns all Q&A pairs that belong to a conversation session."""
    messages = []
    for f in RESULTS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("session_id") == session_id:
                messages.append(data)
        except Exception:
            continue
    messages.sort(key=lambda x: x.get("timestamp", 0))
    return messages

# ── History ───────────────────────────────────────────────────────────────────

@app.get("/history")
async def get_history():
    """Returns one entry per conversation session (grouped by session_id)."""
    sessions: dict = {}  # session_id → first message data
    for f in RESULTS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sid = data.get("session_id", data.get("task_id"))
            if sid and (sid not in sessions or
                        data.get("timestamp", 0) < sessions[sid].get("timestamp", 0)):
                sessions[sid] = data
        except Exception:
            continue
    history = [
        {"task_id": v["session_id"], "query": v["query"], "timestamp": v.get("timestamp", 0)}
        for v in sessions.values()
    ]
    history.sort(key=lambda x: x["timestamp"], reverse=True)
    return history

@app.delete("/history/{session_id}")
async def delete_history_item(session_id: str):
    deleted = 0
    for f in RESULTS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("session_id") == session_id:
                f.unlink()
                deleted += 1
        except Exception:
            continue
    if deleted:
        return {"status": "success", "deleted": deleted}
    raise HTTPException(status_code=404, detail="Session not found")

# ── Models ────────────────────────────────────────────────────────────────────

@app.get("/models")
async def get_models():
    from .models import model_info
    return model_info()

# ── RAG / Ingest ──────────────────────────────────────────────────────────────

@app.post("/ingest")
async def ingest_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    allowed = {".pdf", ".txt", ".md", ".csv"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported type '{ext}'. Allowed: {allowed}")
    dest = DATA_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    background_tasks.add_task(lambda: __import__('src.ingest', fromlist=['process_file']).process_file(str(dest)))
    return {"status": "processing", "file": file.filename}

@app.get("/ingest/status")
async def get_kb_status():
    from .ingest import get_collection_stats
    return get_collection_stats()

@app.get("/ingest/files")
async def list_ingested_files():
    files = [{"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)}
             for f in DATA_DIR.iterdir() if f.is_file()]
    return {"files": files, "count": len(files)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
