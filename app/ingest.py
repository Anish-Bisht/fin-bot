import os
import csv
import io
from uuid import uuid4
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchAny

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Point to the 'documents' folder where user has placed all domain docs
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
DB_PATH = os.path.join(BASE_DIR, ".data", "qdrant")
COLLECTION_NAME = "rbac_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBED_DIM = 384

# Role names are lowercase to match JWT token roles
ALL_ROLES = ["employee", "finance", "engineering", "marketing", "c_level"]

COLLECTION_ACCESS_MAP = {
    "general":     ALL_ROLES,           # HR handbook, employee FAQ — all roles
    "hr":          ALL_ROLES,           # HR data — treated as general, all roles
    "finance":     ["finance", "c_level"],
    "engineering": ["engineering", "c_level"],
    "marketing":   ["marketing", "c_level"],
}

# Map folder name → canonical collection name
FOLDER_TO_COLLECTION = {
    "general":     "general",
    "hr":          "general",   # HR folder maps to 'general' collection
    "finance":     "finance",
    "engineering": "engineering",
    "marketing":   "marketing",
}


def get_roles_for_folder(folder_name: str):
    """Return the list of roles that can access documents in this folder."""
    return COLLECTION_ACCESS_MAP.get(folder_name.lower(), ["c_level"])


def get_collection_for_folder(folder_name: str) -> str:
    """Return the canonical collection name for a document folder."""
    return FOLDER_TO_COLLECTION.get(folder_name.lower(), folder_name.lower())


def read_csv_as_text(file_path: str) -> list[dict]:
    """Convert a CSV file into a list of text chunks (one per row group)."""
    chunks = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            headers = reader.fieldnames or []
            
            # Group every 20 rows into one chunk for better context
            batch_size = 20
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                lines = [", ".join(f"{h}: {row.get(h, '')}" for h in headers) for row in batch]
                text = "\n".join(lines)
                if text.strip():
                    chunks.append({
                        "text": text,
                        "section_title": f"Data rows {i+1}-{i+len(batch)}",
                        "page_number": 1,
                        "chunk_type": "table"
                    })
    except Exception as e:
        print(f"  CSV read error: {e}")
    return chunks


def process_and_ingest():
    """Parse all documents in the documents/ folder and ingest them into Qdrant with RBAC metadata."""
    
    # Connect to Qdrant
    qdrant_url = os.environ.get("QDRANT_URL")
    if qdrant_url:
        client = QdrantClient(url=qdrant_url)
    else:
        os.makedirs(DB_PATH, exist_ok=True)
        client = QdrantClient(path=DB_PATH)

    # Drop and recreate collection for fresh ingest
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Dropped existing collection '{COLLECTION_NAME}'")
    except Exception:
        pass

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
    )
    print(f"Created fresh collection '{COLLECTION_NAME}'")

    # Load embedding model
    print("Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    
    # Load Docling converter with HybridChunker for better structure-awareness
    converter = DocumentConverter()
    chunker = HybridChunker(tokenizer="sentence-transformers/all-MiniLM-L6-v2", max_tokens=256)

    points = []
    total_files = 0
    total_chunks = 0

    if not os.path.isdir(DOCUMENTS_DIR):
        print(f"ERROR: Documents directory not found at {DOCUMENTS_DIR}")
        return

    for folder_name in sorted(os.listdir(DOCUMENTS_DIR)):
        if folder_name.startswith("."):
            continue
        folder_path = os.path.join(DOCUMENTS_DIR, folder_name)
        if not os.path.isdir(folder_path):
            continue

        collection = get_collection_for_folder(folder_name)
        access_roles = get_roles_for_folder(folder_name)
        print(f"\n📂 Processing folder: {folder_name} → collection={collection}, roles={access_roles}")

        for file_name in sorted(os.listdir(folder_path)):
            if file_name.startswith("."):
                continue
            file_path = os.path.join(folder_path, file_name)
            ext = os.path.splitext(file_name)[1].lower()
            print(f"  📄 Processing: {file_name} ({ext})")
            total_files += 1

            try:
                if ext == ".csv":
                    # Special handling for CSV files
                    raw_chunks = read_csv_as_text(file_path)
                    for rc in raw_chunks:
                        text = rc["text"]
                        if not text.strip():
                            continue
                        vector = embeddings.embed_query(text)
                        metadata = {
                            "source_document": file_name,
                            "collection": collection,
                            "access_roles": access_roles,
                            "section_title": rc["section_title"],
                            "page_number": rc["page_number"],
                            "chunk_type": rc["chunk_type"],
                            "parent_chunk_id": None,
                            "text": text,
                            "folder": folder_name,
                        }
                        point_id = str(uuid4())
                        points.append(PointStruct(id=point_id, vector=vector, payload=metadata))
                        total_chunks += 1

                elif ext in (".pdf", ".docx", ".doc", ".md", ".txt"):
                    # Use Docling for all supported document types
                    doc = converter.convert(file_path).document
                    doc_chunks = list(chunker.chunk(doc))

                    for chunk in doc_chunks:
                        text = chunk.text
                        if not text or not text.strip():
                            continue

                        # Extract metadata from chunk
                        section_title = ""
                        page_number = 1
                        chunk_type = "text"
                        parent_chunk_id = None

                        try:
                            if chunk.meta.headings:
                                section_title = chunk.meta.headings[0]
                        except Exception:
                            pass

                        try:
                            if chunk.meta.doc_items and chunk.meta.doc_items[0].prov:
                                page_number = chunk.meta.doc_items[0].prov[0].page_no
                        except Exception:
                            pass

                        # Detect chunk type from label
                        try:
                            label = str(chunk.meta.doc_items[0].label).lower() if chunk.meta.doc_items else ""
                            if "table" in label:
                                chunk_type = "table"
                            elif "heading" in label or "title" in label:
                                chunk_type = "heading"
                            elif "code" in label:
                                chunk_type = "code"
                            else:
                                chunk_type = "text"
                        except Exception:
                            chunk_type = "text"

                        vector = embeddings.embed_query(text)
                        metadata = {
                            "source_document": file_name,
                            "collection": collection,
                            "access_roles": access_roles,
                            "section_title": section_title,
                            "page_number": page_number,
                            "chunk_type": chunk_type,
                            "parent_chunk_id": parent_chunk_id,
                            "text": text,
                            "folder": folder_name,
                        }
                        point_id = str(uuid4())
                        points.append(PointStruct(id=point_id, vector=vector, payload=metadata))
                        total_chunks += 1

                    print(f"    ✅ {len(doc_chunks)} chunks extracted")

                else:
                    print(f"    ⚠️  Skipping unsupported file type: {ext}")

            except Exception as e:
                print(f"    ❌ Error processing {file_name}: {e}")

    # Batch upsert into Qdrant
    if points:
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(collection_name=COLLECTION_NAME, points=batch)
            print(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1} ({len(batch)} chunks)")

        print(f"\n✅ Ingestion complete!")
        print(f"   Total files processed: {total_files}")
        print(f"   Total chunks ingested: {total_chunks}")
        print(f"   Collection: {COLLECTION_NAME}")
    else:
        print("\n⚠️  No chunks were generated. Check your documents folder.")


if __name__ == "__main__":
    process_and_ingest()
