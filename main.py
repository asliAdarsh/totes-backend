import os
import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 1. Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")

# Use 'psycopg2' for Postgres. SQLAlchemy handles the connection pooling.
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. Database Models ---
class TodoModel(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class NoteModel(Base):
    __tablename__ = "standalone_notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Automatically create tables in Supabase/Postgres on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Todo & Notes API")

# --- 3. Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 4. Pydantic Schemas ---
class TodoBase(BaseModel):
    title: str
    notes: Optional[str] = ""
    completed: bool = False

class TodoResponse(TodoBase):
    id: int
    created_at: datetime.datetime
    class Config:
        from_attributes = True

class NoteBase(BaseModel):
    title: str
    content: Optional[str] = ""

class NoteResponse(NoteBase):
    id: int
    created_at: datetime.datetime
    class Config:
        from_attributes = True

# --- 5. Endpoints ---

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow()}

# --- Todo Endpoints ---
@app.get("/todos", response_model=List[TodoResponse])
def get_todos(db: Session = Depends(get_db)):
    return db.query(TodoModel).order_by(TodoModel.created_at.desc()).all()

@app.post("/todos", response_model=TodoResponse)
def create_todo(todo: TodoBase, db: Session = Depends(get_db)):
    db_todo = TodoModel(**todo.model_dump())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoBase, db: Session = Depends(get_db)):
    db_todo = db.query(TodoModel).filter(TodoModel.id == todo_id).first()
    if not db_todo: 
        raise HTTPException(status_code=404, detail="Todo not found")
    for key, value in todo.model_dump().items():
        setattr(db_todo, key, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = db.query(TodoModel).filter(TodoModel.id == todo_id).first()
    if not db_todo: 
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(db_todo)
    db.commit()
    return {"message": "Todo deleted successfully"}

# --- Note Endpoints ---
@app.get("/notes", response_model=List[NoteResponse])
def get_notes(db: Session = Depends(get_db)):
    return db.query(NoteModel).order_by(NoteModel.created_at.desc()).all()

@app.post("/notes", response_model=NoteResponse)
def create_note(note: NoteBase, db: Session = Depends(get_db)):
    db_note = NoteModel(**note.model_dump())
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note: NoteBase, db: Session = Depends(get_db)):
    db_note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    for key, value in note.model_dump().items():
        setattr(db_note, key, value)
    db.commit()
    db.refresh(db_note)
    return db_note

@app.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(db_note)
    db.commit()
    return {"message": "Note deleted successfully"}