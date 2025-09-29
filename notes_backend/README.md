# Notes Backend (FastAPI)

A minimalist, modern notes API built with FastAPI and SQLModel using the "Ocean Professional" theme for OpenAPI docs.

## Features
- CRUD endpoints for notes (create, list, get, update/patch, delete)
- SQLModel + SQLAlchemy persistence
- Clean structure and theme-aware OpenAPI docs
- CORS enabled for quick integration

## Run locally
Install dependencies and start the server (port 3001):

```bash
pip install -r requirements.txt
uvicorn src.api.main:app --host 0.0.0.0 --port 3001
```

## Environment variables
- NOTES_DB_URL: Database URL (default: sqlite:///./notes.db)

Create a `.env.example` to guide setup if needed; the orchestrator will set actual values in `.env`.

## API
- GET / -> Health
- POST /api/notes -> Create note
- GET /api/notes -> List notes (optional filter `?pinned=true|false`)
- GET /api/notes/{id} -> Get note
- PUT /api/notes/{id} -> Replace note
- PATCH /api/notes/{id} -> Partially update note
- DELETE /api/notes/{id} -> Delete note
- DELETE /api/notes -> Delete all notes (maintenance)

OpenAPI docs:
- Swagger UI: /docs
- ReDoc: /redoc
- Theme info: /docs/theme
