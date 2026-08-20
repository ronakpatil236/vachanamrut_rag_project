import os
import sys
from typing import Any, Dict

# Ensure the root directory is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.step4_retriever import answer_question
from src.step5_query_transform import transform_query


def run_vachanamrut_rag(
    user_query: str,
    retriever_type: str = "hybrid",
    store_type: str = "structural",
    verbose: bool = True,
) -> Dict[str, Any]:
    """Main pipeline orchestrator for the Vachanamrut RAG system."""
    if verbose:
        print("\n" + "=" * 60)
        print("         VACHANAMRUT AI - SPIRITUAL WISDOM RAG         ")
        print("=" * 60)
        print(f"\n📥 [ORIGINAL QUERY]:\n   {user_query}\n")

    # Step 1: Transform Query
    if verbose:
        print("🔄 [STEP 1]: Optimizing Query with Scriptural Keywords...")

    transformed_query = transform_query(user_query)

    # Combine original query (literal nouns/entities) + transformed terms (spiritual concepts)
    combined_search_query = f"{user_query} {transformed_query}".strip()

    if verbose:
        print(f"✨ [TRANSFORMED KEYWORDS]:\n   {transformed_query}")
        print(f"🎯 [COMBINED SEARCH QUERY]:\n   {combined_search_query}\n")

    # Step 2: Hybrid Retrieval & Answer Generation
    if verbose:
        print(
            f"🔍 [STEP 2]: Executing {retriever_type.upper()} Retrieval on"
            f" '{store_type}' store & Generating Answer..."
        )

    # Pass original user_query for response formatting, combined_search_query for database retrieval
    answer = answer_question(
        question=user_query,
        search_query=combined_search_query,
        retriever_type=retriever_type,
        store_type=store_type,
    )

    if verbose:
        print("\n" + "-" * 60)
        print("💡 [ANSWER]:")
        print("-" * 60)
        print(answer)
        print("=" * 60 + "\n")

    return {
        "original_query": user_query,
        "transformed_query": transformed_query,
        "search_query": combined_search_query,
        "answer": answer,
        "retriever_type": retriever_type,
        "store_type": store_type,
    }


def main():
    print("Welcome to Vachanamrut RAG CLI! Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("Ask a spiritual or life question: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Jai Swaminarayan! Goodbye.")
                break

            run_vachanamrut_rag(
                user_input, retriever_type="hybrid", store_type="structural"
            )

        except KeyboardInterrupt:
            print("\nExiting... Jai Swaminarayan!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}\n")


if __name__ == "__main__":
    main()