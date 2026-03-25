from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import datetime

app = FastAPI(title="Todo & Notes API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow local frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "todos.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize DB
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            notes TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS standalone_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic models
class TodoBase(BaseModel):
    title: str
    notes: Optional[str] = ""
    completed: bool = False

class TodoCreate(TodoBase):
    pass

class TodoUpdate(TodoBase):
    pass

class TodoResponse(TodoBase):
    id: int
    created_at: str

class NoteBase(BaseModel):
    title: str
    content: Optional[str] = ""

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    pass

class NoteResponse(NoteBase):
    id: int
    created_at: str

@app.get("/todos", response_model=List[TodoResponse])
def get_todos():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM todos ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/todos", response_model=TodoResponse)
def create_todo(todo: TodoCreate):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.datetime.now().isoformat()
    c.execute(
        'INSERT INTO todos (title, notes, completed, created_at) VALUES (?, ?, ?, ?)',
        (todo.title, todo.notes, todo.completed, created_at)
    )
    conn.commit()
    todo_id = c.lastrowid
    conn.close()
    
    return {
        "id": todo_id,
        "title": todo.title,
        "notes": todo.notes,
        "completed": todo.completed,
        "created_at": created_at
    }

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoUpdate):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo not found")
        
    c.execute(
        'UPDATE todos SET title = ?, notes = ?, completed = ? WHERE id = ?',
        (todo.title, todo.notes, todo.completed, todo_id)
    )
    conn.commit()
    
    c.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    updated_row = c.fetchone()
    conn.close()
    return dict(updated_row)

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Todo not found")
        
    c.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()
    return {"message": "Todo deleted successfully"}

# ---- Notes Endpoints ----

@app.get("/notes", response_model=List[NoteResponse])
def get_notes():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM standalone_notes ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.post("/notes", response_model=NoteResponse)
def create_note(note: NoteCreate):
    conn = get_db_connection()
    c = conn.cursor()
    created_at = datetime.datetime.now().isoformat()
    c.execute(
        'INSERT INTO standalone_notes (title, content, created_at) VALUES (?, ?, ?)',
        (note.title, note.content, created_at)
    )
    conn.commit()
    note_id = c.lastrowid
    conn.close()
    
    return {
        "id": note_id,
        "title": note.title,
        "content": note.content,
        "created_at": created_at
    }

@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note: NoteUpdate):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM standalone_notes WHERE id = ?', (note_id,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")
        
    c.execute(
        'UPDATE standalone_notes SET title = ?, content = ? WHERE id = ?',
        (note.title, note.content, note_id)
    )
    conn.commit()
    
    c.execute('SELECT * FROM standalone_notes WHERE id = ?', (note_id,))
    updated_row = c.fetchone()
    conn.close()
    return dict(updated_row)

@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM standalone_notes WHERE id = ?', (note_id,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found")
        
    c.execute('DELETE FROM standalone_notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
    return {"message": "Note deleted successfully"}
