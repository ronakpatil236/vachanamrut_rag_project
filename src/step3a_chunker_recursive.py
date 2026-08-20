#this script loads the structured Markdown files of Vachanamrut entries, splits them into smaller chunks using a recursive text splitter that is aware of Markdown formatting, saves them to JSON for evaluation, and then embeds these chunks into a Chroma vector store for efficient retrieval.
# src/step3a_chunker_recursive.py
import json
import glob
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from src.config import (
    PROCESSED_DATA_DIR,
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
)


def load_documents(kb_directory: Path) -> list:
    """Loads Markdown files from the knowledge base directory and attaches metadata."""
    search_pattern = str(kb_directory / "**" / "*.md")
    file_paths = glob.glob(search_pattern, recursive=True)
    
    documents = []
    for file_path in file_paths:
        section_name = Path(file_path).parent.name
        file_name = Path(file_path).stem

        loader = TextLoader(file_path, encoding="utf-8")
        loaded_docs = loader.load()

        for doc in loaded_docs:
            doc.metadata["file_type"] = "markdown"
            doc.metadata["section"] = section_name
            doc.metadata["chapter"] = file_name
            documents.append(doc)

    print(f"Loaded {len(documents)} markdown files.")
    return documents


def create_chunks(documents: list, chunk_size: int = 1000, chunk_overlap: int = 200) -> list:
    """Splits loaded LangChain documents using Markdown-aware recursive text splitting."""
    text_splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN,
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Divided documents into {len(chunks)} chunks.")
    return chunks


def build_vector_store(chunks: list, persist_dir: Path) -> Chroma:
    """Embeds document chunks and saves them to a persistent Chroma vector store."""
    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL, 
        openai_api_key=OPENAI_API_KEY
    )

    store_path = persist_dir / "recursive"
    persist_dir_str = str(store_path)

    # Clean collection reset
    if store_path.exists():
        Chroma(
            persist_directory=persist_dir_str, 
            embedding_function=embeddings
        ).delete_collection()

    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory=persist_dir_str
    )
    
    count = vectorstore._collection.count()
    print(f"Successfully populated recursive vector store at '{store_path}' with {count} chunks.")
    return vectorstore


def main():
    kb_path = PROCESSED_DATA_DIR / "vachanamruts"

    if not kb_path.exists():
        raise FileNotFoundError(
            f"Knowledge base directory not found at: {kb_path}. "
            "Please run step2_parser first."
        )

    docs = load_documents(kb_path)
    chunks = create_chunks(docs)

    # Save recursive chunks to JSON for easy inspection/evals
    json_path = PROCESSED_DATA_DIR / "vachanamrut_recursive_chunks.json"
    json_data = [{"page_content": c.page_content, "metadata": c.metadata} for c in chunks]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"Saved recursive chunks to {json_path}")

    build_vector_store(chunks, CHROMA_DB_PATH)


if __name__ == "__main__":
    main()