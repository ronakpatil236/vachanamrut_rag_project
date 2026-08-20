import sys
import os
import gradio as gr

# Ensure python can locate modules in src/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.step5_query_transform import transform_query
from src.step4_retriever import answer_question

def get_spiritual_guidance(user_query):
    if not user_query.strip():
        return "", "Please enter a question first."
    
    # Step 1: Query Transformation (Step 5)
    transformed_search_query = transform_query(user_query)
    
    # Step 2: Answer Generation via Hybrid RAG (Step 4)
    # Using transformed search query to retrieve best matching context
    answer = answer_question(
        question=transformed_search_query, 
        retriever_type="hybrid", 
        store_type="structural"
    )
    
    return transformed_search_query, answer

# Build Gradio UI
with gr.Blocks(title="Vachanamrut AI Guide") as demo:
    gr.Markdown("# 🙏 Vachanamrut Spiritual AI Guide")
    gr.Markdown("Grounded spiritual wisdom powered by Hybrid RAG & Vachanamrut Taxonomy")
    
    with gr.Row():
        with gr.Column(scale=2):
            query_input = gr.Textbox(
                label="Ask a life or spiritual question:",
                placeholder="e.g., Someone at work got promoted over me and I feel jealous...",
                lines=4
            )
            submit_btn = gr.Button("Seek Guidance", variant="primary")
            
    with gr.Row():
        with gr.Column(scale=2):
            keywords_output = gr.Textbox(
                label="🔍 Transformed Query (Step 5):",
                interactive=False
            )
            answer_output = gr.Markdown(label="💡 Guidance:")

    submit_btn.click(
        fn=get_spiritual_guidance,
        inputs=[query_input],
        outputs=[keywords_output, answer_output]
    )

if __name__ == "__main__":
    demo.launch()