#this script scrapes the Vachanamrut entries from the Anirdesh website, cleans the text, and saves it in a structured JSON format. It also has an option to generate a PDF document containing all the entries.
# src/step1_scraper.py
import time
import requests
import re
import json
import unicodedata
from bs4 import BeautifulSoup

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# Import path configurations from central config
from src.config import RAW_DATA_DIR

VACHANAMRUT_INDEX = {
    1: "Gadhada I-1: Continuously Engaging One's Mind on God",
    2: "Gadhada I-2: Three Levels of Vairagya",
    3: "Gadhada I-3: Remembering the Divine Actions and Incidents of God",
    4: "Gadhada I-4: Jealousy like that of Naradji",
    5: "Gadhada I-5: Persistence in Meditation",
    6: "Gadhada I-6: One with Wisdom and One without Wisdom",
    7: "Gadhada I-7: Anvay-Vyatirek",
    8: "Gadhada I-8: Engaging the Indriyas in the Service of God and His Sant",
    9: "Gadhada I-9: Desiring Nothing Except God",
    10: "Gadhada I-10: The Ungrateful Sevakram",
    11: "Gadhada I-11: Vasana; An Ekantik Bhakta",
    12: "Gadhada I-12: The Attributes of the Elements; Creation",
    13: "Gadhada I-13: Planting the Branch of a Banyan or Pipal Tree Elsewhere",
    14: "Gadhada I-14: Ante Ya Matihi Sa Gatihi",
    15: "Gadhada I-15: Not Becoming Discouraged in Meditation",
    16: "Gadhada I-16: Wisdom",
    17: "Gadhada I-17: Negative Influence in Satsang; Not Uttering Discouraging Words",
    18: "Gadhada I-18: Denouncing the Vishays; A Haveli",
    19: "Gadhada I-19: The Interdependency of Atma-realization and Other Virtues",
    20: "Gadhada I-20: An Ignorant Person; Seeing One's Own Self",
    21: "Gadhada I-21: One Possessing Ekantik Dharma; The Two Forms of Akshar",
    22: "Gadhada I-22: Singing without Remembering God Is as Good as Not Singing at All; The Digit '1'",
    23: "Gadhada I-23: Emptying a Pot of Water; Remaining in an Elevated Spiritual State",
    24: "Gadhada I-24: The Elevated Spiritual State of Gnan; 'Sourness' in the Form of the Understanding of God's Greatness",
    25: "Gadhada I-25: The Flow of Twenty Pails of Water",
    26: "Gadhada I-26: A Genuine Amorous Devotee; The Nirgun State",
    27: "Gadhada I-27: The Understanding by which God Eternally Resides within One",
    28: "Gadhada I-28: A Smouldering Log; Progressing and Regressing",
    29: "Gadhada I-29: Intensifying the Force of Dharma, Gnan, Vairagya and Bhakti; Prarabdha, Grace and Personal Endeavor",
    30: "Gadhada I-30: Thoughts that Leave a Lasting Impression",
    31: "Gadhada I-31: Greatness Is Due To Faith",
    32: "Gadhada I-32: A Nest and a Stake",
    33: "Gadhada I-33: Blind Faith, Love and Understanding",
    34: "Gadhada I-34: Setting the World in Motion",
    35: "Gadhada I-35: Safeguarding One's Liberation",
    36: "Gadhada I-36: A True Renunciant, Based on the Example of a Pauper",
    37: "Gadhada I-37: Attachment to One's Native Place; Eleven Honors",
    38: "Gadhada I-38: A Merchant's Balance Sheet",
    39: "Gadhada I-39: Those Possessing the Nirvikalp or Savikalp State",
    40: "Gadhada I-40: Savikalp and Nirvikalp Samadhi",
    41: "Gadhada I-41: Eko'ham Bahu Syam",
    42: "Gadhada I-42: The Observance of the Moral Do's and Don'ts",
    43: "Gadhada I-43: The Four Types of Liberation",
    44: "Gadhada I-44: A Red-hot Branding Iron; A Dagli",
    45: "Gadhada I-45: Does God Possess a Form or Is He Formless?",
    46: "Gadhada I-46: The Creation and Destruction of Akash",
    47: "Gadhada I-47: The Characteristics of Those Who Have the Four Types of Firmness",
    48: "Gadhada I-48: The Four Types of Kusangis",
    49: "Gadhada I-49: 'Antardrashti'",
    50: "Gadhada I-50: One Possessing a Sharp Intellect",
    51: "Gadhada I-51: Only a Diamond Can Cut a Diamond",
    52: "Gadhada I-52: Realizing God through the Four Scriptures",
    53: "Gadhada I-53: Progress and Regress",
    54: "Gadhada I-54: Upholding Bhagwat Dharma; The Gateway to Liberation",
    55: "Gadhada I-55: Resoluteness in Worship, Remembrance and Observance of Religious Vows",
    56: "Gadhada I-56: Hollow Stones",
    57: "Gadhada I-57: The Most Extraordinary Means to Attain Liberation",
    58: "Gadhada I-58: The Body, Bad Company and Past Sanskars; One Becomes like One Perceives the Great",
    59: "Gadhada I-59: Unparalleled Love",
    60: "Gadhada I-60: Observing Ekantik Dharma; Eradicating Worldly Desires",
    61: "Gadhada I-61: King Bali",
    62: "Gadhada I-62: Acquiring the Virtues of Satya, Shauch, Etc.",
    63: "Gadhada I-63: Faith; Realizing God Perfectly",
    64: "Gadhada I-64: The Relationship between Sharir and Shariri; A Master-Servant Relationship",
    65: "Gadhada I-65: 'Gnan-shakti', 'Kriya-shakti' and 'Ichchha-shakti'",
    66: "Gadhada I-66: Misinterpreting the Words of the Scriptures; The Four Emanations of God",
    67: "Gadhada I-67: Acquiring the Virtues of the Satpurush",
    68: "Gadhada I-68: God Forever Resides in the Eight Types of Murtis and in the Sant",
    69: "Gadhada I-69: The Dharma of a Wicked Person and a Sadhu",
    70: "Gadhada I-70: Kakabhai's Question; A Thief Injured by a Thorn",
    71: "Gadhada I-71: God Manifests with His Akshardham",
    72: "Gadhada I-72: Faith Coupled with the Knowledge of God's Greatness",
    73: "Gadhada I-73: Conquering Lust; Becoming Free of Worldly Desires",
    74: "Gadhada I-74: Understanding Is Measured in Times of Hardship",
    75: "Gadhada I-75: Redeeming Seventy-One Generations",
    76: "Gadhada I-76: An Angry Person, a Jealous Person, a Deceitful Person and an Egotistical Person",
    77: "Gadhada I-77: Not Invalidating Dharma under the Pretext of Gnan",
    78: "Gadhada I-78: The Predominance of Place, Time, Etc.",
    79: "Sarangpur-1: Conquering the Mind",
    80: "Sarangpur-2: Developing Affection for the Form of God",
    81: "Sarangpur-3: 'Shravan', 'Manan', 'Nididhyas' and 'Sakshatkar'",
    82: "Sarangpur-4: Wisdom in Discerning between Atma and Non-Atma",
    83: "Sarangpur-5: Anvay-Vyatirek",
    84: "Sarangpur-6: Two States within Each State; The Four Types of Speech",
    85: "Sarangpur-7: Naimisharanya Kshetra",
    86: "Sarangpur-8: The Characteristics of Jealousy",
    87: "Sarangpur-9: The Prevalence of the Dharma of the Yugs; 'Sthan'",
    88: "Sarangpur-10: A Physical Perspective versus the Atma's Perspective; Being Beaten by Shoes",
    89: "Sarangpur-11: Personal Endeavor",
    90: "Sarangpur-12: Thinking about the Atma",
    91: "Sarangpur-13: Losing Faith and Not Losing Faith",
    92: "Sarangpur-14: Laziness and Infatuation",
    93: "Sarangpur-15: Obstinate, Mediocre and Mature Gopis",
    94: "Sarangpur-16: Narnarayan's Austerities",
    95: "Sarangpur-17: Differences among Muktas; The Branch of a Tamarind Tree",
    96: "Sarangpur-18: Saline Land",
    97: "Kariyani-1: A Worm and a Bee",
    98: "Kariyani-2: A Cursed Intellect",
    99: "Kariyani-3: Shuk Muni Is a Great Sadhu; A Person Cannot Be Known by His Superficial Nature",
    100: "Kariyani-4: Awareness of the Jiva and the Witness",
    101: "Kariyani-5: God's Purpose for Assuming an Avatar",
    102: "Kariyani-6: One Who Possesses Matsar",
    103: "Kariyani-7: Vairagya Due to Obsession; Ultimate Liberation",
    104: "Kariyani-8: The Sagun and Nirgun Forms of God",
    105: "Kariyani-9: Obstinacy like a Buffalo",
    106: "Kariyani-10: Checking the Pulse; Austerities",
    107: "Kariyani-11: The Characteristic of Affection",
    108: "Kariyani-12: Destroying the Karan Body; A Tamarind Seed",
    109: "Loya-1: Anger; Developing Complete Satsang",
    110: "Loya-2: One with Faith, Gnan, Courage or Affection",
    111: "Loya-3: One with Faith in God Coupled with the Knowledge of His Greatness",
    112: "Loya-4: If One Doubts God, One Cannot Be Said to Have Overcome Maya",
    113: "Loya-5: Controlling the Indriyas and the Antahkaran",
    114: "Loya-6: Purifying the Company One Keeps",
    115: "Loya-7: Realizing God through the Indriyas, the Antahkaran and Experience",
    116: "Loya-8: Eradicating the Over-Excitability of the Indriyas; Accepting Only Words Related to One's Inclination",
    117: "Loya-9: Factors which Lead to the Development of Dharma, Gnan, Vairagya and Bhakti",
    118: "Loya-10: Remaining Uninfatuated",
    119: "Loya-11: Beliefs of a Holy and Unholy Person",
    120: "Loya-12: The Six Levels of Faith; Savikalp and Nirvikalp Faith",
    121: "Loya-13: Not Being Overcome by Adverse Circumstances",
    122: "Loya-14: Personal Preferences",
    123: "Loya-15: Explaining Atmadarshan Using the Analogies of a Doll and a Cow",
    124: "Loya-16: Worldly Desires Becoming Blunt and Uprooted",
    125: "Loya-17: Reverence and Condemnation",
    126: "Loya-18: Conviction of God",
    127: "Panchala-1: One Who Is Intelligent; Applying a Thought Process",
    128: "Panchala-2: Sankhya and Yoga",
    129: "Panchala-3: Muni Bawa; That Which Is Instrumental in Attaining Liberation Is Known as Intelligence",
    130: "Panchala-4: Perceiving Divinity in the Human Traits of God",
    131: "Panchala-5: Where Is Conceit Appropriate, and Where Is Humility Appropriate?",
    132: "Panchala-6: Those with Firm Upasana Attain Liberation",
    133: "Panchala-7: The 'Maya' of a Magician",
    134: "Gadhada II-1: The Cause of Infatuation",
    135: "Gadhada II-2: A Small Streamlet of Water",
    136: "Gadhada II-3: The Path of Amorousness and the Knowledge of the Atma",
    137: "Gadhada II-4: Constant Contemplation Is Achieved through Realizing the Greatness of God and Shraddha: A Torn Waistcloth and a Gourd",
    138: "Gadhada II-5: Fidelity and Courage",
    139: "Gadhada II-6: A Draft; The Nature of the Chitt",
    140: "Gadhada II-7: A Poor Man",
    141: "Gadhada II-8: Ekadashi; 'Gnan-Yagna'; 'Antardrashti'",
    142: "Gadhada II-9: Conviction of God; Realizing God to be like Other Avatars Is Blasphemy",
    143: "Gadhada II-10: Safeguarding the Fetus in the Form of Faith in God",
    144: "Gadhada II-11: All Karmas Becoming a Form of Bhakti",
    145: "Gadhada II-12: The Art of Ruling",
    146: "Gadhada II-13: Divine Light",
    147: "Gadhada II-14: Nirvikalp Samadhi",
    148: "Gadhada II-15: Keeping Enmity towards One's Swabhavs",
    149: "Gadhada II-16: Faith in God and Faith in Dharma",
    150: "Gadhada II-17: The Elements in the Form of God; 'Sthitapragna'",
    151: "Gadhada II-18: Nastiks and Shushka-Vedantis",
    152: "Gadhada II-19: Writing a Letter Having Become Distressed by Hearing Shushka-Vedanta Scriptures",
    153: "Gadhada II-20: How Do the Faculty of Knowing and the Strength of the Indriyas of One Who Has Mastered Samadhi Increase?",
    154: "Gadhada II-21: The Main Principle",
    155: "Gadhada II-22: Two Armies; The Installation of Nar-Narayan",
    156: "Gadhada II-23: Heat and Frost",
    157: "Gadhada II-24: Resoluteness in Sankhya and in Yoga; Choko-Patlo",
    158: "Gadhada II-25: A Renunciant Who Harbors Worldly Desires and a Householder Who Has No Worldly Desires",
    159: "Gadhada II-26: Suppressing Atma-realization and Other Virtues if They Obstruct Bhakti",
    160: "Gadhada II-27: The Great Are Pleased When No Impure Desires Remain",
    161: "Gadhada II-28: Maharaj's Compassionate Nature; A 'Lifeline'",
    162: "Gadhada II-29: The Characteristics of One Who Is Attached to God",
    163: "Gadhada II-30: Not Becoming Bound by Women and Gold",
    164: "Gadhada II-31: Associating with Brahma through Contemplation",
    165: "Gadhada II-32: A Cactus Plant; Unhindered Bhakti",
    166: "Gadhada II-33: The Vow of Non-Lust",
    167: "Gadhada II-34: Are the Elements Jad or Chaitanya?",
    168: "Gadhada II-35: The Underground Store of Grains",
    169: "Gadhada II-36: Four Means of Maintaining Continuous Vrutti",
    170: "Gadhada II-37: Eradicating One's Innate Natures; Even a Person Possessing Gnan Behaves According to His Nature",
    171: "Gadhada II-38: Mancha Bhakta; 'Merging'",
    172: "Gadhada II-39: Natural Virtues",
    173: "Gadhada II-40: Offering One Extra Prostration",
    174: "Gadhada II-41: A Bone in the Form of Egotism",
    175: "Gadhada II-42: Akshar Has Both Sagun and Nirgun Aspects; The Key",
    176: "Gadhada II-43: Brahmaswarup Love",
    177: "Gadhada II-44: The Characteristics of Godly and Demonic People",
    178: "Gadhada II-45: Expelling the Horde of the Fifty-One Bhuts",
    179: "Gadhada II-46: The 'Death-line'; Falling from Ekantik Dharma",
    180: "Gadhada II-47: A Split in the Pruthvi Down to Patal",
    181: "Gadhada II-48: The 'Vandu' Devotional Songs; Taking Birth in the Company of the Sant",
    182: "Gadhada II-49: A Great Difference Exists between God's Form and Mayik Forms; Not Becoming Content with Spiritual Discourses, Devotional Songs, etc.",
    183: "Gadhada II-50: The Fundamental Principle; Worldly Attachment",
    184: "Gadhada II-51: The Characteristics of One Who Behaves as the Atma",
    185: "Gadhada II-52: What Befits a Renunciant and What Befits a Householder",
    186: "Gadhada II-53: Not Being Able to Perceive One's Own Flaws Is Delusion",
    187: "Gadhada II-54: Satsang Is the Greatest Spiritual Endeavor; A 'Gokhar'; Profound Attachment",
    188: "Gadhada II-55: A Goldsmith's Workshop",
    189: "Gadhada II-56: A Lightly Dyed Cloth",
    190: "Gadhada II-57: The Example of a Lizard; A 'Cat-like' Devotee",
    191: "Gadhada II-58: The Flourishing of a Sampraday",
    192: "Gadhada II-59: Ultimate Liberation",
    193: "Gadhada II-60: Overcoming Difficulties; Being Loyal",
    194: "Gadhada II-61: Niyams, Faith in God, and Loyalty",
    195: "Gadhada II-62: Atma-Realization, Fidelity and Servitude",
    196: "Gadhada II-63: Gaining Strength",
    197: "Gadhada II-64: Purushottam Bhatt's Question",
    198: "Gadhada II-65: The Over-Wise",
    199: "Gadhada II-66: Questions to the Senior Sadhus; Holding a Red-Hot Iron Ball",
    200: "Gadhada II-67: The Gangajaliyo Well",
    201: "Vartal-1: Nirvikalp Samadhi",
    202: "Vartal-2: Realizing God through the Four Scriptures; Kandasji's Question",
    203: "Vartal-3: Four Types of Eminent Spiritual People",
    204: "Vartal-4: A Fountain",
    205: "Vartal-5: One Should Not Perceive Maya in God; Performing Similar Service",
    206: "Vartal-6: Chimanravji's Question",
    207: "Vartal-7: The Characteristics of Godly and Demonic People; Anvay-Vyatirek",
    208: "Vartal-8: A Spider's Web",
    209: "Vartal-9: How Can One Experience the Nirgun Bliss of God?",
    210: "Vartal-10: How the Jiva Attains Liberation",
    211: "Vartal-11: The Destruction of the Jiva; Love for the Satpurush Is the Only Means to Realizing the Atma",
    212: "Vartal-12: Faith Coupled with the Knowledge of God's Greatness",
    213: "Vartal-13: If Brahma Pervades, How Can It Possess a Form?",
    214: "Vartal-14: Whom a Non-believer Considers a Sinner Is Not a Sinner, and Whom He Considers to be Sincere in His Dharma Is Not Really So",
    215: "Vartal-15: The Reasons for Becoming Godly and Demonic",
    216: "Vartal-16: Not Feeling Comfortable with Worldly Great Men",
    217: "Vartal-17: An Enlightened Person Has Conquered His Indriyas",
    218: "Vartal-18: Facts That Must Be Understood",
    219: "Vartal-19: Becoming a Devotee of God; Indiscretion",
    220: "Vartal-20: King Janak's Understanding",
    221: "Amdavad-1: Miraculous Meditation",
    222: "Amdavad-2: Performing Puja after Washing and Bathing",
    223: "Amdavad-3: The Implanted Branch of a Banyan Tree; Upsham",
    224: "Gadhada III-1: The Inclinations of Gnan and Affection",
    225: "Gadhada III-2: The Attainment of All Purusharths; Incarnate God in the Form of the Guru",
    226: "Gadhada III-3: Compassion and Affection",
    227: "Gadhada III-4: Badhitanuvrutti",
    228: "Gadhada III-5: Bhakti Coupled with the Knowledge of God's Greatness",
    229: "Gadhada III-6: The Friendship between the Mind and the Jiva",
    230: "Gadhada III-7: An Iron Nail",
    231: "Gadhada III-8: Remaining Eternally Happy",
    232: "Gadhada III-9: The Gateway in the Form of Awareness",
    233: "Gadhada III-10: Vrundavan and Kashi",
    234: "Gadhada III-11: Understanding like that of Sitaji",
    235: "Gadhada III-12: A Magical Technique",
    236: "Gadhada III-13: Maintaining Ekantik Dharma amidst Adverse Circumstances",
    237: "Gadhada III-14: The Kayasth's Indiscretion; A Donkey",
    238: "Gadhada III-15: Applying Bandages to Wounds",
    239: "Gadhada III-16: The Vow of Fidelity",
    240: "Gadhada III-17: The Story of Bharatji",
    241: "Gadhada III-18: The Degeneration of Worldly Desires",
    242: "Gadhada III-19: Two Undesirable Traits of a Renunciant",
    243: "Gadhada III-20: 'Swabhav', 'Prakruti' and 'Vasana'",
    244: "Gadhada III-21: A Golden Thread; Dharma Possesses the Same Eminence as Bhakti",
    245: "Gadhada III-22: An Intimate Form of Bhakti",
    246: "Gadhada III-23: Mansi Puja",
    247: "Gadhada III-24: Sixteen Spiritual Endeavors; Vairagya Due To Gnan",
    248: "Gadhada III-25: Pleasing Shriji Maharaj; A True Devotee of God",
    249: "Gadhada III-26: The Sant Who Suppresses His Mind and Indriyas",
    250: "Gadhada III-27: Not Keeping Any Obstinacy",
    251: "Gadhada III-28: Falling from the Path of God",
    252: "Gadhada III-29: Two Twenty-Year-Old Devotees of God",
    253: "Gadhada III-30: Constant Awareness of Five Thoughts",
    254: "Gadhada III-31: A Method of Meditation Using the Example of a Shadow",
    255: "Gadhada III-32: Committing Sins under the Pretext of Knowing God's Greatness",
    256: "Gadhada III-33: Not Allowing the Mind to Become Affected by Four Things",
    257: "Gadhada III-34: Maintaining Desires Only for God",
    258: "Gadhada III-35: Forcefully Altering One's Innate Nature; God Is Maligned When His Bhakta Is Maligned",
    259: "Gadhada III-36: The Most Extraordinary Spiritual Endeavor for Liberation",
    260: "Gadhada III-37: Objects Enjoyed Previously Are Remembered in Times of Poverty",
    261: "Gadhada III-38: The Sankhya Scriptures and Others; Remaining Forever Happy",
    262: "Gadhada III-39: Vishalyakarani Herbal Medicine",
    263: "Additional: Bhugol-Khagol (Geography and Astronomy)",
    264: "Amdavad-4: Firm Conviction of the Form of God",
    265: "Amdavad-5: Most Extraordinary Characteristic of Shri Purushottam Narayan",
    266: "Amdavad-6: Unfaltering Conviction of God",
    267: "Amdavad-7: Firmly Fixing One's Mind on God",
    268: "Amdavad-8: Causes of Anger and Solutions to Overcome It",
    269: "Ashlali-1: Loss Suffered by Incompletely Realizing God's Form",
    270: "Jetalpur-1: Means to Transcend Maya and Profound Attachment to the Sant",
    271: "Jetalpur-2: Characteristics of a Yati and Nature of the Jiva",
    272: "Jetalpur-3: Method for Eradicating Impure Desires",
    273: "Jetalpur-4: Liberation through Faith in the Manifest form of God",
    274: "Jetalpur-5: Nothing Is Greater Than Worshipping God"
}


def clean_and_strip_devnagari(text):
    """Removes Devnagari/Gujarati scripts while preserving English, numbers, and punctuation."""
    if not text:
        return ""

    custom_fixes = {
        "ā": "a", "ī": "i", "ū": "u", "ṛ": "ri", "ñ": "n", "ḍ": "d", "ṭ": "t",
        "ṅ": "n", "ḥ": "h", "ś": "sh", "ṣ": "sh",
        "Ā": "A", "Ī": "I", "Ū": "U", "Ṛ": "Ri", "Ñ": "N", "Ḍ": "D", "Ṭ": "T"
    }
    for broken, fixed in custom_fixes.items():
        text = text.replace(broken, fixed)

    text = unicodedata.normalize('NFD', text)
    text = "".join([c for c in text if not unicodedata.combining(c)])
    text = re.sub(r'[\u0900-\u097f\u0a80-\u0aff]+', '', text)

    return " ".join(text.split())


def fetch_vachanamrut(vachno):
    """Fetches textual elements and formats them with structured prefixes."""
    url = f"https://www.anirdesh.com/vachanamrut/index.php?format=en&vachno={vachno}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, "html.parser", from_encoding="utf-8")
        content_div = soup.find('div', id='content')
        if not content_div:
            return None

        vach_data = []

        assigned_title = VACHANAMRUT_INDEX.get(vachno, f"Vachanamrut {vachno}")
        vach_data.append(f"HEADER::{assigned_title}")

        elements = content_div.find_all(['p', 'blockquote', 'li'])
        for elem in elements:
            if elem.find('p', recursive=False):
                continue

            text_raw = elem.get_text().strip()
            if not text_raw:
                continue

            if any(x in text_raw.lower() for x in ["menu", "side by side", "audio", "share", "text_increase", "text_decrease", "en \u25a0", "tr \u25a0"]):
                continue
            if "vachanamrut took place" in text_raw.lower() or "took place ... ago" in text_raw.lower():
                continue

            parent_classes = elem.get('class', []) + [c for parent in elem.parents for c in parent.get('class', []) if parent.get('class')]
            if any(cls in parent_classes for cls in ['vach_translit', 'vach_gujarati', 'vach_nav']):
                if elem.name != 'blockquote':
                    continue

            cleaned_text = clean_and_strip_devnagari(text_raw)
            if not cleaned_text:
                continue

            if elem.name == 'blockquote':
                vach_data.append(f"SHLOKA::{cleaned_text}")
            elif elem.name == 'li' or text_raw.startswith(tuple(str(x) for x in range(1, 20))) or "FOOTNOTES" in text_raw:
                vach_data.append(f"FOOTNOTE::{cleaned_text}")
            else:
                if len(cleaned_text) <= 1 and not cleaned_text.isalnum():
                    continue
                vach_data.append(f"BODY::{cleaned_text}")

        # Deduplicate identical adjacent elements
        final_clean_blocks = []
        for item in vach_data:
            if not final_clean_blocks or item != final_clean_blocks[-1]:
                final_clean_blocks.append(item)

        return final_clean_blocks
    except Exception as e:
        print(f"[-] Error parsing entry index {vachno}: {e}")
        return None


def run_scraper(generate_pdf=False):
    """
    Scrapes all Vachanamrut entries and saves structured JSON data to RAW_DATA_DIR.
    Optionally outputs PDF file as well.
    """
    # Ensure directory exists before saving files
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = RAW_DATA_DIR / "vachanamrut_raw.json"
    pdf_path = RAW_DATA_DIR / "Vachanamrut_English_Final_Clean.pdf"

    print(f"[+] Starting Scraper. Targets:\n    - JSON: {json_path}")
    if generate_pdf:
        print(f"    - PDF:  {pdf_path}")

    all_chapters = []
    total_chapters = 274

    for i in range(1, total_chapters + 1):
        print(f"[+] Scraping Chapter {i}/{total_chapters}...")
        parsed_blocks = fetch_vachanamrut(i)

        if not parsed_blocks:
            continue

        chapter_data = {
            "chapter_id": i,
            "title": VACHANAMRUT_INDEX.get(i, f"Vachanamrut {i}"),
            "blocks": parsed_blocks
        }
        all_chapters.append(chapter_data)
        time.sleep(0.02)

    # Save to JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_chapters, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved {len(all_chapters)} raw chapters to {json_path}")

    # Build PDF if requested
    if generate_pdf:
        print("[+] Building optional PDF document...")
        doc = SimpleDocTemplate(
            str(pdf_path), pagesize=letter,
            rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=28, leading=34, alignment=TA_CENTER, spaceAfter=20)
        vach_heading_style = ParagraphStyle('VachHeading', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=13, leading=17, spaceBefore=18, spaceAfter=12, keepWithNext=True)
        body_style = ParagraphStyle('VachBody', parent=styles['BodyText'], fontName='Helvetica', fontSize=10.5, leading=16, alignment=TA_JUSTIFY, spaceAfter=8)
        shloka_style = ParagraphStyle('VachShloka', parent=styles['BodyText'], fontName='Helvetica-Oblique', fontSize=10, leading=15, leftIndent=25, rightIndent=25, spaceBefore=6, spaceAfter=6)
        footnote_style = ParagraphStyle('VachFoot', parent=styles['BodyText'], fontName='Helvetica', fontSize=9, leading=13, alignment=TA_JUSTIFY, spaceAfter=4)

        story = [Spacer(1, 180), Paragraph("<b>VACHANAMRUT</b>", title_style), PageBreak()]

        for ch in all_chapters:
            for block in ch["blocks"]:
                prefix, text = block.split("::", 1)
                safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                if prefix == "HEADER":
                    story.append(Paragraph(f"<b>{safe_text}</b>", vach_heading_style))
                elif prefix == "SHLOKA":
                    story.append(Paragraph(f"<i>\"{safe_text}\"</i>", shloka_style))
                elif prefix == "FOOTNOTE":
                    story.append(Paragraph(safe_text, footnote_style))
                else:
                    story.append(Paragraph(safe_text, body_style))
            story.append(PageBreak())

        doc.build(story)
        print(f"[+] PDF successfully created at {pdf_path}")


if __name__ == "__main__":
    run_scraper(generate_pdf=False)