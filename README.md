# Sentinel Research — Multi-Model AI Agent

Sentinel Research is an autonomous AI research agent powered by multiple local LLMs through [Ollama](https://ollama.com/). It combines web search, a RAG knowledge base (Qdrant), and a LangGraph workflow to deliver fast answers, deep research, document-grounded responses, and code generation — all from a single chat interface.

## Features

- **Four Specialised Modes** – each backed by a dedicated model:
  | Mode | Model | Purpose |
  |------|-------|---------|
  | Fast | Llama 3.2 (3 B) | Quick answers with live web search |
  | Deep | Gemma 3 | Thorough research with web + knowledge base |
  | RAG | Phi 3.5 | Knowledge-base-first answers using ingested documents |
  | Coding | Qwen 2.5 (7 B Instruct) | Code generation and debugging |
- **Auto Mode** – automatically upgrades Fast queries to Coding when code-related keywords are detected.
- **RAG Ingestion** – upload PDF, TXT, Markdown, or CSV files; they are chunked, embedded with `all-MiniLM-L6-v2`, and stored in Qdrant.
- **Session History** – conversations are grouped by session and persisted to disk so you can resume or review past chats.
- **Web Search** – uses Brave Search (when an API key is configured) with a DuckDuckGo fallback.
- **Modern Chat UI** – dark/light theme, markdown rendering, code-block copy button, file attachments, and mobile-responsive sidebar.

## Architecture

```
Sentinel-Research/
├── src/
│   ├── main.py            # FastAPI application & REST endpoints
│   ├── worker.py          # Celery task dispatcher (fast & coding modes)
│   ├── app_workflow.py    # LangGraph research pipeline (deep & RAG modes)
│   ├── agent_tools.py     # Web search & RAG retrieval tools
│   ├── models.py          # Centralised Ollama LLM loader & model config
│   ├── state.py           # AgentState TypedDict for the workflow
│   ├── ingest.py          # Document ingestion into Qdrant
│   └── static/            # Frontend (HTML, CSS, JS)
├── tests/                 # Verification & integration tests
├── k8s/                   # Kubernetes deployment manifests
├── Dockerfile             # Multi-stage Docker build
└── requirements.txt       # Python dependencies
```

## Prerequisites

| Dependency | Purpose |
|------------|---------|
| Python 3.11+ | Runtime |
| [Ollama](https://ollama.com/) | Local LLM serving |
| Redis | Celery broker / result backend |
| Qdrant *(optional)* | Vector store for RAG (falls back to local file mode) |

Pull the required models before starting:

```bash
ollama pull llama3.2:3b
ollama pull gemma3:latest
ollama pull phi3.5:latest
ollama pull qwen2.5:7b-instruct
```

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/grandmaster-01/Sentinel-Research-Ai-Agent.git
cd Sentinel-Research-Ai-Agent/Sentinel-Research

# 2. Create a virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. (Optional) Create a .env file
cat > .env <<EOF
OLLAMA_BASE_URL=http://localhost:11434
REDIS_URL=redis://localhost:6379/0
# QDRANT_URL=http://localhost:6333   # uncomment for server mode
# BRAVE_SEARCH_API_KEY=your_key      # uncomment to use Brave Search
EOF

# 4. Start Redis (in a separate terminal)
redis-server

# 5. Start the Celery worker
celery -A src.worker worker --loglevel=info --pool=solo

# 6. Start the API server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000** in your browser to use the chat UI.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serve the chat UI |
| `POST` | `/research` | Submit a research query (returns `task_id`) |
| `GET` | `/research/{task_id}` | Poll task status / retrieve result |
| `GET` | `/session/{session_id}` | Get all messages in a conversation session |
| `GET` | `/history` | List all conversation sessions |
| `DELETE` | `/history/{session_id}` | Delete a conversation session |
| `GET` | `/models` | List configured models |
| `POST` | `/ingest` | Upload a document for RAG ingestion |
| `GET` | `/ingest/status` | Knowledge base collection stats |
| `GET` | `/ingest/files` | List ingested files |

## Docker

```bash
docker build -t sentinel-research ./Sentinel-Research
docker run -p 8000:8000 \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  sentinel-research
```

## Kubernetes

A Deployment, Service, and HorizontalPodAutoscaler manifest is provided:

```bash
kubectl apply -f Sentinel-Research/k8s/deployment.yaml
```

## License

This project is released under the [MIT License](LICENSE.txt).
