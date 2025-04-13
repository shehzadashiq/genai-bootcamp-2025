import os
import sys
import django
import json
import boto3
from langchain_community.embeddings import BedrockEmbeddings
from django.db import transaction

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lang_portal_backend.settings')
django.setup()

from api.sentence_builder_models import WordCategory, SentenceWord, SentencePattern
import chromadb

# Setup ChromaDB for sentence embeddings
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'chroma_db', 'sentence_builder')
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Initialize Bedrock client for embeddings
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

# Initialize Bedrock embeddings
embeddings = BedrockEmbeddings(
    client=bedrock_runtime,
    model_id="amazon.titan-embed-text-v1"
)

# Initialize ChromaDB client
chroma_client = chromadb.Client(chromadb.Settings(
    persist_directory=CHROMA_PERSIST_DIR,
    chroma_db_impl="duckdb+parquet",
))

# Create or get the collection
try:
    sentence_collection = chroma_client.get_collection("sentence_patterns")
except:
    sentence_collection = chroma_client.create_collection(
        name="sentence_patterns",
        metadata={"hnsw:space": "cosine"}
    )

def seed_word_categories():
    """Seed word categories (parts of speech)"""
    categories = [
        {"name": "Subject", "description": "The person or thing performing the action"},
        {"name": "Verb", "description": "The action or state of being"},
        {"name": "Object", "description": "The person or thing receiving the action"},
        {"name": "Adjective", "description": "Describes or modifies a noun"},
        {"name": "Adverb", "description": "Modifies a verb, adjective, or another adverb"},
        {"name": "Preposition", "description": "Shows relationship between words"},
        {"name": "Conjunction", "description": "Connects words, phrases, or clauses"},
        {"name": "Interjection", "description": "Expresses emotion"}
    ]
    
    for category_data in categories:
        WordCategory.objects.get_or_create(
            name=category_data["name"],
            defaults={"description": category_data["description"]}
        )
    
    print(f"Seeded {len(categories)} word categories")

def seed_words():
    """Seed words with their categories"""
    # Get categories
    subject_category = WordCategory.objects.get(name="Subject")
    verb_category = WordCategory.objects.get(name="Verb")
    object_category = WordCategory.objects.get(name="Object")
    adjective_category = WordCategory.objects.get(name="Adjective")
    adverb_category = WordCategory.objects.get(name="Adverb")
    preposition_category = WordCategory.objects.get(name="Preposition")
    conjunction_category = WordCategory.objects.get(name="Conjunction")
    interjection_category = WordCategory.objects.get(name="Interjection")
    
    # Sample words - split into batches for better performance
    word_batches = [
        # Batch 1: Subjects (40 words)
        [
            {"urdu_word": "میں", "roman_urdu": "main", "english_translation": "I", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "تم", "roman_urdu": "tum", "english_translation": "you", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "وہ", "roman_urdu": "woh", "english_translation": "he/she", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "ہم", "roman_urdu": "hum", "english_translation": "we", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "آپ", "roman_urdu": "aap", "english_translation": "you (formal)", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "یہ", "roman_urdu": "yeh", "english_translation": "this", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "وہ لوگ", "roman_urdu": "woh log", "english_translation": "they", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "لڑکا", "roman_urdu": "larka", "english_translation": "boy", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "لڑکی", "roman_urdu": "larki", "english_translation": "girl", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "بچہ", "roman_urdu": "bacha", "english_translation": "child", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "آدمی", "roman_urdu": "aadmi", "english_translation": "man", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "عورت", "roman_urdu": "aurat", "english_translation": "woman", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "استاد", "roman_urdu": "ustad", "english_translation": "teacher", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "طالب علم", "roman_urdu": "talib ilm", "english_translation": "student", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "دوست", "roman_urdu": "dost", "english_translation": "friend", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "خاندان", "roman_urdu": "khaandan", "english_translation": "family", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "والد", "roman_urdu": "walid", "english_translation": "father", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "والدہ", "roman_urdu": "walida", "english_translation": "mother", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "بھائی", "roman_urdu": "bhai", "english_translation": "brother", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "بہن", "roman_urdu": "behan", "english_translation": "sister", "category": subject_category, "difficulty_level": 1},
        ],
        # Batch 2: More Subjects
        [
            {"urdu_word": "بیٹا", "roman_urdu": "beta", "english_translation": "son", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "بیٹی", "roman_urdu": "beti", "english_translation": "daughter", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "دادا", "roman_urdu": "dada", "english_translation": "grandfather", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "دادی", "roman_urdu": "dadi", "english_translation": "grandmother", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "چاچا", "roman_urdu": "chacha", "english_translation": "uncle", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "چاچی", "roman_urdu": "chachi", "english_translation": "aunt", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "ڈاکٹر", "roman_urdu": "doctor", "english_translation": "doctor", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "انجینئر", "roman_urdu": "engineer", "english_translation": "engineer", "category": subject_category, "difficulty_level": 2},
            {"urdu_word": "کسان", "roman_urdu": "kisaan", "english_translation": "farmer", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "مزدور", "roman_urdu": "mazdoor", "english_translation": "laborer", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "تاجر", "roman_urdu": "tajir", "english_translation": "businessman", "category": subject_category, "difficulty_level": 2},
            {"urdu_word": "صحافی", "roman_urdu": "sahafi", "english_translation": "journalist", "category": subject_category, "difficulty_level": 2},
            {"urdu_word": "فنکار", "roman_urdu": "fankar", "english_translation": "artist", "category": subject_category, "difficulty_level": 2},
            {"urdu_word": "سیاستدان", "roman_urdu": "siyasatdan", "english_translation": "politician", "category": subject_category, "difficulty_level": 2},
            {"urdu_word": "کھلاڑی", "roman_urdu": "khilari", "english_translation": "player", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "مصنف", "roman_urdu": "musannif", "english_translation": "author", "category": subject_category, "difficulty_level": 2},
            {"urdu_word": "شاعر", "roman_urdu": "shair", "english_translation": "poet", "category": subject_category, "difficulty_level": 2},
            {"urdu_word": "موسیقار", "roman_urdu": "mosiqar", "english_translation": "musician", "category": subject_category, "difficulty_level": 2},
            {"urdu_word": "مہمان", "roman_urdu": "mehman", "english_translation": "guest", "category": subject_category, "difficulty_level": 1},
            {"urdu_word": "پڑوسی", "roman_urdu": "parosi", "english_translation": "neighbor", "category": subject_category, "difficulty_level": 1},
        ],
        # Batch 3: Verbs (20 words)
        [
            {"urdu_word": "کھاتا/کھاتی ہے", "roman_urdu": "khata/khati hai", "english_translation": "eats", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "پیتا/پیتی ہے", "roman_urdu": "peeta/peeti hai", "english_translation": "drinks", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "جاتا/جاتی ہے", "roman_urdu": "jata/jati hai", "english_translation": "goes", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "آتا/آتی ہے", "roman_urdu": "aata/aati hai", "english_translation": "comes", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "سوتا/سوتی ہے", "roman_urdu": "sota/soti hai", "english_translation": "sleeps", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "بولتا/بولتی ہے", "roman_urdu": "bolta/bolti hai", "english_translation": "speaks", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "سنتا/سنتی ہے", "roman_urdu": "sunta/sunti hai", "english_translation": "listens", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "دیکھتا/دیکھتی ہے", "roman_urdu": "dekhta/dekhti hai", "english_translation": "sees", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "پڑھتا/پڑھتی ہے", "roman_urdu": "parhta/parhti hai", "english_translation": "reads", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "لکھتا/لکھتی ہے", "roman_urdu": "likhta/likhti hai", "english_translation": "writes", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "کرتا/کرتی ہے", "roman_urdu": "karta/karti hai", "english_translation": "does", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "دیتا/دیتی ہے", "roman_urdu": "deta/deti hai", "english_translation": "gives", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "لیتا/لیتی ہے", "roman_urdu": "leta/leti hai", "english_translation": "takes", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "بناتا/بناتی ہے", "roman_urdu": "banata/banati hai", "english_translation": "makes", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "رکھتا/رکھتی ہے", "roman_urdu": "rakhta/rakhti hai", "english_translation": "keeps", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "چلتا/چلتی ہے", "roman_urdu": "chalta/chalti hai", "english_translation": "walks", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "دوڑتا/دوڑتی ہے", "roman_urdu": "dorta/dorti hai", "english_translation": "runs", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "اڑتا/اڑتی ہے", "roman_urdu": "urta/urti hai", "english_translation": "flies", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "تیرتا/تیرتی ہے", "roman_urdu": "tairta/tairti hai", "english_translation": "swims", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "کھیلتا/کھیلتی ہے", "roman_urdu": "khelta/khelti hai", "english_translation": "plays", "category": verb_category, "difficulty_level": 1},
        ],
        # Batch 4: More Verbs (20 words)
        [
            {"urdu_word": "ہنستا/ہنستی ہے", "roman_urdu": "hansta/hansti hai", "english_translation": "laughs", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "روتا/روتی ہے", "roman_urdu": "rota/roti hai", "english_translation": "cries", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "گاتا/گاتی ہے", "roman_urdu": "gata/gati hai", "english_translation": "sings", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "بجاتا/بجاتی ہے", "roman_urdu": "bajata/bajati hai", "english_translation": "plays (instrument)", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "ناچتا/ناچتی ہے", "roman_urdu": "nachta/nachti hai", "english_translation": "dances", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "سمجھتا/سمجھتی ہے", "roman_urdu": "samajhta/samajhti hai", "english_translation": "understands", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "سیکھتا/سیکھتی ہے", "roman_urdu": "seekhta/seekhti hai", "english_translation": "learns", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "سکھاتا/سکھاتی ہے", "roman_urdu": "sikhata/sikhati hai", "english_translation": "teaches", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "خریدتا/خریدتی ہے", "roman_urdu": "kharidta/kharidti hai", "english_translation": "buys", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "بیچتا/بیچتی ہے", "roman_urdu": "bechta/bechti hai", "english_translation": "sells", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "کھولتا/کھولتی ہے", "roman_urdu": "kholta/kholti hai", "english_translation": "opens", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "بند کرتا/کرتی ہے", "roman_urdu": "band karta/karti hai", "english_translation": "closes", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "شروع کرتا/کرتی ہے", "roman_urdu": "shuru karta/karti hai", "english_translation": "starts", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "ختم کرتا/کرتی ہے", "roman_urdu": "khatam karta/karti hai", "english_translation": "finishes", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "انتظار کرتا/کرتی ہے", "roman_urdu": "intezar karta/karti hai", "english_translation": "waits", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "ملتا/ملتی ہے", "roman_urdu": "milta/milti hai", "english_translation": "meets", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "بھیجتا/بھیجتی ہے", "roman_urdu": "bhejta/bhejti hai", "english_translation": "sends", "category": verb_category, "difficulty_level": 1},
            {"urdu_word": "حاصل کرتا/کرتی ہے", "roman_urdu": "hasil karta/karti hai", "english_translation": "obtains", "category": verb_category, "difficulty_level": 2},
            {"urdu_word": "استعمال کرتا/کرتی ہے", "roman_urdu": "istemal karta/karti hai", "english_translation": "uses", "category": verb_category, "difficulty_level": 2},
            {"urdu_word": "پسند کرتا/کرتی ہے", "roman_urdu": "pasand karta/karti hai", "english_translation": "likes", "category": verb_category, "difficulty_level": 1},
        ],
        # Batch 5: Objects (20 words)
        [
            {"urdu_word": "کھانا", "roman_urdu": "khana", "english_translation": "food", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "پانی", "roman_urdu": "pani", "english_translation": "water", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "چائے", "roman_urdu": "chai", "english_translation": "tea", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "کافی", "roman_urdu": "coffee", "english_translation": "coffee", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "دودھ", "roman_urdu": "doodh", "english_translation": "milk", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "پھل", "roman_urdu": "phal", "english_translation": "fruit", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "سبزی", "roman_urdu": "sabzi", "english_translation": "vegetable", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "گوشت", "roman_urdu": "gosht", "english_translation": "meat", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "روٹی", "roman_urdu": "roti", "english_translation": "bread", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "چاول", "roman_urdu": "chawal", "english_translation": "rice", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "کتاب", "roman_urdu": "kitab", "english_translation": "book", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "قلم", "roman_urdu": "qalam", "english_translation": "pen", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "کاغذ", "roman_urdu": "kaghaz", "english_translation": "paper", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "میز", "roman_urdu": "mez", "english_translation": "table", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "کرسی", "roman_urdu": "kursi", "english_translation": "chair", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "بستر", "roman_urdu": "bistar", "english_translation": "bed", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "کمرہ", "roman_urdu": "kamra", "english_translation": "room", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "گھر", "roman_urdu": "ghar", "english_translation": "house", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "دروازہ", "roman_urdu": "darwaza", "english_translation": "door", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "کھڑکی", "roman_urdu": "khirki", "english_translation": "window", "category": object_category, "difficulty_level": 1},
        ],
        # Batch 6: More Objects (20 words)
        [
            {"urdu_word": "گاڑی", "roman_urdu": "gari", "english_translation": "car", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "بس", "roman_urdu": "bus", "english_translation": "bus", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "ٹرین", "roman_urdu": "train", "english_translation": "train", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "ہوائی جہاز", "roman_urdu": "hawai jahaz", "english_translation": "airplane", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "سڑک", "roman_urdu": "sarak", "english_translation": "road", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "دکان", "roman_urdu": "dukan", "english_translation": "shop", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "بازار", "roman_urdu": "bazar", "english_translation": "market", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "اسکول", "roman_urdu": "school", "english_translation": "school", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "یونیورسٹی", "roman_urdu": "university", "english_translation": "university", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "ہسپتال", "roman_urdu": "hospital", "english_translation": "hospital", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "موبائل فون", "roman_urdu": "mobile phone", "english_translation": "mobile phone", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "کمپیوٹر", "roman_urdu": "computer", "english_translation": "computer", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "ٹیلی ویژن", "roman_urdu": "television", "english_translation": "television", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "ریڈیو", "roman_urdu": "radio", "english_translation": "radio", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "انٹرنیٹ", "roman_urdu": "internet", "english_translation": "internet", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "پیسہ", "roman_urdu": "paisa", "english_translation": "money", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "وقت", "roman_urdu": "waqt", "english_translation": "time", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "دن", "roman_urdu": "din", "english_translation": "day", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "رات", "roman_urdu": "raat", "english_translation": "night", "category": object_category, "difficulty_level": 1},
            {"urdu_word": "ہفتہ", "roman_urdu": "hafta", "english_translation": "week", "category": object_category, "difficulty_level": 1},
        ],
        # Batch 7: Adjectives (20 words)
        [
            {"urdu_word": "اچھا", "roman_urdu": "acha", "english_translation": "good", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "برا", "roman_urdu": "bura", "english_translation": "bad", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "بڑا", "roman_urdu": "bara", "english_translation": "big", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "چھوٹا", "roman_urdu": "chota", "english_translation": "small", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "لمبا", "roman_urdu": "lamba", "english_translation": "tall", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "مختصر", "roman_urdu": "mukhtasar", "english_translation": "short", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "موٹا", "roman_urdu": "mota", "english_translation": "fat", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "پتلا", "roman_urdu": "patla", "english_translation": "thin", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "نیا", "roman_urdu": "naya", "english_translation": "new", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "پرانا", "roman_urdu": "purana", "english_translation": "old", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "گرم", "roman_urdu": "garam", "english_translation": "hot", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "ٹھنڈا", "roman_urdu": "thanda", "english_translation": "cold", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "خوبصورت", "roman_urdu": "khubsurat", "english_translation": "beautiful", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "بدصورت", "roman_urdu": "badsurat", "english_translation": "ugly", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "تیز", "roman_urdu": "tez", "english_translation": "fast", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "سست", "roman_urdu": "sust", "english_translation": "slow", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "مشکل", "roman_urdu": "mushkil", "english_translation": "difficult", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "آسان", "roman_urdu": "aasan", "english_translation": "easy", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "سخت", "roman_urdu": "sakht", "english_translation": "hard", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "نرم", "roman_urdu": "naram", "english_translation": "soft", "category": adjective_category, "difficulty_level": 1},
        ],
        # Batch 8: More Adjectives (20 words)
        [
            {"urdu_word": "صاف", "roman_urdu": "saaf", "english_translation": "clean", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "گندا", "roman_urdu": "ganda", "english_translation": "dirty", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "خوش", "roman_urdu": "khush", "english_translation": "happy", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "غمگین", "roman_urdu": "ghamgeen", "english_translation": "sad", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "غصہ", "roman_urdu": "gussa", "english_translation": "angry", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "پرسکون", "roman_urdu": "pursukoon", "english_translation": "calm", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "بھوکا", "roman_urdu": "bhooka", "english_translation": "hungry", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "پیاسا", "roman_urdu": "pyasa", "english_translation": "thirsty", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "تھکا ہوا", "roman_urdu": "thaka hua", "english_translation": "tired", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "تازہ دم", "roman_urdu": "taza dam", "english_translation": "fresh", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "امیر", "roman_urdu": "ameer", "english_translation": "rich", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "غریب", "roman_urdu": "ghareeb", "english_translation": "poor", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "ہوشیار", "roman_urdu": "hoshiyar", "english_translation": "intelligent", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "بیوقوف", "roman_urdu": "bewakoof", "english_translation": "stupid", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "مضبوط", "roman_urdu": "mazboot", "english_translation": "strong", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "کمزور", "roman_urdu": "kamzor", "english_translation": "weak", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "صحت مند", "roman_urdu": "sehat mand", "english_translation": "healthy", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "بیمار", "roman_urdu": "beemar", "english_translation": "sick", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "زندہ", "roman_urdu": "zinda", "english_translation": "alive", "category": adjective_category, "difficulty_level": 1},
            {"urdu_word": "مردہ", "roman_urdu": "murda", "english_translation": "dead", "category": adjective_category, "difficulty_level": 1},
        ],
        # Batch 9: Adverbs (15 words)
        [
            {"urdu_word": "جلدی", "roman_urdu": "jaldi", "english_translation": "quickly", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "آہستہ", "roman_urdu": "ahista", "english_translation": "slowly", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "اچھی طرح", "roman_urdu": "achi tarah", "english_translation": "well", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "بری طرح", "roman_urdu": "buri tarah", "english_translation": "badly", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "بہت", "roman_urdu": "bohat", "english_translation": "very", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "تھوڑا", "roman_urdu": "thora", "english_translation": "a little", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "زیادہ", "roman_urdu": "zyada", "english_translation": "more", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "کم", "roman_urdu": "kam", "english_translation": "less", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "ہمیشہ", "roman_urdu": "hamesha", "english_translation": "always", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "کبھی", "roman_urdu": "kabhi", "english_translation": "sometimes", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "کبھی نہیں", "roman_urdu": "kabhi nahi", "english_translation": "never", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "اکثر", "roman_urdu": "aksar", "english_translation": "often", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "شاید", "roman_urdu": "shayad", "english_translation": "perhaps", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "یقیناً", "roman_urdu": "yaqeenan", "english_translation": "certainly", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "ابھی", "roman_urdu": "abhi", "english_translation": "now", "category": adverb_category, "difficulty_level": 1},
        ],
        # Batch 10: More Adverbs (15 words)
        [
            {"urdu_word": "پھر", "roman_urdu": "phir", "english_translation": "then", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "کل", "roman_urdu": "kal", "english_translation": "yesterday/tomorrow", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "آج", "roman_urdu": "aaj", "english_translation": "today", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "پرسوں", "roman_urdu": "parson", "english_translation": "day after tomorrow", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "یہاں", "roman_urdu": "yahan", "english_translation": "here", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "وہاں", "roman_urdu": "wahan", "english_translation": "there", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "اندر", "roman_urdu": "andar", "english_translation": "inside", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "باہر", "roman_urdu": "bahar", "english_translation": "outside", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "اوپر", "roman_urdu": "upar", "english_translation": "above", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "نیچے", "roman_urdu": "neeche", "english_translation": "below", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "آگے", "roman_urdu": "aage", "english_translation": "ahead", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "پیچھے", "roman_urdu": "peeche", "english_translation": "behind", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "دائیں", "roman_urdu": "dayen", "english_translation": "right", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "بائیں", "roman_urdu": "bayen", "english_translation": "left", "category": adverb_category, "difficulty_level": 1},
            {"urdu_word": "بالکل", "roman_urdu": "bilkul", "english_translation": "exactly", "category": adverb_category, "difficulty_level": 1},
        ],
        # Batch 11: Prepositions (20 words)
        [
            {"urdu_word": "میں", "roman_urdu": "mein", "english_translation": "in", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "پر", "roman_urdu": "par", "english_translation": "on", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے اندر", "roman_urdu": "ke andar", "english_translation": "inside", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے باہر", "roman_urdu": "ke bahar", "english_translation": "outside", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے اوپر", "roman_urdu": "ke upar", "english_translation": "above", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے نیچے", "roman_urdu": "ke neeche", "english_translation": "below", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے سامنے", "roman_urdu": "ke saamne", "english_translation": "in front of", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے پیچھے", "roman_urdu": "ke peeche", "english_translation": "behind", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے ساتھ", "roman_urdu": "ke saath", "english_translation": "with", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے بغیر", "roman_urdu": "ke baghair", "english_translation": "without", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے لیے", "roman_urdu": "ke liye", "english_translation": "for", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "سے", "roman_urdu": "se", "english_translation": "from", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "تک", "roman_urdu": "tak", "english_translation": "until", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے درمیان", "roman_urdu": "ke darmiyan", "english_translation": "between", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے قریب", "roman_urdu": "ke qareeb", "english_translation": "near", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے دور", "roman_urdu": "ke door", "english_translation": "far", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے بعد", "roman_urdu": "ke baad", "english_translation": "after", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے پہلے", "roman_urdu": "ke pehle", "english_translation": "before", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے بارے میں", "roman_urdu": "ke baare mein", "english_translation": "about", "category": preposition_category, "difficulty_level": 1},
            {"urdu_word": "کے ذریعے", "roman_urdu": "ke zariye", "english_translation": "through", "category": preposition_category, "difficulty_level": 1},
        ],
        # Batch 12: Conjunctions (15 words)
        [
            {"urdu_word": "اور", "roman_urdu": "aur", "english_translation": "and", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "یا", "roman_urdu": "ya", "english_translation": "or", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "لیکن", "roman_urdu": "lekin", "english_translation": "but", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "اگر", "roman_urdu": "agar", "english_translation": "if", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "تو", "roman_urdu": "to", "english_translation": "then", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "کیونکہ", "roman_urdu": "kyunke", "english_translation": "because", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "تاکہ", "roman_urdu": "taake", "english_translation": "so that", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "جب", "roman_urdu": "jab", "english_translation": "when", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "جب تک", "roman_urdu": "jab tak", "english_translation": "until", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "جیسے", "roman_urdu": "jaise", "english_translation": "as", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "کہ", "roman_urdu": "ke", "english_translation": "that", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "چونکہ", "roman_urdu": "chunke", "english_translation": "since", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "حالانکہ", "roman_urdu": "halanke", "english_translation": "although", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "بلکہ", "roman_urdu": "balke", "english_translation": "rather", "category": conjunction_category, "difficulty_level": 1},
            {"urdu_word": "نہ", "roman_urdu": "na", "english_translation": "neither/nor", "category": conjunction_category, "difficulty_level": 1},
        ],
        # Batch 13: Interjections (15 words)
        [
            {"urdu_word": "واہ", "roman_urdu": "wah", "english_translation": "wow", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "اوہو", "roman_urdu": "oho", "english_translation": "oh", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "ارے", "roman_urdu": "arey", "english_translation": "hey", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "ہائے", "roman_urdu": "haaye", "english_translation": "alas", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "افسوس", "roman_urdu": "afsos", "english_translation": "unfortunately", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "شاباش", "roman_urdu": "shabash", "english_translation": "bravo", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "واقعی", "roman_urdu": "waqai", "english_translation": "really", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "ہاں", "roman_urdu": "haan", "english_translation": "yes", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "نہیں", "roman_urdu": "nahi", "english_translation": "no", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "معاف کیجیے", "roman_urdu": "maaf kijiye", "english_translation": "excuse me", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "شکریہ", "roman_urdu": "shukriya", "english_translation": "thank you", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "خدا حافظ", "roman_urdu": "khuda hafiz", "english_translation": "goodbye", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "سلام", "roman_urdu": "salaam", "english_translation": "hello", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "بسم اللہ", "roman_urdu": "bismillah", "english_translation": "in the name of God", "category": interjection_category, "difficulty_level": 1},
            {"urdu_word": "ماشاءاللہ", "roman_urdu": "mashaAllah", "english_translation": "God has willed it", "category": interjection_category, "difficulty_level": 1},
        ],
    ]
    
    # Process batches with transaction handling for each batch
    total_words = 0
    for i, batch in enumerate(word_batches):
        try:
            with transaction.atomic():
                for word_data in batch:
                    SentenceWord.objects.get_or_create(
                        urdu_word=word_data["urdu_word"],
                        roman_urdu=word_data["roman_urdu"],
                        english_translation=word_data["english_translation"],
                        category=word_data["category"],
                        difficulty_level=word_data["difficulty_level"]
                    )
                total_words += len(batch)
                print(f"Seeded batch {i+1} with {len(batch)} words. Total words: {total_words}")
        except Exception as e:
            print(f"Error seeding batch {i+1}: {e}")
            # Continue with next batch even if this one fails
            continue
    
    print(f"Seeded {total_words} words")

def seed_sentence_patterns():
    """Seed sentence patterns and add to ChromaDB"""
    patterns = [
        # Basic patterns (already included)
        {
            "pattern": "subject verb",
            "description": "Simple sentence with subject and verb",
            "example": "میں جاتا/جاتی ہوں۔ (I go.)",
            "difficulty_level": 1
        },
        {
            "pattern": "subject verb",
            "description": "Simple sentence with subject and verb (without full stop)",
            "example": "میں جاتا/جاتی ہوں (I go)",
            "difficulty_level": 1
        },
        {
            "pattern": "subject object verb",
            "description": "Subject-Object-Verb order (common in Urdu)",
            "example": "میں کھانا کھاتا/کھاتی ہوں۔ (I food eat.)",
            "difficulty_level": 1
        },
        {
            "pattern": "subject object verb",
            "description": "Subject-Object-Verb order (without full stop)",
            "example": "میں کھانا کھاتا/کھاتی ہوں (I food eat)",
            "difficulty_level": 1
        },
        {
            "pattern": "subject adjective object verb",
            "description": "Subject with adjective describing the object",
            "example": "میں اچھا کھانا کھاتا/کھاتی ہوں۔ (I good food eat.)",
            "difficulty_level": 2
        },
        {
            "pattern": "subject adjective object verb",
            "description": "Subject with adjective describing the object (without full stop)",
            "example": "میں اچھا کھانا کھاتا/کھاتی ہوں (I good food eat)",
            "difficulty_level": 2
        },
        {
            "pattern": "subject adverb verb",
            "description": "Subject with adverb modifying the verb",
            "example": "میں تیزی سے جاتا/جاتی ہوں۔ (I quickly go.)",
            "difficulty_level": 2
        },
        {
            "pattern": "subject adverb verb",
            "description": "Subject with adverb modifying the verb (without full stop)",
            "example": "میں تیزی سے جاتا/جاتی ہوں (I quickly go)",
            "difficulty_level": 2
        },
        
        # Additional patterns from the comprehensive list
        # Present tense
        {
            "pattern": "subject object verb present",
            "description": "Subject-Object-Verb in present tense",
            "example": "وہ کتاب پڑھتا ہے۔ (He reads a book.)",
            "difficulty_level": 1
        },
        # Past tense
        {
            "pattern": "subject object verb past",
            "description": "Subject-Object-Verb in past tense",
            "example": "اُس نے کھانا کھایا۔ (He ate the food.)",
            "difficulty_level": 1
        },
        # Future tense
        {
            "pattern": "subject object verb future",
            "description": "Subject-Object-Verb in future tense",
            "example": "وہ اسکول جائے گا۔ (He will go to school.)",
            "difficulty_level": 2
        },
        # Present continuous
        {
            "pattern": "subject object continuous present",
            "description": "Subject-Object-Verb in present continuous",
            "example": "وہ کہانی سنا رہا ہے۔ (He is telling a story.)",
            "difficulty_level": 2
        },
        # Past continuous
        {
            "pattern": "subject object continuous past",
            "description": "Subject-Object-Verb in past continuous",
            "example": "وہ گانا گا رہا تھا۔ (He was singing a song.)",
            "difficulty_level": 2
        },
        # Future continuous
        {
            "pattern": "subject object continuous future",
            "description": "Subject-Object-Verb in future continuous",
            "example": "وہ کام کر رہا ہوگا۔ (He will be working.)",
            "difficulty_level": 3
        },
        # Present perfect
        {
            "pattern": "subject object perfect present",
            "description": "Subject-Object-Verb in present perfect",
            "example": "وہ کھانا کھا چکا ہے۔ (He has eaten the food.)",
            "difficulty_level": 3
        },
        # Past perfect
        {
            "pattern": "subject object perfect past",
            "description": "Subject-Object-Verb in past perfect",
            "example": "وہ خط لکھ چکا تھا۔ (He had written the letter.)",
            "difficulty_level": 3
        },
        # Future perfect
        {
            "pattern": "subject object perfect future",
            "description": "Subject-Object-Verb in future perfect",
            "example": "وہ کام مکمل کر چکا ہوگا۔ (He will have completed the task.)",
            "difficulty_level": 3
        },
        
        # Question forms
        # Yes/No questions
        {
            "pattern": "question subject object verb",
            "description": "Yes/No question with کیا",
            "example": "کیا وہ اسکول جاتا ہے؟ (Does he go to school?)",
            "difficulty_level": 2
        },
        # WH-questions
        {
            "pattern": "wh-word subject object verb",
            "description": "WH-question",
            "example": "تم کیا کھا رہے ہو؟ (What are you eating?)",
            "difficulty_level": 2
        },
        
        # Imperative forms
        {
            "pattern": "verb object",
            "description": "Imperative (command)",
            "example": "دروازہ بند کرو۔ (Close the door.)",
            "difficulty_level": 1
        },
        {
            "pattern": "negative verb object",
            "description": "Negative imperative",
            "example": "شور نہ مچاؤ۔ (Don't make noise.)",
            "difficulty_level": 2
        },
        
        # Compound sentences
        {
            "pattern": "subject verb conjunction subject verb",
            "description": "Compound sentence with conjunction",
            "example": "وہ کھیلتا ہے اور ہنستا ہے۔ (He plays and laughs.)",
            "difficulty_level": 3
        },
        {
            "pattern": "conditional clause result clause",
            "description": "Conditional sentence",
            "example": "اگر وہ آئے گا، تو ہم چلیں گے۔ (If he comes, then we will go.)",
            "difficulty_level": 3
        },
        
        # Advanced structures
        {
            "pattern": "object passive verb",
            "description": "Passive voice",
            "example": "خط لکھا گیا۔ (The letter was written.)",
            "difficulty_level": 3
        },
        {
            "pattern": "subject emphasis object verb",
            "description": "Sentence with emphasis",
            "example": "وہی آیا تھا۔ (He (and no one else) had come.)",
            "difficulty_level": 3
        },
        {
            "pattern": "subject object negative verb",
            "description": "Negative sentence",
            "example": "وہ سکول نہیں گیا۔ (He did not go to school.)",
            "difficulty_level": 2
        }
    ]
    
    # Clear existing embeddings in ChromaDB
    try:
        sentence_collection.delete(ids=[f"pattern_{i+1}" for i in range(len(patterns) * 2)])  # Account for more patterns
    except:
        pass
    
    # Add patterns to database and ChromaDB
    for pattern_data in patterns:
        pattern, created = SentencePattern.objects.get_or_create(
            pattern=pattern_data["pattern"],
            example=pattern_data["example"],  # Include example in uniqueness check
            defaults={
                "description": pattern_data["description"],
                "difficulty_level": pattern_data["difficulty_level"]
            }
        )
        
        # Add to ChromaDB - both with and without full stop versions
        pattern_text = f"{pattern.pattern} - {pattern.example if pattern.example else ''}"
        pattern_embedding = embeddings.embed_query(pattern_text)
        
        # Create a normalized version without full stop if it has one
        normalized_example = pattern.example
        if '۔' in normalized_example:
            normalized_example = normalized_example.replace('۔', '').strip()
        
        # Add the pattern to ChromaDB
        sentence_collection.add(
            ids=[f"pattern_{pattern.id}"],
            embeddings=[pattern_embedding],
            metadatas=[{
                "pattern_id": pattern.id,
                "pattern": pattern.pattern,
                "example": pattern.example,
                "difficulty_level": pattern.difficulty_level
            }],
            documents=[pattern_text]
        )
    
    print(f"Seeded {len(patterns)} sentence patterns")

if __name__ == "__main__":
    print("Starting to seed Sentence Builder data...")
    seed_word_categories()
    seed_words()
    seed_sentence_patterns()
    print("Finished seeding Sentence Builder data!")
