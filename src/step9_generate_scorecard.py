import argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def create_linkedin_scorecard(csv_path: str, output_img: str, arch_name: str):
    df = pd.read_csv(csv_path)
    
    # Calculate all key metrics
    total_tests = len(df)
    hit_rate = (df['source_found'].mean() * 100) if 'source_found' in df else 0.0
    keyword_cov = (df['keyword_coverage'].mean() * 100) if 'keyword_coverage' in df else 0.0
    mean_mrr = df['mrr'].mean() if 'mrr' in df else 0.0
    mean_ndcg = df['ndcg'].mean() if 'ndcg' in df else 0.0
    
    mean_accuracy = df['accuracy'].mean() if 'accuracy' in df else 0.0
    mean_relevance = df['relevance'].mean() if 'relevance' in df else 0.0
    mean_completeness = df['completeness'].mean() if 'completeness' in df else 0.0

    # Print Full Text Scorecard to Terminal
    print("=" * 50)
    print(f"   RAG MASTER SCORECARD - {arch_name.upper()}   ")
    print("=" * 50)
    print(f" Total Evaluated Queries : {total_tests}")
    print(f" Source Retrieval Hit Rate: {hit_rate:.1f}%")
    print(f" Keyword Coverage Rate   : {keyword_cov:.1f}%")
    print(f" Mean Retrieval MRR      : {mean_mrr:.3f}")
    print(f" Mean Retrieval nDCG     : {mean_ndcg:.3f}")
    print(f" Mean LLM Answer Accuracy: {mean_accuracy:.2f} / 5.0")
    print(f" Mean Answer Relevance   : {mean_relevance:.2f} / 5.0")
    print(f" Mean Answer Completeness: {mean_completeness:.2f} / 5.0")
    print("=" * 50)

    # Generate Image Card for LinkedIn
    fig, ax = plt.subplots(figsize=(8, 7.5), dpi=300)
    fig.patch.set_facecolor('#0f172a')  # Slate Dark Background
    ax.set_facecolor('#0f172a')
    ax.axis('off')

    # Main Title
    ax.text(0.5, 0.93, "Vachanamrut RAG System", color='#38bdf8', fontsize=20, weight='bold', ha='center')
    
    # Dynamic Architecture Subtitle
    ax.text(0.5, 0.87, f"Architecture Benchmark: {arch_name}", color='#facc15', fontsize=12, weight='bold', ha='center')

    # Draw Top Divider Line
    ax.plot([0.1, 0.9], [0.83, 0.83], color='#334155', lw=1.5)

    # All Comprehensive Metrics
    metrics = [
        ("Total Queries Evaluated", f"{total_tests}"),
        ("Source Hit Rate (Recall@4)", f"{hit_rate:.1f}%"),
        ("Keyword Coverage Rate", f"{keyword_cov:.1f}%"),
        ("Mean Retrieval MRR", f"{mean_mrr:.3f}"),
        ("Mean Retrieval nDCG", f"{mean_ndcg:.3f}"),
        ("Mean LLM Answer Accuracy", f"{mean_accuracy:.2f} / 5.0"),
        ("Answer Relevance Score", f"{mean_relevance:.2f} / 5.0"),
        ("Answer Completeness Score", f"{mean_completeness:.2f} / 5.0"),
    ]

    y_pos = 0.76
    for label, val in metrics:
        ax.text(0.12, y_pos, label, color='#e2e8f0', fontsize=11, weight='medium', va='center')
        
        # Color coding: Green for %, Yellow for 5.0 scores and decimals
        value_color = '#4ade80' if '%' in val else '#facc15'
        ax.text(0.88, y_pos, val, color=value_color, fontsize=12, weight='bold', ha='right', va='center')
        
        y_pos -= 0.075

    # Draw Bottom Divider Line
    ax.plot([0.1, 0.9], [0.12, 0.12], color='#334155', lw=1.5)
    ax.text(0.5, 0.06, f"Evaluated using Structural Chunks • {arch_name}", 
            color='#64748b', fontsize=9, ha='center')

    # Save PNG
    plt.tight_layout()
    plt.savefig(output_img, bbox_inches='tight', facecolor=fig.get_facecolor(), pad_inches=0.4)
    plt.close()
    print(f"\nImage Scorecard successfully saved to: '{output_img}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=str, default="results/eval_results.csv", help="Input CSV path")
    parser.add_argument("--out_img", type=str, default="results/scorecard.png", help="Output PNG path")
    parser.add_argument("--arch", type=str, default="BM25 + Dense RRF Hybrid Search", help="Architecture label for image header")
    args = parser.parse_args()
    
    create_linkedin_scorecard(args.csv, args.out_img, args.arch)

#to run:
# python -m src.step9_generate_scorecard --csv results/eval_results_dense.csv --out_img results/scorecard_dense.png --arch "Pure Dense Vector Search"
# python -m src.step9_generate_scorecard --csv results/eval_results_hybrid.csv --out_img results/scorecard_hybrid.png --arch "BM25 + Dense RRF Hybrid Search"