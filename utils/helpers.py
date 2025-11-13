# utils/helpers.py

import streamlit as st
import time
import re
import emoji
import nltk
from nltk.corpus import stopwords
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer, util
from .constants import REPORT_CATEGORIES

# Inisialisasi NLTK (hanya sekali)
try:
    stop_words = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    stop_words = set(stopwords.words("english"))

@st.cache_resource
def load_semantic_model():
    """Memuat model Sentence Transformer untuk klasifikasi report."""
    model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    category_embeddings = model.encode(REPORT_CATEGORIES, convert_to_tensor=True)
    return model, category_embeddings

MODEL, CATEGORY_EMBEDDINGS = load_semantic_model()

def classify_report_category(review_text):
    """Mengklasifikasikan teks review ke salah satu kategori report."""
    if not review_text or len(review_text.strip()) < 3:
        return "Spam", 100.0

    text_embedding = MODEL.encode(review_text, convert_to_tensor=True)
    # Gunakan util.cos_sim untuk menghitung kesamaan
    cosine_scores = util.cos_sim(text_embedding, CATEGORY_EMBEDDINGS)
    best_idx = cosine_scores.argmax().item()
    best_score = cosine_scores[0][best_idx].item()

    return REPORT_CATEGORIES[best_idx], round(best_score * 100, 2)

def clean_review_text_en(text):
    """Membersihkan teks review dari emoji, URL, dan stop words."""
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
    """Mengubah teks tanggal relatif menjadi format YYYY-MM-DD."""
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
    """Membuat kunci unik berdasarkan data ulasan (Composite Key)."""
    place_key = row.get("Place", "UNKNOWN").replace(' ', '').lower()
    user_key = row.get("User", "UNKNOWN").replace(' ', '').lower()
    date_key = row.get("Date (Parsed)", "UNKNOWN").replace('-', '')
    
    # Gunakan 50 karakter pertama teks ulasan (yang sudah dibersihkan dari non-alphanumeric)
    text_snippet = re.sub(r'[^a-z0-9]', '', row.get("Review Text", "no_text")[:50].lower())
    
    # Gabungkan semua komponen menjadi satu string unik
    key = f"{place_key}_{user_key}_{date_key}_{text_snippet}"
    return key