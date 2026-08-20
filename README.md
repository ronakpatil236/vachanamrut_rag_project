# Vachanamrut Hybrid RAG Pipeline

Vachanamrut is a principal theological scripture of the Swaminarayan Sampradaya, which has a collection of 273 discourses delivered by Bhagwan Swaminarayan. My project is a production-grade, modular Retrieval-Augmented Generation (RAG) system built to query the sacred Vachanamrut text. 
This project compares standard dense vector retrieval against a hybrid system (Dense + Sparse BM25), featuring dynamic query expansion and an automated LLM-as-a-Judge evaluation framework.

## 📌 Features

* **Hybrid Retrieval:** Integrates ChromaDB (dense semantic search) with BM25 (sparse keyword search) to maximize recall and precision.
* **Query Transformation:** Expands user queries dynamically to catch complex or ambiguous phrasing across spiritual contexts.
* **Automated Evaluation:** Evaluates retrieval depth, answer faithfulness, and context relevance using `gemini-1.5-flash` as a judge.
* **Modular Codebase:** Organized into clean, reproducible steps from raw web scraping to final scorecard generation.

<img src="results/scorecard_dense.png" width="600" alt="Dense Retrieval Scorecard" />
<br/><br/>
<img src="results/scorecard_hybrid.png" width="600" alt="Hybrid Retrieval Scorecard" />
<br/><br/>
<img src="results/scorecard_transformed.png" width="600" alt="Query Transformed Scorecard" />

## 💡 Key Engineering Insights & Tradeoffs

Running benchmarks across all retrieval strategies revealed a critical architectural insight regarding **direct lookups** versus **situational queries**:

1. **Situational Queries Work Naturally:**
   Queries rooted in human scenarios or spiritual concepts (e.g., *"How do I stop feeling jealous at work?"* or *"How to strengthen faith during failure?"*) perform exceptionally well across Dense and Hybrid retrieval. The vector embeddings easily match emotional/conceptual intent to relevant spiritual discourses.

2. **Direct Scripture Lookups Fail in Raw Retriever:**
   Asking raw direct questions (e.g., *"What does Shriji Maharaj say in Gadhada I-15?"*) yields low retrieval accuracy in the standard retriever. Pure vector search lacks semantic understanding of specific section metadata, while BM25 fails if formatting variations (e.g., `Gadhada 1-15` vs `Gadhada I-15`) exist in the raw scraped chunks.

3. **Query Expansion Bridges the Vocabulary Gap:**
   Modern user queries use everyday conversational language (e.g., *"I feel jealous of my neighbor's new car"*), whereas the Vachanamrut relies on classical spiritual terminology. Running `transform_query` bridges this language gap by converting modern expressions into scriptural Gujarati keywords (such as *matsar*, *irshya*, *swabhav*, or *eghokh*). This allows BM25 and vector search to match real-world user intent directly to the underlying theological concepts.

### 🛠️ Production Takeaway
A standard RAG pipeline is great for semantic/situational user prompts, but struggles with explicit entity lookups. To make a RAG system production-ready for sacred texts:
* **Metadata Filtering:** Extract section identifiers (e.g., `Gadhada I-15`) using regex and apply direct metadata filters in ChromaDB rather than relying on pure vector/keyword search.
* **Topic Expansion:** Use query transformation to enrich direct lookups with relevant spiritual taxonomy keywords before running hybrid search.
* 
## 📁 Repository Structure

```text
├── data/                    # Raw & processed markdown files (DBs ignored in git)
├── interactive notebooks/    # Prototyping & exploratory analysis
├── results/                 # Evaluation scorecards and benchmark outputs
├── src/
│   ├── config.py            # Centralized directory & hyperparameter config
│   ├── step1_scraper.py     # Web scraping pipeline
│   ├── step2_parser.py      # Markdown parsing and cleaning
│   ├── step3a_chunker_recursive.py
│   ├── step3b_chunker_structural.py
│   ├── step4_retriever.py   # ChromaDB + BM25 hybrid setup
│   ├── step5_query_transform.py
│   ├── step6_pipeline.py    # End-to-end execution script
│   ├── step7_make_dataset.py
│   ├── step8_evals_dense.py
│   ├── step8_evals_hybrid.py
│   └── step9_generate_scorecard.py
├── app.py                   # Gradio / Web interface setup
├── pyproject.toml           # Environment setup via uv
└── README.md
