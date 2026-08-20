import argparse
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

import pandas as pd

from src.config import PROCESSED_DATA_DIR, RESULTS_DIR
from src.step4_retriever import (
    answer_question, 
    get_vector_store, 
    load_chunks_from_json, 
    build_bm25_retriever, 
    reciprocal_rank_fusion
)
from src.eval import evaluate_answer, evaluate_retrieval


class TestItem:
    """Dataclass wrapper for test cases loaded from JSONL."""

    def __init__(self, data: dict):
        self.question = data.get("question", "")
        self.category = data.get("category", "Uncategorized")
        self.source_file = data.get("source_file", "")
        self.reference_answer = data.get("reference_answer", "")
        self.keywords = data.get("keywords", [])


def load_test_dataset(jsonl_path: Path | str) -> List[TestItem]:
    """Loads benchmark test cases from JSONL dataset."""
    path = Path(jsonl_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Test dataset not found at '{path}'. "
            "Please ensure tests.jsonl exists in your data directory."
        )

    tests = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                tests.append(TestItem(json.loads(line)))
    
    print(f"Loaded {len(tests)} evaluation tests from '{path.name}'.")
    return tests


# Pre-load BM25 chunks once globally to speed up evaluations
_ALL_CHUNKS = None
_BM25_RETRIEVER = None

def get_hybrid_chunks(query: str, k: int = 4):
    """Retrieves context chunks using the exact Hybrid RRF Retriever used in step4_retriever."""
    global _ALL_CHUNKS, _BM25_RETRIEVER
    if _ALL_CHUNKS is None:
        _ALL_CHUNKS = load_chunks_from_json(store_type="structural")
        _BM25_RETRIEVER = build_bm25_retriever(_ALL_CHUNKS, k=max(k * 3, 12))

    vectorstore = get_vector_store(store_type="structural")
    dense_retriever = vectorstore.as_retriever(search_kwargs={"k": max(k * 3, 12)})

    bm25_docs = _BM25_RETRIEVER.invoke(query)
    dense_docs = dense_retriever.invoke(query)

    return reciprocal_rank_fusion([bm25_docs, dense_docs], weights=[0.5, 0.5], top_n=k)


def run_single_eval(test_item: TestItem) -> Dict[str, Any]:
    try:
        # 1. Retrieval Evaluation (Evaluates actual Hybrid Search)
        retrieved_chunks = get_hybrid_chunks(test_item.question, k=4)
        retrieval_eval = evaluate_retrieval(test_item, retrieved_chunks)

        # 2. Answer Generation & Evaluation
        generated_ans = answer_question(
            test_item.question, 
            retriever_type="hybrid",
            store_type="structural"
        )
        answer_eval = evaluate_answer(test_item, generated_ans)

        return {
            "question": test_item.question,
            "category": test_item.category,
            "source_file": test_item.source_file,
            "source_found": retrieval_eval.source_file_found,
            "mrr": retrieval_eval.mrr,
            "ndcg": retrieval_eval.ndcg,
            "keywords_found": f"{retrieval_eval.keywords_found}/{retrieval_eval.total_keywords}",
            "keyword_coverage": retrieval_eval.keyword_coverage,
            "generated_answer": generated_ans,
            "reference_answer": test_item.reference_answer,
            "accuracy": answer_eval.accuracy,
            "completeness": answer_eval.completeness,
            "relevance": answer_eval.relevance,
            "judge_feedback": answer_eval.feedback,
            "status": "Success",
        }
    except Exception as e:
        return {
            "question": test_item.question,
            "category": test_item.category,
            "source_file": test_item.source_file,
            "source_found": False,
            "mrr": 0.0,
            "ndcg": 0.0,
            "keywords_found": f"0/{len(test_item.keywords)}",
            "keyword_coverage": 0.0,
            "generated_answer": f"Error: {str(e)}",
            "reference_answer": test_item.reference_answer,
            "accuracy": 0.0,
            "completeness": 0.0,
            "relevance": 0.0,
            "judge_feedback": f"Execution Error: {str(e)}",
            "status": "Failed",
        }


def run_all_evaluations(
    tests: List[TestItem], max_workers: int = 1
) -> pd.DataFrame:
    """Executes all test items sequentially or with controlled threads."""
    results = []
    total_tests = len(tests)
    print(
        f"\n🚀 Running evaluation for {total_tests} tests with {max_workers} worker thread(s)...\n"
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_test = {executor.submit(run_single_eval, t): t for t in tests}

        for idx, future in enumerate(as_completed(future_to_test), start=1):
            res = future.result()
            results.append(res)
            print(f"[{idx}/{total_tests}] Processed: {res['question'][:60]}...")

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(
        description="Run Vachanamrut RAG Benchmark Suite"
    )
    parser.add_argument(
        "--test_data",
        type=str,
        default=str(PROCESSED_DATA_DIR / "tests.jsonl"),
        help="Path to JSONL test dataset",
    )
    parser.add_argument(
        "--output_csv",
        type=str,
        default=str(RESULTS_DIR / "eval_results_hybrid.csv"),
        help="Path to save evaluation results CSV",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,  # Set to 1 to prevent ChromaDB multithreading locks
        help="Number of concurrent threads",
    )
    args = parser.parse_args()

    csv_path = Path(args.output_csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    tests = load_test_dataset(args.test_data)
    df = run_all_evaluations(tests, max_workers=args.workers)

    json_path = csv_path.with_suffix(".json")

    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2)

    print("\n" + "=" * 50)
    print(f"✅ Evaluation Complete!")
    print(f"📊 Total Evaluated: {len(df)}")
    if "source_found" in df.columns:
        print(f"🎯 Source Hit Rate: {df['source_found'].mean() * 100:.1f}%")
    if "accuracy" in df.columns:
        print(f"⭐ Mean Accuracy:   {df['accuracy'].mean():.2f} / 5.0")
    print(f"💾 CSV Saved to: '{csv_path}'")
    print(f"💾 JSON Saved to: '{json_path}'")
    print("=" * 50)


if __name__ == "__main__":
    main()