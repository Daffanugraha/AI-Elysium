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
from .constants import REPORT_CATEGORIES

# Inisialisasi NLTK (hanya sekali)
try:
    stop_words = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    stop_words = set(stopwords.words("english"))

@st.cache_resource
def load_semantic_model():
    """Memuat model Sentence Transformer dan menghitung embedding hanya dari 6 nama kategori."""
    model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    
    # Menghitung embedding hanya dari 6 nama kategori (Vektor Ringkas)
    category_embeddings = model.encode(REPORT_CATEGORIES, convert_to_tensor=True)
    
    return model, category_embeddings

MODEL, CATEGORY_EMBEDDINGS = load_semantic_model()


# --- FUNGSI BARU UNTUK MENGEKSTRAK ALASAN (KEY TOKENS) ---
@st.cache_data
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

def classify_report_category(review_text):
    """Mengklasifikasikan teks review ke salah satu kategori report dan mengembalikan alasannya."""
    if not review_text or len(review_text.strip()) < 3:
        # Mengembalikan 3 nilai: Kategori, Skor, Alasan
        return "Off topic", 100.0, "Input teks terlalu singkat atau kosong."

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