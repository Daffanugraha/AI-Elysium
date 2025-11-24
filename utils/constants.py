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
COOKIE_EXPIRY_MINUTES = 90  # 1 hours 30 Minutes
LOGIN_TIMEOUT_SECONDS = 300  # 5 menit

# --- Kategori Laporan Resmi ---
# Daftar ini digunakan sebagai hasil klasifikasi akhir
REPORT_CATEGORIES = [
    "Off topic",
    "Conflict of interest",
    "Profanity",
    "Bullying or harassment",
    "Discrimination or hate speech",
    "Personal information", 
    "Harmful"
]

# --- Definisi yang Diperkaya untuk Pembelajaran Model (Embedding) ---
# Model akan menggunakan deskripsi ini untuk membuat representasi vektor yang lebih spesifik
CATEGORY_DEFINITIONS = {
    "Off topic": [
        "Content that is not relevant to the place being reviewed.",
        "A personal anecdote or political comment unrelated to the business.",
        "Random thoughts or generic statements that do not describe the location or experience.",
        # --- Tambahan Google Policy ---
        "Content that does not describe an actual experience at the location.",
        "Comments about national/global issues unrelated to the place.",
        "Complaints about things the business cannot control (weather, traffic, taxes).",
        "Promotion of other products, services, or businesses not related to the place."
    ],
    "Conflict of interest": [
        "Reviews posted by the business owner, employee, or a direct competitor.",
        "Content from someone paid to write the review.",
        "Unfairly biased content due to a personal relationship with the business.",
        # --- Tambahan Google Policy ---
        "Reviews written to artificially inflate or deflate ratings.",
        "Content created as part of incentives, gifts, or rewards programs.",
        "Coordinated campaigns to manipulate ratings (review bombing or boosting).",
        "Fake reviews created to influence reputation."
    ],
    "Profanity": [
        "Use of strong vulgar, obscene, or sexually explicit language.",
        "Content containing slurs or excessively crude words.",
        "Blatant use of foul or indecent language.",
        # --- Tambahan Google Policy ---
        "Use of offensive or vulgar language unrelated to the experience.",
        "Obscene expressions intended to shock or offend readers.",
        "Profanity targeting a place, staff, or customers in an inappropriate manner."
    ],
    "Bullying or harassment": [
        "Directly attacking, insulting, or threatening an individual user or employee.",
        "Content that encourages hate or violence against a person.",
        "Intimidating or aggressive language directed at someone.",
        # --- Tambahan Google Policy ---
        "Calling staff or customers derogatory names or insults.",
        "Publicly shaming someone with the intent to demean.",
        "Threats—explicit or implied—towards any person at the location.",
        "Harassment based on appearance, name, or personal characteristics."
    ],
    "Discrimination or hate speech": [
        "Content that promotes discrimination or disparages based on race, gender, religion, or orientation.",
        "Attacks against a protected group of people.",
        "Hate speech or bias against any protected characteristics.",
        # --- Tambahan Google Policy ---
        "Generalizing or demeaning groups using stereotypes.",
        "Linking business quality or service to someone's identity group.",
        "Using coded language, symbols, or phrases promoting hate.",
        "Encouraging discrimination towards customers or employees."
    ],
    "Personal information": [
        "Content that reveals private, non-public information about an individual (e.g., phone number, home address, medical records).",
        "Publishing someone's name and contact details without consent.",
        "Sharing financial or sensitive identification documents.",
        # --- Tambahan Google Policy ---
        "Posting photos of personal documents (ID cards, license plates, receipts).",
        "Revealing personal details about someone's private life.",
        "Sharing medical or health-related information about someone.",
        "Identifying minors without parental consent."
    ],
    "Harmful": [
        "Content that promotes illegal acts, violence, self-harm, or terrorism.",
        "Instructional content on creating weapons or dangerous substances.",
        "Encouraging or providing methods for illegal activities.",
        # --- Tambahan Google Policy ---
        "Promoting violence or harm toward staff, customers, or property.",
        "Instructions on committing vandalism, fraud, or unsafe behavior.",
        "Giving dangerous guidance (e.g., bypassing emergency systems or security).",
        "Supporting harmful organizations or activities."
    ]
}
