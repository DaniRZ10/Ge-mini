"""
database.py — Módulo de persistencia con SQLite async.
Gestiona conversaciones y mensajes para el historial de Ge-mini.
"""

import aiosqlite
import uuid
from datetime import datetime, timezone

import os

# Ruta a la base de datos (se mantiene en la carpeta data/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gemini_chat.db")


async def init_db():
    """Crea las tablas si no existen. Se llama al arrancar la app."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role            TEXT NOT NULL,
                content         TEXT NOT NULL,
                model           TEXT,
                provider        TEXT,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
        """)

        await db.commit()


# ─── Conversaciones ───────────────────────────────────────

async def create_conversation(title: str) -> str:
    """Crea una nueva conversación y devuelve su ID (UUID)."""
    conv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, title, now, now)
        )
        await db.commit()

    return conv_id


async def list_conversations(limit: int = 50) -> list[dict]:
    """Devuelve las conversaciones ordenadas por última actividad (más recientes primero)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def delete_conversation(conversation_id: str) -> bool:
    """Borra una conversación y todos sus mensajes (CASCADE). Devuelve True si existía."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        cursor = await db.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def update_conversation_title(conversation_id: str, title: str):
    """Actualiza el título de una conversación."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (title, conversation_id)
        )
        await db.commit()


async def _touch_conversation(db, conversation_id: str):
    """Actualiza el campo updated_at de la conversación (uso interno)."""
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conversation_id)
    )


# ─── Mensajes ─────────────────────────────────────────────

async def add_message(
    conversation_id: str,
    role: str,
    content: str,
    model: str | None = None,
    provider: str | None = None
):
    """Inserta un mensaje y actualiza la fecha de la conversación."""
    now = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute(
            """INSERT INTO messages (conversation_id, role, content, model, provider, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (conversation_id, role, content, model, provider, now)
        )
        await _touch_conversation(db, conversation_id)
        await db.commit()


async def get_conversation_messages(conversation_id: str) -> list[dict]:
    """Devuelve todos los mensajes de una conversación, ordenados cronológicamente."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, role, content, model, provider, created_at
               FROM messages
               WHERE conversation_id = ?
               ORDER BY created_at ASC""",
            (conversation_id,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
