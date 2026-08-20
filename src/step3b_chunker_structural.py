"""
src/step3b_chunker_structural.py
Fast, Deterministic Structural Chunking for Vachanamrut.
- 100% text preservation (zero loss).
- Preserves natural Q&A dialogue and setting context.
- Runs in < 5 seconds for $0 LLM cost.
- Batches embeddings to prevent OpenAI batch token errors.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from src.config import (
    PROCESSED_DATA_DIR,
    CHROMA_DB_PATH,
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
)

# Paths Configuration
KNOWLEDGE_BASE_PATH = PROCESSED_DATA_DIR / "vachanamruts"
CHUNKS_JSON_PATH = PROCESSED_DATA_DIR / "vachanamrut_structural_chunks.json"

TARGET_CHUNK_CHARS = 1500  # Ideal target size (~300-400 words)
MAX_CHUNK_CHARS = 2500     # Hard upper bound before splitting


def clean_raw_text(text: str) -> str:
    """Strips header/footer page number remnants."""
    cleaned = re.sub(r'^\s*Vachanamrut\s+\d+(\s+\d+)?\s*$', '', text, flags=re.MULTILINE)
    return cleaned.strip()


def fetch_documents() -> List[Dict[str, str]]:
    """Loads markdown files from the processed directory."""
    if not KNOWLEDGE_BASE_PATH.exists():
        raise FileNotFoundError(f"Knowledge base path not found: {KNOWLEDGE_BASE_PATH}")

    documents = []
    for file in sorted(KNOWLEDGE_BASE_PATH.rglob("*.md")):
        with open(file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        cleaned = clean_raw_text(raw_text)
        if cleaned:
            documents.append({
                "section": file.parent.name,
                "source": file.as_posix(),
                "file_name": file.stem,
                "text": cleaned
            })

    print(f"Loaded {len(documents)} markdown document(s).")
    return documents


def chunk_vachanamrut_document(doc: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Splits a single Vachanamrut document along paragraph boundaries
    while grouping speaker turns into clean logical units.
    """
    raw_text = doc["text"]
    # Split by double newlines to isolate paragraphs
    paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = []
    current_length = 0

    # Patterns indicating a new dialogue question or major shift
    speaker_pattern = re.compile(
        r'^(Then|Thereupon|Thereafter|Addressing|Asking|Shriji Maharaj|Further)', 
        re.IGNORECASE
    )

    for p in paragraphs:
        p_len = len(p)

        # If adding this paragraph exceeds target size AND it starts a new speaker turn, output chunk
        if current_length >= TARGET_CHUNK_CHARS and speaker_pattern.match(p):
            chunk_str = "\n\n".join(current_chunk)
            chunks.append(chunk_str)
            current_chunk = [p]
            current_length = p_len
        # If adding this paragraph exceeds hard maximum length, output current chunk regardless
        elif current_length + p_len > MAX_CHUNK_CHARS and current_chunk:
            chunk_str = "\n\n".join(current_chunk)
            chunks.append(chunk_str)
            current_chunk = [p]
            current_length = p_len
        else:
            current_chunk.append(p)
            current_length += p_len + 2  # account for \n\n

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    # Build formatted result objects
    formatted_chunks = []
    for idx, chunk_text in enumerate(chunks):
        formatted_chunks.append({
            "page_content": chunk_text,
            "metadata": {
                "source": doc["source"],
                "chapter": doc["file_name"],
                "section": doc["section"],
                "chunk_index": idx,
                "character_count": len(chunk_text)
            }
        })

    return formatted_chunks


def index_chunks_to_chroma(chunks_data: List[Dict[str, Any]]):
    langchain_docs = [
        Document(page_content=item["page_content"], metadata=item["metadata"])
        for item in chunks_data
    ]

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL, 
        openai_api_key=OPENAI_API_KEY
    )

    store_path = CHROMA_DB_PATH / "structural"
    
    # Reset collection if it already exists to avoid duplicates
    if store_path.exists():
        Chroma(
            persist_directory=str(store_path), 
            embedding_function=embeddings
        ).delete_collection()

    vectorstore = Chroma(
        persist_directory=str(store_path),
        embedding_function=embeddings
    )

    BATCH_SIZE = 100
    print(f"Indexing {len(langchain_docs)} chunks into ChromaDB in batches of {BATCH_SIZE}...")
    
    for i in tqdm(range(0, len(langchain_docs), BATCH_SIZE), desc="Embedding Batches"):
        batch = langchain_docs[i:i + BATCH_SIZE]
        vectorstore.add_documents(batch)

    count = vectorstore._collection.count()
    print(f"✅ Indexed {count} vectors into ChromaDB at '{store_path}'.")


def main():
    docs = fetch_documents()
    
    all_chunks = []
    for doc in docs:
        doc_chunks = chunk_vachanamrut_document(doc)
        all_chunks.extend(doc_chunks)

    print(f"✅ Fast chunking complete! Generated {len(all_chunks)} chunks from {len(docs)} documents.")

    # Save clean JSON
    with open(CHUNKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved chunks to {CHUNKS_JSON_PATH}")

    # Index into Chroma
    index_chunks_to_chroma(all_chunks)


if __name__ == "__main__":
    main()