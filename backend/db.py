import sqlite3
from datetime import datetime
from utils import debug_print
DATABASE = 'conversations.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    with open('schema.sql', 'r') as f:
        conn.executescript(f.read())
    conn.close()

def save_conversation(provider, model, system_message, title):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("INSERT INTO conversations (provider, model, system_message, created_at, title) VALUES (?, ?, ?, ?, ?)",
                   (provider, model, system_message, timestamp, title))
    conversation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return conversation_id

def add_message_to_conversation(conversation_id, role, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                   (conversation_id, role, content, timestamp))
    conn.commit()
    conn.close()

def get_conversation(conversation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversations WHERE id = ?", (conversation_id,))
    conversation = cursor.fetchone()
    if conversation:
        cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at", (conversation_id,))
        messages = cursor.fetchall()
        conn.close()
        return dict(conversation), [dict(message) for message in messages]
    conn.close()
    return None, None

def list_conversations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, provider, model, created_at FROM conversations ORDER BY created_at DESC")
    conversations = cursor.fetchall()
    conn.close()
    return [dict(conversation) for conversation in conversations]

def save_system_message(name, content):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("INSERT INTO system_messages (name, content, created_at) VALUES (?, ?, ?)", (name, content, timestamp))
    system_message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return system_message_id

def get_system_message(system_message_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM system_messages WHERE id = ?", (system_message_id,))
    system_message = cursor.fetchone()
    conn.close()
    if system_message:
        return dict(system_message)
    return None

def list_system_messages():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, provider, model, created_at FROM conversations ORDER BY created_at DESC")
    conversations = cursor.fetchall()
    cursor.execute("SELECT id, name, content, created_at FROM system_messages ORDER BY created_at DESC")
    system_messages = cursor.fetchall()
    conn.close()
    return [dict(system_message) for system_message in system_messages]

def delete_system_message(system_message_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM system_messages WHERE id = ?", (system_message_id,))
    conn.commit()
    conn.close()

def delete_all_system_messages():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM system_messages")
    conn.commit()
    conn.close()

def delete_conversation(conversation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.commit()

def delete_all_conversations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM conversations")
    cursor.execute("DELETE FROM messages")
    conn.commit()
    conn.close()