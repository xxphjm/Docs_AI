# TechDoc AI Assistant

LangChain + Chroma + NVIDIA 的文件知識庫助手。

## Structure

```text
backend/
  app/
    main.py
    api/v1/
    agent.py
    ingest.py
    db.py
    util/
frontend/
  src/
```

## Run backend

```bash
uv sync
uv run uvicorn backend.app.main:app --reload
```

API will be available at `http://localhost:8000`.

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`.

## API

- `GET /api/v1/health`
- `POST /api/v1/documents/upload`
- `POST /api/v1/chat`

## Deployment

- Backend: run `uv run uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- Frontend: build with `npm run build` and deploy `frontend/dist`
- Production CORS: set `CORS_ORIGINS` to your frontend domain
