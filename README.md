[<div align="center">

<img src="static/Background.jpg" alt="AI Elysium Banner" width="100%" />

<br/><br/>

# 🌌 AI ELYSIUM

### *Pure Intelligence. Think Beyond. Think Elysium.*

<br/>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Framework-Streamlit-FF4B4B?logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Automation-Selenium-43B02A?logo=selenium&logoColor=white" />
  <img src="https://img.shields.io/badge/AI_Model-multilingual--e5--small-FFD21F?logo=huggingface&logoColor=black" />
  <img src="https://img.shields.io/badge/Embedding-SentenceTransformers-9B59B6" />
  <img src="https://img.shields.io/badge/Target-Google_Maps-4285F4?logo=googlemaps&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-brightgreen" />
</p>

<br/>

> **AI Elysium** adalah alat otomatis berbasis AI untuk **melaporkan ulasan berperingkat rendah** di Google Maps secara massal.  
> Dengan satu klik — ulasan 1★ & 2★ dianalisis, dikategorikan, dan dilaporkan langsung ke Google.

<br/>

[🚀 Instalasi](#-instalasi--setup) · [🎬 Cara Kerja](#-cara-kerja--flow) · [🤖 Model AI](#-model-ai) · [📤 Output](#-output-laporan)

</div>

---

## 💡 Tentang Proyek

**AI Elysium** dibuat untuk membantu pemilik bisnis atau pengelola lokasi Google Maps yang menghadapi ulasan tidak wajar, palsu, atau melanggar kebijakan. Proses pelaporan ke Google secara manual sangat lambat dan repetitif — AI Elysium mengotomatiskan semuanya.

**Alur kerja aplikasi:**
1. Login ke akun Google menggunakan Selenium (sesi browser nyata)
2. Scraping semua ulasan 1★ dan 2★ dari link Google Maps target
3. Menganalisis teks ulasan menggunakan model **`intfloat/multilingual-e5-small`** via SentenceTransformers
4. Menampilkan prediksi kategori pelanggaran + confidence score + alasan + konteks
5. User bisa **override kategori** via dropdown sebelum melaporkan
6. Melaporkan ulasan ke Google Maps otomatis — satu per satu atau massal
7. Menyimpan log laporan ke JSON persisten + export Excel

---

## 🛠 Tech Stack & Spesifikasi

### Framework & Library

| Komponen | Teknologi | Fungsi |
|---|---|---|
| **UI Framework** | [Streamlit](https://streamlit.io) | Antarmuka web interaktif |
| **Web Automation** | [Selenium 4](https://selenium.dev) + webdriver-manager | Scraping & auto-report Google Maps |
| **AI Model** | `intfloat/multilingual-e5-small` | Sentence embedding untuk klasifikasi ulasan |
| **Embedding Library** | [SentenceTransformers](https://sbert.net) | Load & inference model HuggingFace |
| **Similarity Engine** | Cosine Similarity (`util.cos_sim`) + PyTorch | Matching ulasan ke kategori pelanggaran |
| **NLP Preprocessing** | NLTK (stopwords) + emoji + regex | Pembersihan & tokenisasi teks |
| **Data Processing** | [Pandas](https://pandas.pydata.org) | Manipulasi tabel ulasan |
| **Visualisasi** | [Altair](https://altair-viz.github.io) | Grafik distribusi rating |
| **Export** | openpyxl | Download data ke Excel |

### Spesifikasi Sistem

```
Bahasa        : Python 3.10+
Browser       : Google Chrome (real browser session)
OS            : Windows 10/11, Linux, macOS
RAM           : Minimal 4 GB (disarankan 8 GB)
Internet      : Wajib aktif (scraping & report ke Google Maps)
ChromeDriver  : Auto-managed oleh webdriver-manager
```

---

## ✨ Fitur Utama

```
╔══════════════════════════════════════════════════════════════════╗
║  🔐  Multi-Account Google Login  │ Simpan banyak sesi sekaligus ║
║  🔍  Scraper Google Maps         │ Ambil ulasan 1★ & 2★ otomatis║
║  🤖  AI Review Classifier        │ multilingual-e5-small + cos  ║
║  ✏️  Override Kategori Manual    │ Ubah kategori sebelum report  ║
║  🚨  Single & Bulk Auto-Report   │ Lapor 1 atau seluruh halaman  ║
║  🛡️  Anti-Double Report          │ SHA-256 key per ulasan        ║
║  📊  Rating Analytics Chart      │ Distribusi bintang (Altair)   ║
║  💾  Log JSON Persistent         │ Riwayat tersimpan permanen    ║
║  📥  Export Excel                │ Download semua data ulasan    ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 🎬 Cara Kerja / Flow

```
  Input: Link Google Maps
         │
         ▼
  ┌─────────────────────────────────┐
  │  🔐 LOGIN GOOGLE               │
  │  Selenium buka browser nyata   │
  │  User login manual sekali      │
  │  Cookies disimpan ke disk      │
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │  🔍 SCRAPING ULASAN            │
  │  Buka Maps → scroll reviews    │
  │  Filter hanya rating 1★ & 2★  │
  │  Ekstrak: User, Teks, Tanggal  │
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────────────────────┐
  │  🤖 AI CLASSIFICATION                          │
  │                                                 │
  │  Model  : intfloat/multilingual-e5-small        │
  │  Library: SentenceTransformers                  │
  │                                                 │
  │  1. Encode teks ulasan → vector embedding       │
  │  2. Encode 9 nama kategori → category vectors   │
  │  3. Cosine Similarity: ulasan vs. tiap kategori │
  │  4. Pilih kategori dengan skor tertinggi        │
  │  5. Extract key tokens via word-level embedding │
  │  6. Match policy definition via cos_sim         │
  └────────────────┬────────────────────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │  🖥️ TAMPILAN UI + FILTER       │
  │  Kartu ulasan + prediksi AI    │
  │  ✏️ User bisa OVERRIDE         │
  │     kategori via dropdown      │
  └────────────────┬────────────────┘
                   │
          ┌────────┴──────────┐
          ▼                   ▼
  ┌──────────────┐   ┌─────────────────────┐
  │ 🚨 SINGLE   │   │  🚨 BULK REPORT     │
  │ REPORT      │   │  Loop otomatis       │
  │ Per ulasan  │   │  Seluruh halaman     │
  └──────┬───────┘   └──────────┬──────────┘
         └──────────┬───────────┘
                    │
                    ▼
  ┌─────────────────────────────────┐
  │  💾 LOG & EXPORT               │
  │  JSON persisten di disk        │
  │  Export ke Excel (.xlsx)       │
  └─────────────────────────────────┘
```

---

## 🤖 Model AI

### `intfloat/multilingual-e5-small`

Model yang digunakan adalah **[intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small)** dari Hugging Face, dimuat via library `sentence-transformers`.

```
Model   : intfloat/multilingual-e5-small
Type    : Sentence Embedding (Dense Retrieval)
Language: Multilingual (100+ bahasa, termasuk Indonesia & Inggris)
Dimensi : 384
Library : sentence-transformers
```

Model ini digunakan untuk mengubah teks ulasan dan nama-nama kategori menjadi **vector embedding**, lalu menghitung **cosine similarity** di antara keduanya — kategori dengan skor tertinggi dipilih sebagai prediksi.

### Pipeline Klasifikasi (dari `utils/helpers.py`)

```
Teks Ulasan (input)
       │
       ▼
  MODEL.encode(review_text)          → text_embedding (384-dim)
  MODEL.encode(REPORT_CATEGORIES)    → category_embeddings (9 x 384)
       │
       ▼
  util.cos_sim(text_embedding, category_embeddings)
       │
       ▼
  argmax → predicted_category + score (%)
       │
       ▼
  extract_key_tokens()
  ├─ Encode tiap kata dalam ulasan   → word_embeddings
  ├─ torch.matmul(word_emb, cat_emb) → per-word similarity
  └─ Top-4 kata → reason_tokens
       │
       ▼
  get_validation_details()
  ├─ Encode CATEGORY_DEFINITIONS[kategori]
  ├─ cos_sim(ulasan, definisi kebijakan)
  └─ Pilih definisi paling relevan → PolicyReason
```

### Contoh Output Classifier

```
Input  : "really want play anymore. unclear parking fee for, hsr valve
          caps gone. used free park, became paid parking fee..."

Output :
  ├─ category_ai     : "Harmful"
  ├─ score           : 55.61   (confidence %)
  ├─ reason_tokens   : "unsafe, trash, burning, used"
  ├─ PolicyReason    : "Violates definition: 'Promoting violence or harm
  │                     toward staff, customers, or property.'"
  └─ ContextSentence : "**used** free park, became paid parking fee."
```

### Kategori Pelanggaran yang Dideteksi

| Kategori | Deskripsi |
|---|---|
| `Off topic` | Konten tidak relevan dengan bisnis/lokasi |
| `Spam` | Konten berulang, promosi, atau link tidak wajar |
| `Conflict of interest` | Ulasan dari pemilik, karyawan, atau kompetitor |
| `Profanity` | Kata-kata kasar atau tidak pantas |
| `Bullying` | Serangan atau intimidasi personal |
| `Discrimination` | Konten diskriminatif terhadap kelompok tertentu |
| `Personal info` | Memuat data pribadi sensitif orang lain |
| `Harmful` | Konten promosi kekerasan atau bahaya fisik |
| `Legal issue` | Klaim hukum, fitnah, atau pencemaran nama baik |

### Override Kategori Manual

Prediksi AI **bisa diubah** sebelum laporan dikirim. Setiap kartu ulasan punya dropdown:

```
📑 Override Report Category for John Doe
┌──────────────────────────────────────────┐
│  Harmful                               ▼ │   ← Bisa diganti kategori lain
└──────────────────────────────────────────┘

         [ 🚨 Single Automatic Report ]
```

---

## 🖥️ Tampilan UI

Setiap ulasan ditampilkan sebagai kartu dengan informasi lengkap dari AI:

```
👤 John Doe — ⭐ 1.0
🕒 2025-03-29 | Reviews: 3 reviews

💬 "really want play anymore. unclear parking fee for, hsr valve
    caps gone. used free park, became paid parking fee..."

🚀 AI Prediction: [ Harmful ] (55.61% confidence)
📋 Policy Violation Reason: Violates definition: 'Promoting violence...'
🔍 Key Concepts: unsafe, trash, burning, used
📝 Contextual Sentence: **used** free park, became paid parking fee.

┌──────────────────────────────────────────┐
│  Harmful                               ▼ │
└──────────────────────────────────────────┘
[ 🚨 Single Automatic Report ]
```

---

## 📤 Output Laporan

Setiap ulasan yang berhasil dilaporkan dicatat ke **log JSON persisten** dan bisa diunduh sebagai Excel.

### Format JSON Output

```json
[
    {
        "Place": "Perumahan Puri Prima Sari",
        "User": "Zaidan Tri Syafiq",
        "Review Text": "",
        "Date": "2022-02-24",
        "Category report": "Off topic",
        "Reported By": "nugrahadaffa568@gmail.com",
        "Review Key": "3c0de34c65457b1c5f57ddf2515587414d6151c61d65eaaf704016296072eedf",
        "Reported Time": "2026-02-23 11:50:40"
    },
    {
        "Place": "Perumahan Puri Prima Sari",
        "User": "budi79ono",
        "Review Text": "",
        "Date": "2019-02-25",
        "Category report": "Off topic",
        "Reported By": "nugrahadaffa568@gmail.com",
        "Review Key": "bb063188df1a54a4d44ba41b3ce67d409da745e38d59d24aaf31cb8b6e4d02d9",
        "Reported Time": "2026-02-23 11:51:26"
    },
    {
        "Place": "Perumahan Puri Prima Sari",
        "User": "matheus johanis",
        "Review Text": "",
        "Date": "2018-02-25",
        "Category report": "Off topic",
        "Reported By": "nugrahadaffa568@gmail.com",
        "Review Key": "6781828a34bb1bd9993ae7f2a52883b11b45fb7dcca453c47cf04ea11fa0f6b8",
        "Reported Time": "2026-02-23 11:52:06"
    }
]
```

### Penjelasan Field Output

| Field | Deskripsi |
|---|---|
| `Place` | Nama lokasi Google Maps yang dianalisis |
| `User` | Nama akun penulis ulasan |
| `Review Text` | Teks ulasan (kosong = ulasan hanya bintang tanpa teks) |
| `Date` | Tanggal ulasan ditulis |
| `Category report` | Kategori pelanggaran yang dipilih saat laporan dikirim |
| `Reported By` | Email akun Google yang mengirim laporan |
| `Review Key` | Hash SHA-256 unik per ulasan — dipakai sistem anti-double-report |
| `Reported Time` | Timestamp laporan dikirim (`YYYY-MM-DD HH:MM:SS`) |

### File yang Tersimpan
- **`report_history.json`** — Log per email reporter, digunakan engine anti-double-report
- **`submitted_log.json`** — Log tampilan tabel di UI
- **`.xlsx`** — Bisa diunduh langsung dari tombol di UI

---

## 🗂 Struktur Proyek

```
AI-Elysium/
│
├── 📄 app.py                    # Entry point — UI Streamlit utama
│
├── 📁 components/
│   ├── auth_manager.py          # Login Google & manajemen cookies sesi
│   ├── scraper.py               # Selenium scraper ulasan Google Maps
│   └── reporter.py              # Auto-report engine + persistensi log JSON
│
├── 📁 utils/
│   ├── helpers.py               # SentenceTransformer classifier + key extractor
│   └── constants.py             # REPORT_CATEGORIES + CATEGORY_DEFINITIONS
│
├── 📁 styles/
│   └── main.css                 # Custom CSS dark-theme UI
│
├── 📁 static/
│   └── Background.jpg           # Background visual aplikasi
│
└── 📄 README.md
```

---

## 🚀 Instalasi & Setup

### Prasyarat
- Python 3.10+
- Google Chrome terinstall
- Git

### Langkah Instalasi

```bash
# 1. Clone repository
git clone https://github.com/Daffanugraha/AI-Elysium.git
cd AI-Elysium

# 2. Buat virtual environment (direkomendasikan)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install semua dependencies
pip install -r requirements.txt

# 4. Jalankan aplikasi
streamlit run app.py
```

> ✅ ChromeDriver diunduh otomatis oleh `webdriver-manager`.  
> ✅ Model `intfloat/multilingual-e5-small` diunduh otomatis dari Hugging Face saat pertama kali dijalankan.

---

## 📖 Panduan Penggunaan

**Step 1 — Login Akun Google**
Klik **"➕ Login / Add New Account"**. Browser Chrome terbuka → login ke akun Google secara normal → cookies tersimpan otomatis.

**Step 2 — Input Link Google Maps**
Paste URL Google Maps lokasi yang ulasannya ingin dilaporkan.

**Step 3 — Start Analyze**
Klik **"🚀 Start Analyze"**. Scraper mengambil semua ulasan 1★ & 2★, AI langsung menganalisis setiap ulasan menggunakan model `intfloat/multilingual-e5-small`.

**Step 4 — Cek & Override (Opsional)**
Lihat prediksi AI di setiap kartu. Kalau kategori tidak sesuai, ubah lewat **dropdown Override** sebelum lapor.

**Step 5 — Report**
- **Per ulasan**: Klik **"🚨 Single Automatic Report"**
- **Massal**: Klik **"🚨 Start Page Report"** → lapor semua ulasan di halaman
- **Stop**: Klik **"🚫 Stop Report Page"** kapan saja

**Step 6 — Export**
Klik **"💾 Download Reviews (Excel)"** untuk unduh data ke file `.xlsx`.

---

## 📄 Lisensi

Proyek ini dilisensikan di bawah **MIT License** — lihat file [LICENSE](LICENSE) untuk detail.

---

<div align="center">

Made with ❤️ by **[Daffa Nugraha](https://github.com/Daffanugraha)**

*"Pure Intelligence. Think Beyond. Think Elysium."*

⭐ Kalau project ini berguna, kasih **Star** ya!

</div>
](https://www.linkedin.com/in/mdaffanugraha/)
