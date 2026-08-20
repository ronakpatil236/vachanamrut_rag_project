#this script parses the structured JSON data of Vachanamrut entries and converts them into individual Markdown files organized by section. It ensures that the output directory structure is created as needed and handles various content types such as headers, shlokas, body text, and footnotes.
# src/step2_parser.py
import json
import re
from pathlib import Path

# Import path configurations from central config
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR

# Define output directory
OUTPUT_BASE_DIR = PROCESSED_DATA_DIR / "vachanamruts"


def extract_section_and_slug(title: str) -> tuple[str, str]:
    """Extracts section directory name and a clean filename slug from a chapter title.
    
    Example input: "Gadhada I-1: Continuously Engaging One's Mind on God"
    Returns: ("Gadhada_I", "Gadhada_I-1")
    """
    header_part = title.split(":")[0].strip()  # "Gadhada I-1"

    # Match section part before the numeric dash (e.g., "Gadhada I", "Sarangpur", "Additional")
    section_match = re.search(
        r"^(Gadhada\s+[I|V|X]+|Sarangpur|Kariyani|Loya|Panchala|Vartal|Vadtal|Amdavad|Ahmedabad|Ashlali|Jetalpur|Additional)",
        header_part,
        re.IGNORECASE,
    )

    if section_match:
        section_folder = section_match.group(1).strip().replace(" ", "_")
    else:
        section_folder = "General"

    filename_slug = header_part.replace(" ", "_").replace("-", "_")
    return section_folder, filename_slug


def parse_json_to_markdown():
    json_path = RAW_DATA_DIR / "vachanamrut_raw.json"

    if not json_path.exists():
        raise FileNotFoundError(
            f"[-] Raw JSON file not found at {json_path}. Please run step1_scraper first."
        )

    print(f" Reading raw JSON data from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        chapters = json.load(f)

    print(f" Processing {len(chapters)} chapters into Markdown files...")

    for ch in chapters:
        chapter_id = ch.get("chapter_id")
        title = ch.get("title", f"Vachanamrut {chapter_id}")
        blocks = ch.get("blocks", [])

        section_folder, slug = extract_section_and_slug(title)
        target_dir = OUTPUT_BASE_DIR / section_folder
        target_dir.mkdir(parents=True, exist_ok=True)

        md_filename = f"{slug}.md"
        file_path = target_dir / md_filename

        md_lines = []
        has_footnotes = False

        for block in blocks:
            if "::" not in block:
                continue

            prefix, content = block.split("::", 1)
            content = content.strip()

            if prefix == "HEADER":
                md_lines.append(f"# {content}\n")
            elif prefix == "SHLOKA":
                md_lines.append(f"> *{content}*\n")
            elif prefix == "FOOTNOTE":
                if not has_footnotes:
                    md_lines.append("## Footnotes\n")
                    has_footnotes = True
                md_lines.append(f"* {content}")
            elif prefix == "BODY":
                md_lines.append(f"{content}\n")

        # Write clean markdown file
        markdown_content = "\n".join(md_lines)
        markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    print(
        f" Successfully saved all individual Markdown files in: {OUTPUT_BASE_DIR}"
    )


if __name__ == "__main__":
    parse_json_to_markdown()