# this script is designed to retrieve relevant context chunks from the Vachanamrut text and generate grounded responses to user queries using OpenAI's language model. It supports both dense vector search and hybrid retrieval methods, combining BM25 keyword search with vector similarity search for improved accuracy.
import json
from typing import Any, Dict, List, Literal, Optional

from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from src.config import (
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    LLM_MODEL,
    OPENAI_API_KEY,
    PROCESSED_DATA_DIR,
)

SYSTEM_PROMPT_TEMPLATE = """You are a compassionate, grounded spiritual guide answering questions based on the Vachanamrut text.

INSTRUCTIONS:
1. Practical Synthesis: Synthesize the provided Vachanamrut context chunks to directly address the user's situation. Apply spiritual doctrines (e.g., managing swabhav, overcoming worldly distress/setbacks, understanding God's will, maintaining stability of mind) directly to the user's feelings.
2. Citation Integrity: Attach inline citations ONLY using the exact Reference ID provided in the context (e.g., [Gadhada I-70], [Sarangpur 18]).
3. Scriptural Nuance: Adhere strictly to the text without hallucinating. Do NOT fabricate Vachanamrut section numbers.
4. Refusal Trigger: ONLY output "I couldn't find specific references for this in the Vachanamrut." if the retrieved context is completely empty or has zero relevance to spiritual growth, mind control, or emotional resilience.

Context:
{context}
"""


def reciprocal_rank_fusion(
    doc_lists: List[List[Document]],
    weights: Optional[List[float]] = None,
    k: int = 60,
    top_n: int = 4,
) -> List[Document]:
  """Combines BM25 and Vector search results using Reciprocal Rank Fusion (RRF)."""
  if weights is None:
    weights = [0.5] * len(doc_lists)

  scores: Dict[str, float] = {}
  doc_lookup: Dict[str, Document] = {}

  for list_idx, docs in enumerate(doc_lists):
    weight = weights[list_idx]
    for rank, doc in enumerate(docs):
      doc_key = doc.page_content.strip()
      if doc_key not in doc_lookup:
        doc_lookup[doc_key] = doc

      scores[doc_key] = scores.get(doc_key, 0.0) + weight * (
          1.0 / (k + rank + 1)
      )

  sorted_keys = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
  return [doc_lookup[key] for key in sorted_keys[:top_n]]


def get_vector_store(store_type: str = "structural") -> Chroma:
  """Connects to the persisted Chroma vector store."""
  embeddings = OpenAIEmbeddings(
      model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY
  )

  target_path = CHROMA_DB_PATH / store_type
  if not target_path.exists():
    raise FileNotFoundError(
        f"Vector store path not found at '{target_path}'. "
        "Please ensure you ran step3b_chunker_structural.py first."
    )

  return Chroma(
      persist_directory=str(target_path), embedding_function=embeddings
  )


def load_chunks_from_json(store_type: str = "structural") -> List[Document]:
  """Auto-loads structural document chunks to initialize BM25 search."""
  json_path = PROCESSED_DATA_DIR / f"vachanamrut_{store_type}_chunks.json"

  if not json_path.exists():
    raise FileNotFoundError(
        f"Cannot find chunks JSON file at {json_path} for BM25 initialization."
    )

  with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

  return [
      Document(page_content=item["page_content"], metadata=item["metadata"])
      for item in data
  ]


def build_bm25_retriever(documents: List[Document], k: int = 4) -> BM25Retriever:
  """Creates a BM25 Keyword Retriever from document chunks."""
  bm25 = BM25Retriever.from_documents(documents)
  bm25.k = k
  return bm25


def answer_question(
    question: str,
    search_query: Optional[str] = None,
    retriever_type: Literal["dense", "hybrid"] = "hybrid",
    store_type: str = "structural",
    all_chunks: Optional[List[Document]] = None,
    k: int = 4,
) -> str:
  """Retrieves context chunks and generates a grounded response using OpenAI."""
  # If search_query is not specified, default to using the raw question
  retrieval_query = search_query if search_query else question

  vectorstore = get_vector_store(store_type=store_type)
  dense_retriever = vectorstore.as_retriever(
      search_type="similarity", search_kwargs={"k": k}
  )

  if retriever_type == "dense":
    docs = dense_retriever.invoke(retrieval_query)
  elif retriever_type == "hybrid":
    if not all_chunks:
      all_chunks = load_chunks_from_json(store_type=store_type)

    # 1. Fetch a broader candidate pool (12 candidates each)
    candidate_k = max(k * 3, 12)

    bm25_retriever = build_bm25_retriever(all_chunks, k=candidate_k)

    candidate_dense_retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": candidate_k}
    )

    # 2. Invoke both retrievers on the larger pool using the optimized retrieval_query
    bm25_docs = bm25_retriever.invoke(retrieval_query)
    dense_docs = candidate_dense_retriever.invoke(retrieval_query)

    # 3. RRF merges candidates and extracts the absolute best top_n (k=4)
    docs = reciprocal_rank_fusion(
        [bm25_docs, dense_docs], weights=[0.5, 0.5], top_n=k
    )

  if not docs:
    return "I couldn't find specific references for this in the Vachanamrut."

  llm = ChatOpenAI(
      temperature=0, model=LLM_MODEL, openai_api_key=OPENAI_API_KEY
  )

  context_blocks = []
  for doc in docs:
    chapter_id = doc.metadata.get("chapter") or doc.metadata.get(
        "section", "Unknown Section"
    )
    clean_ref = (
        chapter_id.replace("_", " ") if "_" in chapter_id else chapter_id
    )

    content = doc.page_content.strip()
    block = f"--- REFERENCE ID: [{clean_ref}] ---\n{content}"
    context_blocks.append(block)

  context = "\n\n".join(context_blocks)

  system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

  # LLM gets the original user question so full emotional/situational context is preserved
  final_user_prompt = (
      f"User Query: {question}\n\n"
      f"Based strictly on the provided context, address the user's situation. "
      f"Cite the exact Reference ID [e.g., Gadhada I-15] for every claim made."
  )

  response = llm.invoke([
      SystemMessage(content=system_prompt),
      HumanMessage(content=final_user_prompt),
  ])

  return str(response.content)


if __name__ == "__main__":
    test_queries = [
        "Someone at work just got promoted over me, and every time I see them celebrating, my chest tightens and I feel angry inside. How do I stop feeling bitter about someone else's success?",
        "I often feel that I am doing everything right in my spiritual life while others around me are lazy and careless. How should I view my own progress compared to others?",
        "When another devotee makes a mistake, I catch myself pointing it out to others and focusing only on their flaws. What does the text say about looking at faults in others?",
        "What does shriji maharaj talk about sitting on a donkey?",
        "Even when I try to focus during prayers, my thoughts wander to old arguments and past desires. How do I train my thoughts to stay fixed on God?"
    ]
    
    # Configure the active search mode here ("dense" or "hybrid")
    active_mode = "hybrid"
    
    print("==================================================")
    print(f"Testing {active_mode.upper()} Search on Structural Chunks across Multiple Queries")
    print("==================================================\n")
    
    for idx, query in enumerate(test_queries, 1):
        print(f"--- QUERY {idx} ---")
        print(f"Q: {query}\n")
        
        answer = answer_question(query, retriever_type=active_mode, store_type="structural")
        
        print("--- ANSWER ---")
        print(answer)
        print("\n" + "="*50 + "\n")



 