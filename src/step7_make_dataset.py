# this code generates a clean dataset of evaluation questions for the Vachanamrut RAG system.
import json
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from pydantic import BaseModel, Field

from src.config import (
    PROCESSED_DATA_DIR,
    LLM_MODEL,
    OPENAI_API_KEY,
)

# Target file output: data/processed/tests.jsonl
OUTPUT_FILE = PROCESSED_DATA_DIR / "tests.jsonl"
INPUT_FOLDER = PROCESSED_DATA_DIR / "vachanamruts"

CATEGORIES = [
    "exact_analogy_or_parable",
    "named_entities_and_location",
    "explicit_definition_or_classification",
    "cause_and_effect_praxis",
    "textual_quote_grounding",
]


class EvaluationItem(BaseModel):
    source_file: str = Field(
        description="The source filename, e.g., 'Gadhada_I_1.md'"
    )
    question: str = Field(
        description="A specific, grounded question based ONLY on the text snippet."
    )
    keywords: list[str] = Field(
        description="3 to 5 key terms present in the text."
    )
    reference_answer: str = Field(
        description="Concise, factual ground-truth answer derived strictly from the text."
    )
    category: str = Field(description="The target category assigned.")


PROMPT_TEMPLATE = """You are a benchmark dataset generator for a Vachanamrut Retrieval-Augmented Generation (RAG) system.

Source Section: "{section_name}"
Source Text Chunk:
\"\"\"
{text_chunk}
\"\"\"

TARGET CATEGORY: "{target_category}"
Category Definitions:
- "exact_analogy_or_parable": Questions about specific physical illustrations, parables, or analogies used by Maharaj in this section.
- "named_entities_and_location": Questions about specific people (Paramhansas, devotees), locations, or historical context mentioned directly in this text.
- "explicit_definition_or_classification": Questions about specific theological terms, lists, or definitions explicitly defined in this section.
- "cause_and_effect_praxis": Practical questions about spiritual discipline, overcoming vices, or daily practice based STRICTLY on the instructions in this text.
- "textual_quote_grounding": Questions that ask for specific details or explanations unique to this exact Vachanamrut section.

CRITICAL RULES FOR GENERATION:
1. STRICT GROUNDING: The question and reference answer MUST be derived ENTIRELY from the provided text chunk. Do NOT use outside knowledge, commentary, or external Vachanamrut facts.
2. NO AMBIGUITY: The question must contain enough context from this section so that it targets THIS specific document during vector retrieval (e.g., mention specific terms or contexts from the text).
3. CONCISE ANSWER: The `reference_answer` should be a factual, ground-truth summary (2-4 sentences) directly supported by the text chunk.
4. KEYWORDS: Extract 3 to 5 precise keywords or phrases present in the text chunk.
"""

client = OpenAI(api_key=OPENAI_API_KEY)


def process_file(file_data: tuple) -> dict | None:
    file_path, category = file_data
    section_name = file_path.stem  # Gets filename without extension

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Could not read file {file_path.name}: {e}")
        return None

    if not content.strip():
        return None

    truncated_content = content[:3500]

    prompt = PROMPT_TEMPLATE.format(
        section_name=section_name,
        text_chunk=truncated_content,
        target_category=category,
    )

    try:
        response = client.beta.chat.completions.parse(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format=EvaluationItem,
        )

        data = response.choices[0].message.parsed.model_dump()
        print(f"✅ Generated [{category}] for: {section_name}")
        return data
    except Exception as e:
        print(f"❌ Error on {section_name}: {e}")
        return None


def generate_vachanamrut_dataset(limit: int | None = None):
    if not INPUT_FOLDER.exists():
        raise FileNotFoundError(
            f"Knowledge base folder not found at '{INPUT_FOLDER}'."
        )

    all_files = sorted(list(INPUT_FOLDER.rglob("*.md")))
    
    # If limit is specified, take only the first N files
    if limit:
        all_files = all_files[:limit]
        print(f"🧪 TEST MODE: Processing first {len(all_files)} files...\n")
    else:
        print(f"🚀 FULL RUN: Processing {len(all_files)} files...")

    tasks = [
        (file_path, CATEGORIES[idx % len(CATEGORIES)])
        for idx, file_path in enumerate(all_files)
    ]

    all_questions = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        for result in executor.map(process_file, tasks):
            if result:
                all_questions.append(result)

    # Print results cleanly to terminal if running a test batch
    if limit:
        print("=" * 60)
        print("SAMPLE OUTPUT PREVIEW:")
        print("=" * 60)
        for i, item in enumerate(all_questions, 1):
            print(f"\n--- Question {i} [{item['category']}] ---")
            print(f"File:     {item['source_file']}")
            print(f"Question: {item['question']}")
            print(f"Answer:   {item['reference_answer']}")
            print(f"Keywords: {', '.join(item['keywords'])}")
        print("=" * 60)
        return

    # Save to disk only during full runs
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_f:
        for q in all_questions:
            out_f.write(json.dumps(q, ensure_ascii=False) + "\n")

    print(f"\n🎉 Clean dataset generated successfully! Total: {len(all_questions)}")
    print(f"Saved to: '{OUTPUT_FILE}'")


if __name__ == "__main__":
    # Change limit=5 to limit=None when you are ready to run all 274 files!
    generate_vachanamrut_dataset(limit=None)  # Set limit=5 for testing, None for full run