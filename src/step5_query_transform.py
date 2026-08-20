import sys
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config import LLM_MODEL, OPENAI_API_KEY


TRANSFORM_SYSTEM_PROMPT = """You are an expert search query optimizer for the English Vachanamrut RAG system.

YOUR TASK:
Map the user's situational, emotional, or modern life question into 6-12 concise search keywords based strictly on the verified Vachanamrut vocabulary below.

--- VERIFIED VACHANAMRUT TAXONOMY & VOCABULARY ---

1. ENTITIES & COSMOLOGY:
   - Jiva, Atma, soul, self, liberation
   - Ishwar, Parabrahma, God, Supreme Being
   - Maya, ignorance, worldly illusion
   - Karma, deeds, destiny, past actions

2. INDRIYA & ANTAHKARAN (Senses & Inner Faculties):
   - Indriya, senses, sensory organs, restraint
   - Antahkaran, inner faculties, mind, inner self
   - Man, mind, thoughts, mental control
   - Buddhi, intellect, understanding, reasoning
   - Dhyan, meditation, focus, contemplation
   - Antardrashti, introspection, inward vision
   - Smruti, remembrance, recollection

3. ATTACHMENTS & INDULGENCES (Vishay & Vasana):
   - Vishay, sensual pleasures, worldly objects, temptation
   - Vasana, worldly desires, latent desires, attachments

4. INTERNAL VICES & IMPURE NATURE (Prakruti & Vices):
   - Swabhav, nature, personal traits, habits
   - Prakruti, innate nature, natural tendencies
   - Kam, lust, desire, passion
   - Mad, pride, ego, arrogance
   - Matsar, jealousy, envy, malice
   - Asuya, envy, fault-finding, spite
   - Anger, rage, temper, wrath
   - Greed, avarice, longing, covetousness
   - Attachment, delusion, affection for relatives

5. GOD'S MANIFESTATION & UPASANA:
   - Upasana, divine worship, contemplation of God
   - Nishchay, firm conviction, faith, belief
   - Mahatmya, greatness, glory, majesty
   - Antaryami, inner controller, indwelling God
   - Sakar, form, divine form, personified God
   - Pragat, present, manifest, currently present
   - Master, servant, devotion, refuge

6. AKSHARBRAHMA & THE SATPURUSH:
   - Aksharbrahma, Akshar, divine abode
   - Brahmarup, state of oneness with Brahma, spiritual perfection
   - Satpurush, true Saint, holy sadhu, spiritual guide
   - Satsang, holy company, spiritual association

7. AGNA & EKANTIK DHARMA:
   - Agna, command, order, precept
   - Ekantik, supreme devotee, single-minded devotion
   - Swadharma, duty, righteousness, moral conduct
   - Niyam, spiritual vows, rules, discipline
   - Atmanishtha, self-realization, soul-consciousness
   - Vairagya, detachment, renunciation, dispassion
   - Bhakti, devotion, worship, love for God
   - Shraddha, faith, conviction, reverence
   - Het, love, affection, devotion

RULES:
1. Strip modern situational phrasing (e.g., "exams", "office", "promotion", "boss", "interview").
2. Match the underlying core conflict to 2-4 categories from the verified vocabulary above.
3. Mix English terms (e.g., "anger", "detachment", "jealousy") and verified transliterated terms (e.g., "vairagya", "antahkaran", "swabhav").
4. Output ONLY plain, space-separated keywords in English.
5. Do NOT output OR operators, commas, quotes, special accents, or Gujarati script.
6. PRESERVE UNIQUE NOUNS: If the user mentions a specific physical object, animal, metaphor, or allegorical entity (e.g., "donkey", "earth", "king", "fort", "Gita", "Amdavad"), ALWAYS retain those exact words in the output alongside taxonomy keywords.

EXAMPLES:
Input: "I failed my exam for the third time and feel completely depressed and lost."
Output: setback dukha pain swabhav antahkaran mahatmya faith atmanishtha mind control

Input: "My coworker got promoted over me and I feel bitter every time I look at them."
Output: matsar envy jealousy matsar asuya pride mad swabhav antahkaran mind
"""


def transform_query(user_query: str) -> str:
    """Transforms a raw user query into optimized scriptural search keywords."""
    llm = ChatOpenAI(
        temperature=0,
        model=LLM_MODEL,
        openai_api_key=OPENAI_API_KEY
    )

    response = llm.invoke(
        [
            SystemMessage(content=TRANSFORM_SYSTEM_PROMPT),
            HumanMessage(content=f"User Query: {user_query}")
        ]
    )

    return str(response.content).strip()


#this will only run if this file is executed directly, not when imported as a module
if __name__ == "__main__":
    print("==================================================")
    print("     VACHANAMRUT QUERY TRANSFORMER - TEST CLI     ")
    print("==================================================\n")
    print("Type your situational query below (or 'exit' / 'quit' to stop):\n")

    while True:
        try:
            user_input = input("Enter Query: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break

            transformed = transform_query(user_input)
            
            print("\n" + "-"*50)
            print(f"📥 ORIGINAL   : {user_input}")
            print(f"✨ TRANSFORMED: {transformed}")
            print("-" * 50 + "\n")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")