# utils/constants.py

import os
import json

# --- Konfigurasi File & Direktori ---
COOKIES_DIR = "gmaps_cookies"
os.makedirs(COOKIES_DIR, exist_ok=True) 
REPORT_FILE = "reported_reviews.json"
HISTORY_FILE = "report_history_email.json" # Kunci: Email Reporter
SUBMITTED_LOG_FILE = "submitted_log.json" # Log untuk tampilan UI (Global)

# --- Konfigurasi Timeout dan Kadaluarsa ---
COOKIE_EXPIRY_MINUTES = 180  # 3 hours
LOGIN_TIMEOUT_SECONDS = 300  # 5 menit

# --- Kategori Laporan Resmi ---
# Daftar ini digunakan sebagai hasil klasifikasi akhir
REPORT_CATEGORIES = [
    "Off topic",
    "Conflict of interest",
    "Profanity",
    "Bullying or harassment",
    "Discrimination or hate speech",
]

# --- Definisi yang Diperkaya untuk Pembelajaran Model (Embedding) ---
# Model akan menggunakan deskripsi ini untuk membuat representasi vektor yang lebih spesifik
CATEGORY_DEFINITIONS = {
    "Off topic": [
        "Content that is not relevant to the place being reviewed.",
        "A personal anecdote or political comment unrelated to the business.",
        "Random thoughts or generic statements that do not describe the location or experience."
    ],
    "Conflict of interest": [
        "Reviews posted by the business owner, employee, or a direct competitor.",
        "Content from someone paid to write the review.",
        "Unfairly biased content due to a personal relationship with the business."
    ],
    "Profanity": [
        "Use of strong vulgar, obscene, or sexually explicit language.",
        "Content containing slurs or excessively crude words.",
        "Blatant use of foul or indecent language."
    ],
    "Bullying or harassment": [
        "Directly attacking, insulting, or threatening an individual user or employee.",
        "Content that encourages hate or violence against a person.",
        "Intimidating or aggressive language directed at someone."
    ],
    "Discrimination or hate speech": [
        "Content that promotes discrimination or disparages based on race, gender, religion, or orientation.",
        "Attacks against a protected group of people.",
        "Hate speech or bias against any protected characteristics."
    ],
}