# utils/helpers.py

import streamlit as st
import time
import re
import emoji
import nltk
import torch # Diperlukan untuk manipulasi tensor (word embeddings)
from nltk.corpus import stopwords
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer, util
from .constants import REPORT_CATEGORIES, CATEGORY_DEFINITIONS

# Inisialisasi NLTK (hanya sekali)
try:
    stop_words = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    stop_words = set(stopwords.words("english"))

@st.cache_resource
def load_semantic_model():
    """Memuat model Sentence Transformer dan menghitung embedding hanya dari 6 nama kategori."""
    model = SentenceTransformer("intfloat/multilingual-e5-small")
    
    # Menghitung embedding hanya dari 6 nama kategori (Vektor Ringkas)
    category_embeddings = model.encode(REPORT_CATEGORIES, convert_to_tensor=True)
    
    return model, category_embeddings

MODEL, CATEGORY_EMBEDDINGS = load_semantic_model()

 
# --- FUNGSI BARU UNTUK MENGEKSTRAK ALASAN (KEY TOKENS) ---
# @st.cache_data
def extract_key_tokens(text, target_category, n_tokens=4):
    """
    Mengekstrak N token kunci dari teks yang paling berkontribusi pada kesamaan dengan kategori target.
    Ini bekerja dengan membandingkan embedding setiap token dengan embedding kategori target.
    """
    if not text:
        return "Teks kosong."

    # 1. Tokenisasi dan Embed Setiap Kata
    # Lakukan pembersihan teks dasar sebelum tokenisasi
    cleaned_text = re.sub(r"[^a-z0-9\s]", "", text.lower())
    words = [w for w in cleaned_text.split() if w not in stop_words and w]

    if not words:
        return "Kata kunci dibersihkan atau terlalu singkat."

    # Embed setiap kata
    # Model ini menerima list of strings dan mengembalikan tensor (Jumlah Kata) x (Dimensi Embedding)
    try:
        word_embeddings = MODEL.encode(words, convert_to_tensor=True)
    except Exception:
        return "Error saat menghitung embedding kata."

    # 2. Cari Embedding Kategori Target
    try:
        category_index = REPORT_CATEGORIES.index(target_category)
    except ValueError:
        return "Kategori tidak ditemukan."
        
    category_embedding = CATEGORY_EMBEDDINGS[category_index]

    # 3. Hitung Kesamaan Kosinus antara Setiap Kata dan Kategori
    # category_embedding perlu di-transpose untuk perkalian matriks (1D ke 2D/kolom)
    # Hasil: (Jumlah Kata) x 1
    word_scores = torch.matmul(word_embeddings, category_embedding.T) 
    
    # 4. Ambil Top N kata
    # Ambil indeks dengan skor tertinggi
    top_indices = torch.topk(word_scores.flatten(), k=min(n_tokens, len(words))).indices
    
    # Ambil kata-kata dari indeks tersebut
    key_tokens = [words[i.item()] for i in top_indices]
    
    return ", ".join(key_tokens)
# --------------------------------------------------------

# @st.cache_data
def get_validation_details(review_text: str, category_ai: str, score: float, key_tokens_str: str) -> dict:
    """
    Finds the specific policy reason from CATEGORY_DEFINITIONS and extracts the contextual sentence.
    
    Args:
        review_text: The complete review text.
        category_ai: The category predicted by the AI (e.g., "Profanity").
        score: The confidence score (0-100).
        key_tokens_str: The comma-separated string of trigger keywords (from extract_key_tokens).

    Returns:
        Dict with 'PolicyReason', 'ContextSentence', and 'KeyConcepts' (str).
    """
    # Convert token string to list
    key_tokens = [token.strip() for token in key_tokens_str.split(',') if token.strip()]

    result = {
        "PolicyReason": f"AI Classification: {category_ai}. No specific policy definition matched.",
        "ContextSentence": review_text if review_text else "*Empty Review*",
        "KeyConcepts": key_tokens_str
    }

    # 1. HANDLE 100% OFF TOPIC (No Text/Short Review)
    if category_ai == "Off topic" and score == 100.0:
        result['PolicyReason'] = "**Input text is missing or too short (No Text/Short Review).**"
        result['ContextSentence'] = "*The classification is based on the absence of substantive content.*"
        result['KeyConcepts'] = "N/A"
        return result
    
    # Check for general errors/empty inputs
    if not review_text or not key_tokens or category_ai not in CATEGORY_DEFINITIONS:
        return result

    # 2. Find the Most Relevant Contextual Sentence
    # Combine all trigger tokens into a regex pattern (case-insensitive, bounded)
    token_pattern = "|".join(r"\b" + re.escape(token) + r"\b" for token in key_tokens)
    
    # Split the review into sentences
    sentences = re.split(r'(?<=[.!?])\s+', review_text) 
    
    context_sentence = ""
    for sentence in sentences:
        if re.search(token_pattern, sentence, re.IGNORECASE):
            # Highlight the keywords in the contextual sentence
            context_sentence = re.sub(
                r'(' + token_pattern + r')', 
                r'**\1**', 
                sentence, 
                flags=re.IGNORECASE
            )
            break
            
    if context_sentence:
        result['ContextSentence'] = context_sentence
    else:
        # If no sentence is found, use the full text and highlight tokens
        result['ContextSentence'] = re.sub(
            r'(' + token_pattern + r')', 
            r'**\1**', 
            review_text, 
            flags=re.IGNORECASE
        )
        
    # 3. Find the Most Relevant Policy Definition using Semantic Similarity
    
    definitions = CATEGORY_DEFINITIONS[category_ai]
    definition_embeddings = MODEL.encode(definitions, convert_to_tensor=True)
    query_embedding = MODEL.encode(review_text, convert_to_tensor=True)

    # Calculate cosine similarity
    sim_scores = util.cos_sim(query_embedding, definition_embeddings).flatten()
    
    best_def_idx = sim_scores.argmax().item()
    best_definition = definitions[best_def_idx]
    
    # Construct the policy reason
    result['PolicyReason'] = (
        f"Violates definition: **'{best_definition}'**."
    )
    
    return result

def classify_report_category(review_text):
    """Mengklasifikasikan teks review ke salah satu kategori report dan mengembalikan alasannya."""
    if not review_text or len(review_text.strip()) < 3:
        # Mengembalikan 3 nilai: Kategori, Skor, Alasan
        return "Off topic", 100.0, "comments are too short or there are no comments."

    text_embedding = MODEL.encode(review_text, convert_to_tensor=True)
    # Gunakan util.cos_sim untuk menghitung kesamaan
    cosine_scores = util.cos_sim(text_embedding, CATEGORY_EMBEDDINGS)
    best_idx = cosine_scores.argmax().item()
    best_score = cosine_scores[0][best_idx].item()
    
    predicted_category = REPORT_CATEGORIES[best_idx]
    
    # --- Tambahkan Alasan ---
    # Panggil fungsi baru untuk mendapatkan kata-kata kunci
    reason_tokens = extract_key_tokens(review_text, predicted_category, n_tokens=4)

    # FUNGSI KINI MENGEMBALIKAN 3 NILAI: Kategori, Skor, Alasan (Tokens)
    return predicted_category, round(best_score * 100, 2), reason_tokens 


def clean_review_text_en(text):
# ... (Fungsi ini tetap sama) ...
    if not text:
        return ""
    text = emoji.replace_emoji(text, replace="")
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    # Pertahankan karakter alfanumerik, spasi, koma, titik, tanda tanya, tanda seru, dan apostrof.
    text = re.sub(r"[^a-z0-9\s.,!?']", " ", text)
    words = text.split()
    filtered_words = [w for w in words if w not in stop_words]
    return " ".join(filtered_words).strip()

def parse_relative_date(text):
# ... (Fungsi ini tetap sama) ...
    text = (text or "").lower().strip()
    now = datetime.now()
    patterns = [
        (r"(\d+)\s+day", "days"),
        (r"(\d+)\s+week", "weeks"),
        (r"(\d+)\s+month", "months"),
        (r"(\d+)\s+year", "years"),
    ]
    for pattern, unit in patterns:
        match = re.search(pattern, text)
        if match:
            num = int(match.group(1))
            if unit == "days":
                return (now - timedelta(days=num)).strftime("%Y-%m-%d")
            elif unit == "weeks":
                return (now - timedelta(weeks=num)).strftime("%Y-%m-%d")
            elif unit == "months":
                # Perkiraan 30 hari per bulan
                return (now - timedelta(days=30 * num)).strftime("%Y-%m-%d")
            elif unit == "years":
                # Perkiraan 365 hari per tahun
                return (now - timedelta(days=365 * num)).strftime("%Y-%m-%d")
    try:
        # Coba parse sebagai "Month Year"
        return datetime.strptime(text, "%B %Y").strftime("%Y-%m-%d")
    except Exception:
        return text # Kembalikan teks asli jika gagal diparse
    
# --- Helper Kunci Permanen ---
def generate_review_key(row):
# ... (Fungsi ini tetap sama) ...
    """Membuat kunci unik berdasarkan data ulasan (Composite Key)."""
    place_key = row.get("Place", "UNKNOWN").replace(' ', '').lower()
    user_key = row.get("User", "UNKNOWN").replace(' ', '').lower()
    date_key = row.get("Date (Parsed)", "UNKNOWN").replace('-', '')
    
    # Gunakan 50 karakter pertama teks ulasan (yang sudah dibersihkan dari non-alphanumeric)
    text_snippet = re.sub(r'[^a-z0-9]', '', row.get("Review Text", "no_text")[:50].lower())
    
    # Gabungkan semua komponen menjadi satu string unik
    key = f"{place_key}_{user_key}_{date_key}_{text_snippet}"
    return key