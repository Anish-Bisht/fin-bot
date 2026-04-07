import sqlite3
import os
from app.auth import get_password_hash
from app.config import settings
from qdrant_client import QdrantClient
from qdrant_client.http import models

def init_db():
    conn = sqlite3.connect(settings.sqlite_db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL
        )
    ''')
    
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        default_users = [
            ("employee1", get_password_hash("password"), "employee", "General"),
            ("finance1", get_password_hash("password"), "finance", "Finance"),
            ("eng1", get_password_hash("password"), "engineering", "Engineering"),
            ("mktg1", get_password_hash("password"), "marketing", "Marketing"),
            ("admin", get_password_hash("admin"), "c_level", "Executive")
        ]
        c.executemany("INSERT INTO users (username, hashed_password, role, department) VALUES (?, ?, ?, ?)", default_users)
    conn.commit()
    conn.close()

def get_user(username: str):
    conn = sqlite3.connect(settings.sqlite_db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT username, hashed_password, role, department FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "hashed_password": row[1], "role": row[2], "department": row[3]}
    return None

def get_all_users():
    conn = sqlite3.connect(settings.sqlite_db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute("SELECT username, role, department FROM users")
    rows = c.fetchall()
    print(f"this is the rows {rows}")
    conn.close()
    return [{"username": r[0], "role": r[1], "department": r[2]} for r in rows]

def create_user(username: str, password: str, role: str, department: str):
    conn = sqlite3.connect(settings.sqlite_db_path, check_same_thread=False)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, hashed_password, role, department) VALUES (?, ?, ?, ?)", 
                  (username, get_password_hash(password), role, department))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_user_role(username: str, role: str, department: str):
    conn = sqlite3.connect(settings.sqlite_db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute("UPDATE users SET role = ?, department = ? WHERE username = ?", (role, department, username))
    updated = c.rowcount > 0
    conn.commit()
    conn.close()
    return updated

def delete_user(username: str):
    conn = sqlite3.connect(settings.sqlite_db_path, check_same_thread=False)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# Qdrant initialization moved to startup event
qdrant_client = None
COLLECTION_NAME = "rbac_documents"

def init_qdrant():
    global qdrant_client
    if qdrant_client is not None:
        return

    import time
    qdrant_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".data", "qdrant")
    os.makedirs(qdrant_path, exist_ok=True)
    qdrant_url = os.environ.get("QDRANT_URL")

    max_retries = 30
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            if qdrant_url:
                qdrant_client = QdrantClient(url=qdrant_url, timeout=10)
            else:
                qdrant_client = QdrantClient(path=qdrant_path)

            # Test connection
            qdrant_client.get_collection(COLLECTION_NAME)
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  Qdrant connection attempt {attempt + 1}/{max_retries} failed: {e}")
                print(f"   Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                qdrant_client = None
            else:
                print(f"❌ Failed to connect to Qdrant after {max_retries} attempts")
                raise

    # Create collection if it doesn't exist
    try:
        if qdrant_client:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
            )
    except Exception:
        pass  # Collection likely already exists

def add_document(doc_id: str, content: str, role: str, folder: str = "", filename: str = ""):
    """Add a document to Qdrant with proper RBAC roles (all lowercase)."""
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector = embeddings.embed_query(content)
    
    # Determine access roles based on folder/collection name
    role_lower = role.lower()
    all_roles = ["employee", "finance", "engineering", "marketing", "c_level"]
    role_map = {
        "general": all_roles,
        "hr": all_roles,
        "all": all_roles,
        "finance": ["finance", "c_level"],
        "engineering": ["engineering", "c_level"],
        "marketing": ["marketing", "c_level"],
    }
    access_roles = role_map.get(role_lower, [role_lower, "c_level"])
    
    payload = {
        "text": content,
        "access_roles": access_roles,
        "collection": folder or role_lower,
        "source_document": filename,
        "folder": folder,
        "filename": filename,
        "page_number": 1,
        "chunk_type": "text",
        "section_title": "",
    }
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[models.PointStruct(id=doc_id, vector=vector, payload=payload)]
    )

def remove_document(doc_id: str):
    qdrant_client.delete(collection_name=COLLECTION_NAME, points_selector=models.PointIdsList(points=[doc_id]))

def get_all_documents():
    # Only fetches a small sample for Admin panel
    results = qdrant_client.scroll(
        collection_name=COLLECTION_NAME,
        limit=100,
        with_payload=True
    )[0]
    docs = []
    for r in results:
        roles = r.payload.get("access_roles", [])
        docs.append({
            "id": r.id,
            "content": r.payload.get("text", "")[:200] + "...",
            "role": roles[0] if roles else "Employee",
            "folder": r.payload.get("folder", ""),
            "filename": r.payload.get("filename", "")
        })
    return docs

def search_documents(query: str, user_role: str, top_k: int = 5):
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector = embeddings.embed_query(query)

    # **RBAC Enforcement**: Normalize role to lowercase and filter at Qdrant level.
    # This ensures restricted chunks are NEVER surfaced to the LLM context.
    role_normalized = user_role.lower()
    rbac_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="access_roles",
                match=models.MatchAny(any=[role_normalized])
            )
        ]
    )
    
    # Use query_points for newer qdrant-client versions
    search_result = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        query_filter=rbac_filter,
        limit=top_k,
        with_payload=True
    ).points
    
    if not search_result:
        return [], "No relevant internal documents found in the database."
    
    chunks = []
    for hit in search_result:
        p = hit.payload
        if p is None:
            continue  # Skip if payload is missing for some reason
            
        content = p.get("text", "")
        source = p.get("source_document", p.get("filename", "Unknown"))
        page = p.get("page_number", 1)
        # Store chunks differently for agent reasoning vs citing
        chunks.append({
            "text": content,
            "source": source,
            "page": page
        })
        
    return chunks, ""
