import os
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlmodel import SQLModel, create_engine, Session, select
from starlette.responses import Response

# Theme metadata for OpenAPI docs (Ocean Professional)
APP_TITLE = "Notes API"
APP_DESC = (
    "Modern, minimalist notes management API. "
    "Create, read, update, and delete notes with clean, well-documented endpoints."
)
APP_VERSION = "1.0.0"
OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "Service health endpoints",
    },
    {
        "name": "notes",
        "description": "Operations to create, read, update, and delete notes",
    },
]

# Database URL: use environment variable if provided, else fallback to local SQLite.
# IMPORTANT: Do not edit .env here; orchestrator will provide env vars.
DATABASE_URL = os.getenv("NOTES_DB_URL", "sqlite:///./notes.db")

# Create SQLModel engine
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


# PUBLIC_INTERFACE
class NoteBase(BaseModel):
    """Base attributes for a Note."""
    title: str = Field(..., description="Title of the note", min_length=1, max_length=255)
    content: str = Field(..., description="Full content of the note", min_length=1)
    pinned: bool = Field(False, description="Whether the note is pinned for quick access")
    color: Optional[str] = Field(
        None,
        description="Optional HEX color code to accent this note in UIs (e.g., #2563EB)",
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
    )


# PUBLIC_INTERFACE
class NoteCreate(NoteBase):
    """Payload to create a new note."""
    pass


# PUBLIC_INTERFACE
class NoteUpdate(BaseModel):
    """Payload to update an existing note. All fields optional."""
    title: Optional[str] = Field(None, description="Updated title of the note", min_length=1, max_length=255)
    content: Optional[str] = Field(None, description="Updated content of the note", min_length=1)
    pinned: Optional[bool] = Field(None, description="Updated pinned state of the note")
    color: Optional[str] = Field(
        None,
        description="Updated HEX color code for the note",
        pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$",
    )


# PUBLIC_INTERFACE
class NoteRead(NoteBase):
    """Response model for a Note."""
    id: int = Field(..., description="Unique identifier for the note")


# SQLModel ORM
from sqlmodel import Field as SQLField  # re-alias to avoid confusion with Pydantic Field
from sqlmodel import Column, String, Boolean


class Note(SQLModel, table=True):
    """Database model for a note."""
    id: Optional[int] = SQLField(default=None, primary_key=True)
    title: str = SQLField(sa_column=Column(String(255), nullable=False))
    content: str = SQLField(sa_column=Column(String, nullable=False))
    pinned: bool = SQLField(sa_column=Column(Boolean, nullable=False, default=False))
    color: Optional[str] = SQLField(default=None, sa_column=Column(String(7), nullable=True))


def create_db_and_tables() -> None:
    """Create database tables if they do not exist."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency to provide a SQLModel session."""
    with Session(engine) as session:
        yield session


# Initialize FastAPI app with themed metadata
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESC,
    version=APP_VERSION,
    contact={
        "name": "Notes API",
        "url": "https://example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=OPENAPI_TAGS,
    swagger_ui_parameters={
        # Minimalist UI tweaks inspired by Ocean Professional theme
        "docExpansion": "list",
        "displayRequestDuration": True,
        "tryItOutEnabled": True,
        "defaultModelsExpandDepth": 0,
        "syntaxHighlight.theme": "agate",
    },
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for demo; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


# ROUTES

# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check", description="Simple health endpoint to check service availability.")
def health_check():
    """Health check endpoint returning a status message."""
    return {
        "status": "ok",
        "theme": {
            "name": "Ocean Professional",
            "primary": "#2563EB",
            "secondary": "#F59E0B",
            "error": "#EF4444",
            "background": "#f9fafb",
            "surface": "#ffffff",
            "text": "#111827",
        },
        "service": "notes-backend",
        "version": APP_VERSION,
    }


# PUBLIC_INTERFACE
@app.post(
    "/api/notes",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
    tags=["notes"],
    summary="Create a note",
    description="Create a new note with title and content. Optional fields: pinned, color.",
    responses={
        201: {"description": "Note created successfully"},
        422: {"description": "Validation error"},
    },
)
def create_note(payload: NoteCreate, session: Session = Depends(get_session)):
    """Create a new note and persist it to the database."""
    note = Note(**payload.model_dict())
    session.add(note)
    session.commit()
    session.refresh(note)
    return NoteRead(**note.model_dump())


# PUBLIC_INTERFACE
@app.get(
    "/api/notes",
    response_model=List[NoteRead],
    tags=["notes"],
    summary="List all notes",
    description="Retrieve all notes with their details.",
)
def list_notes(session: Session = Depends(get_session), pinned: Optional[bool] = None):
    """Return a list of notes. Optionally filter by pinned=true/false."""
    query = select(Note)
    if pinned is not None:
        query = query.where(Note.pinned == pinned)
    results = session.exec(query).all()
    return [NoteRead(**n.model_dump()) for n in results]


# PUBLIC_INTERFACE
@app.get(
    "/api/notes/{note_id}",
    response_model=NoteRead,
    tags=["notes"],
    summary="Get a note",
    description="Retrieve a single note by its ID.",
    responses={
        404: {"description": "Note not found"},
    },
)
def get_note(note_id: int, session: Session = Depends(get_session)):
    """Get a note by ID or return 404 if not found."""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return NoteRead(**note.model_dump())


# PUBLIC_INTERFACE
@app.put(
    "/api/notes/{note_id}",
    response_model=NoteRead,
    tags=["notes"],
    summary="Update a note (full)",
    description="Replace all fields of a note by ID.",
    responses={
        200: {"description": "Note updated successfully"},
        404: {"description": "Note not found"},
    },
)
def update_note(note_id: int, payload: NoteCreate, session: Session = Depends(get_session)):
    """Replace a note's fields with provided payload."""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    for k, v in payload.model_dump().items():
        setattr(note, k, v)
    session.add(note)
    session.commit()
    session.refresh(note)
    return NoteRead(**note.model_dump())


# PUBLIC_INTERFACE
@app.patch(
    "/api/notes/{note_id}",
    response_model=NoteRead,
    tags=["notes"],
    summary="Update a note (partial)",
    description="Update one or more fields of a note by ID.",
    responses={
        200: {"description": "Note updated successfully"},
        404: {"description": "Note not found"},
    },
)
def patch_note(note_id: int, payload: NoteUpdate, session: Session = Depends(get_session)):
    """Partially update a note's fields."""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(note, k, v)
    session.add(note)
    session.commit()
    session.refresh(note)
    return NoteRead(**note.model_dump())


# PUBLIC_INTERFACE
@app.delete(
    "/api/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["notes"],
    summary="Delete a note",
    description="Delete a note by ID. Returns 204 on success.",
    responses={
        204: {"description": "Note deleted"},
        404: {"description": "Note not found"},
    },
)
def delete_note(note_id: int, session: Session = Depends(get_session)):
    """Delete a note by ID."""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    session.delete(note)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# PUBLIC_INTERFACE
@app.delete(
    "/api/notes",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["notes"],
    summary="Delete all notes",
    description="Delete all notes in the database. Intended for maintenance or resetting state.",
)
def delete_all_notes(session: Session = Depends(get_session)):
    """Delete all notes from the database."""
    results = session.exec(select(Note)).all()
    for n in results:
        session.delete(n)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# PUBLIC_INTERFACE
@app.get(
    "/docs/theme",
    tags=["health"],
    summary="Docs theme info",
    description="Returns the Ocean Professional theme information used for OpenAPI documentation.",
)
def docs_theme():
    """Provide theme metadata for clients/tools."""
    return {
        "applicationTheme": "Ocean Professional",
        "palette": {
            "primary": "#2563EB",
            "secondary": "#F59E0B",
            "success": "#F59E0B",
            "error": "#EF4444",
            "background": "#f9fafb",
            "surface": "#ffffff",
            "text": "#111827",
            "gradient": "from-blue-500/10 to-gray-50",
        },
    }


# Convenience root for uvicorn when run in this container:
# uvicorn src.api.main:app --host 0.0.0.0 --port 3001
