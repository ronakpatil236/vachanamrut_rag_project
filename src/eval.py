import json
import re
from dataclasses import dataclass
from typing import List, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.config import LLM_MODEL, OPENAI_API_KEY

@dataclass
class RetrievalEvalResult:
    source_file_found: bool
    mrr: float
    ndcg: float
    keywords_found: int
    total_keywords: int
    keyword_coverage: float

@dataclass
class AnswerEvalResult:
    accuracy: float
    completeness: float
    relevance: float
    feedback: str

def normalize_source_name(name: str) -> str:
    """Standardizes file/chapter names for comparison by removing extensions and special characters."""
    if not name:
        return ""
    # Remove file extension (.md, .txt, etc.)
    name = re.sub(r'\.[a-zA-Z0-9]+$', '', name)
    # Replace underscores, hyphens, and multiple spaces with a single space
    name = re.sub(r'[-_]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip().lower()

def evaluate_retrieval(test_item: Any, retrieved_chunks: List[Any]) -> RetrievalEvalResult:
    """Evaluates keyword coverage, MRR, and source file hit rate with robust string normalization."""
    source_found = False
    rank = 0
    mrr = 0.0

    target_source = normalize_source_name(getattr(test_item, "source_file", ""))

    # Check source file matching across retrieved chunks
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        # Extract metadata flexibly checking common key variants
        meta = getattr(chunk, "metadata", {})
        chunk_source_raw = (
            meta.get("source_file") or 
            meta.get("source") or 
            meta.get("chapter") or 
            meta.get("file_path") or 
            meta.get("filename") or 
            ""
        )
        
        chunk_source = normalize_source_name(str(chunk_source_raw))

        # Perform bidirectional substring matching on normalized strings
        if target_source and chunk_source and (target_source in chunk_source or chunk_source in target_source):
            if not source_found:
                source_found = True
                rank = idx
                mrr = 1.0 / rank

    # Calculate keyword coverage across chunks
    combined_text = " ".join([getattr(c, "page_content", "").lower() for c in retrieved_chunks])
    total_keywords = len(getattr(test_item, "keywords", []))
    found_count = sum(1 for kw in getattr(test_item, "keywords", []) if kw.lower() in combined_text)
    coverage = (found_count / total_keywords) if total_keywords > 0 else 0.0

    ndcg = mrr  # Lightweight approximation for top-k

    return RetrievalEvalResult(
        source_file_found=source_found,
        mrr=mrr,
        ndcg=ndcg,
        keywords_found=found_count,
        total_keywords=total_keywords,
        keyword_coverage=coverage,
    )

def evaluate_answer(test_item: Any, generated_answer: str) -> AnswerEvalResult:
    """Uses LLM-as-a-Judge to evaluate accuracy, completeness, and relevance."""
    llm = ChatOpenAI(temperature=0, model=LLM_MODEL, openai_api_key=OPENAI_API_KEY)
    
    prompt = f"""You are an expert evaluator assessing RAG system responses.
Compare the Generated Answer against the Reference Answer for the given Question.

Question: {test_item.question}
Reference Answer: {test_item.reference_answer}
Generated Answer: {generated_answer}

Provide ratings from 1.0 to 5.0 and brief feedback in strict JSON format:
{{
  "accuracy": 5.0,
  "completeness": 5.0,
  "relevance": 5.0,
  "feedback": "Brief evaluation explanation..."
}}"""

    res = llm.invoke([
        SystemMessage(content="You are a precise JSON-only evaluation judge."),
        HumanMessage(content=prompt)
    ])

    try:
        clean_json = res.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean_json)
        return AnswerEvalResult(
            accuracy=float(data.get("accuracy", 0.0)),
            completeness=float(data.get("completeness", 0.0)),
            relevance=float(data.get("relevance", 0.0)),
            feedback=str(data.get("feedback", "")),
        )
    except Exception as e:
        return AnswerEvalResult(0.0, 0.0, 0.0, f"Judge parsing failed: {str(e)}")