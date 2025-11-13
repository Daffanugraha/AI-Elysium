# utils/constants.py

import os
from datetime import timedelta
import json

# --- Konfigurasi File & Direktori ---
COOKIES_DIR = "gmaps_cookies"
os.makedirs(COOKIES_DIR, exist_ok=True) 
REPORT_FILE = "reported_reviews.json"
HISTORY_FILE = "report_history_email.json" # Kunci: Email Reporter
SUBMITTED_LOG_FILE = "submitted_log.json" # Log untuk tampilan UI (Global)

# --- Konfigurasi Timeout dan Kadaluarsa ---
COOKIE_EXPIRY_MINUTES = 180  # 3 jam
LOGIN_TIMEOUT_SECONDS = 300  # 5 menit

# --- Kategori Laporan ---
REPORT_CATEGORIES = [
    "Off topic",
    "Spam",
    "Conflict of interest",
    "Profanity",
    "Bullying or harassment",
    "Discrimination or hate speech",
]