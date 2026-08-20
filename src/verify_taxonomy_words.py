import os
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
VACHANAMRUTS_DIR = BASE_DIR / "data" / "processed" / "vachanamruts"

# Extract all taxonomy terms from our prompt (English concepts & transliterated Gujarati)
TAXONOMY_TERMS = [
    # Entities & Cosmology
    "Jiva", "Jivanu Swarup", "Atma", "Ishwar", "Ishwarnu Swarup", "Parabrahma", "Maya",
    "Karma", "Sanskar", "Purva Sanskar", "Shubh-Ashubh", "Desh-kaladik", "Desh-kal",

    # Indriya & Antahkaran
    "Indriya", "Antahkaran", "Man", "Buddhi", "Chitta", "Dhyan", "Antardrashti",
    "Akhand-vrutti", "Smruti",

    # Vasana & Panch-Vishay
    "Vasana", "Panch-vishay", "Vishay", "Asakti",

    # Antar-shatruo & Malin Swabhav
    "Antar-shatru", "Antar-shatruo", "Swabhav", "Malin", "Prakruti", "Kam", "Krodh", 
    "Lobh", "Moh", "Mad", "Man", "Dehabhiman", "Matsar", "Irshya", "Asuya", "Kapat", 
    "Dambh", "Sneh",

    # Upasana & Manifestation
    "Nishchay", "Nishtha", "Asharo", "Upasana", "Mahatmya", "Mahatmya-gnan", "Pratap",
    "Aishwarya", "Sarva Karta-Harta", "Karta-Niyanta", "Antaryami", "Sarvagna",
    "Karma-fal-pradata", "Sakar", "Divyabhav", "Sarvopari", "Swami-Sevak",

    # Pragat Bhagwan & Aksharbrahma
    "Pragat", "Aksharbrahma", "Brahmarup",

    # Agna & Ekantik Dharma
    "Agna", "Ekantik", "Swadharma", "Niyam", "Tap", "Deh-daman", "Atmanishtha",
    "Vairagya", "Bhakti", "Leela", "Leela-charitro", "Nirvighna", "Priti", "Het",
    "Pativrata", "Pratilom", "Janpanu", "Shraddha",

    # Satsang & Service
    "Kalyan", "Katha-varta", "Satsang", "Samagam", "Satpurush", "Seva", "Paksha",
    "Abhav", "Avagun", "Abhav-avagun", "Droh", "Gungrahak", "Gungrahak-drashti",
    "Kusang", "Vimukh", "Yatharth", "Puro", "Pako"
]


def verify_terms():
    if not VACHANAMRUTS_DIR.exists():
        print(f"❌ Directory not found: {VACHANAMRUTS_DIR}")
        return

    # Read all markdown files across all section subfolders
    md_files = list(VACHANAMRUTS_DIR.rglob("*.md"))
    print(f"📄 Found {len(md_files)} markdown files in {VACHANAMRUTS_DIR}.\n")

    # Combine all text into memory for fast searching (case-insensitive)
    combined_text = ""
    file_contents = {}

    for file_path in md_files:
        content = file_path.read_text(encoding="utf-8").lower()
        file_contents[file_path.name] = content
        combined_text += f" {content} "

    print("=" * 70)
    print(f"{'TAXONOMY TERM':<25} | {'TOTAL COUNT':<12} | {'STATUS'}")
    print("=" * 70)

    missing_terms = []
    found_terms = []

    for term in TAXONOMY_TERMS:
        # Search using word boundary regex for exact matching
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        matches = re.findall(pattern, combined_text)
        count = len(matches)

        if count > 0:
            found_terms.append((term, count))
            print(f"{term:<25} | {count:<12} | ✅ EXPLICIT MATCH")
        else:
            missing_terms.append(term)
            print(f"{term:<25} | {count:<12} | ❌ NOT IN TEXT")

    print("=" * 70)
    print(f"\n📊 SUMMARY:")
    print(f"   - Total Terms Tested: {len(TAXONOMY_TERMS)}")
    print(f"   - Terms Present in Text: {len(found_terms)}")
    print(f"   - Terms Missing from Text: {len(missing_terms)}")

    if missing_terms:
        print("\n⚠️ MISSING TERMS LIST (Remove or replace in prompt):")
        for term in missing_terms:
            print(f"   - {term}")
    print("=" * 70)


if __name__ == "__main__":
    verify_terms()