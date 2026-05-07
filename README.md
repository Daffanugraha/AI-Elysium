<div align="center">

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
</p>

<br/>

> **AI Elysium** is an AI-powered automation tool for **automatically reporting low-rating reviews** on Google Maps at scale.
> Scrape, classify, and report 1★ & 2★ reviews — all in one click.

<br/>

[🚀 Installation](#-installation) · [🎬 How It Works](#-how-it-works) · [🤖 AI Model](#-ai-model) · [📤 Output](#-output)

</div>

---

## 💡 About This Project

**AI Elysium** was built as a freelance AI engineering project to help business owners and Google Maps location managers deal with unfair, fake, or policy-violating reviews. Manual reporting to Google is slow and repetitive — AI Elysium automates the entire pipeline.

**What this app does:**
1. Logs into Google using Selenium (real browser session with cookies)
2. Scrapes all 1★ and 2★ reviews from a given Google Maps link
3. Analyzes each review using **`intfloat/multilingual-e5-small`** via SentenceTransformers
4. Displays predicted violation category + confidence score + policy reason + context
5. Lets users **override the category** via dropdown before reporting
6. Automatically reports reviews to Google Maps — one at a time or in bulk
7. Saves a persistent JSON log and exports data to Excel

---

## 🛠 Tech Stack & Specifications

### Frameworks & Libraries

| Component | Technology | Role |
|---|---|---|
| **UI Framework** | [Streamlit](https://streamlit.io) | Interactive web interface |
| **Web Automation** | [Selenium 4](https://selenium.dev) + webdriver-manager | Scraping & auto-reporting on Google Maps |
| **AI Model** | `intfloat/multilingual-e5-small` | Sentence embedding for review classification |
| **Embedding Library** | [SentenceTransformers](https://sbert.net) | Load & run HuggingFace model |
| **Similarity Engine** | Cosine Similarity (`util.cos_sim`) + PyTorch | Match reviews to violation categories |
| **NLP Preprocessing** | NLTK (stopwords) + emoji + regex | Text cleaning & tokenization |
| **Data Processing** | [Pandas](https://pandas.pydata.org) | Review table manipulation |
| **Visualization** | [Altair](https://altair-viz.github.io) | Rating distribution charts |
| **Export** | openpyxl | Download data as Excel |

### System Requirements

```
Language      : Python 3.10+
Browser       : Google Chrome (real browser session)
OS            : Windows 10/11, Linux, macOS
RAM           : Minimum 4 GB (8 GB recommended)
Internet      : Required (scraping & reporting to Google Maps)
ChromeDriver  : Auto-managed by webdriver-manager
```

---

## ✨ Key Features

```
╔══════════════════════════════════════════════════════════════════╗
║  🔐  Multi-Account Google Login  │ Store multiple sessions      ║
║  🔍  Google Maps Scraper         │ Auto-collect 1★ & 2★ reviews ║
║  🤖  AI Review Classifier        │ multilingual-e5-small + cos  ║
║  ✏️  Manual Category Override    │ Change category before report ║
║  🚨  Single & Bulk Auto-Report   │ Report one or full page      ║
║  🛡️  Anti-Double Report          │ SHA-256 key per review       ║
║  📊  Rating Analytics Chart      │ Star distribution (Altair)   ║
║  💾  Persistent JSON Log         │ Report history saved to disk  ║
║  📥  Excel Export                │ Download all review data      ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 🎬 How It Works

```
  Input: Google Maps URL
         │
         ▼
  ┌─────────────────────────────────┐
  │  🔐 GOOGLE LOGIN               │
  │  Selenium opens real browser   │
  │  User logs in once manually    │
  │  Cookies saved to disk         │
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │  🔍 REVIEW SCRAPING            │
  │  Open Maps → scroll reviews    │
  │  Filter only 1★ & 2★ ratings   │
  │  Extract: User, Text, Date     │
  └────────────────┬────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────────────────────┐
  │  🤖 AI CLASSIFICATION                          │
  │                                                 │
  │  Model  : intfloat/multilingual-e5-small        │
  │  Library: SentenceTransformers                  │
  │                                                 │
  │  1. Encode review text   → 384-dim vector       │
  │  2. Encode 9 categories  → category vectors     │
  │  3. Cosine Similarity: review vs. each category │
  │  4. Pick highest-score category                 │
  │  5. Extract key tokens via word-level embedding │
  │  6. Match policy definition via cos_sim         │
  └────────────────┬────────────────────────────────┘
                   │
                   ▼
  ┌─────────────────────────────────┐
  │  🖥️ UI DISPLAY + FILTERS       │
  │  Review cards + AI prediction  │
  │  ✏️ Override category via      │
  │     dropdown before reporting  │
  └────────────────┬────────────────┘
                   │
          ┌────────┴──────────┐
          ▼                   ▼
  ┌──────────────┐   ┌─────────────────────┐
  │ 🚨 SINGLE   │   │  🚨 BULK REPORT     │
  │ REPORT      │   │  Auto-loop through   │
  │ Per review  │   │  entire page         │
  └──────┬───────┘   └──────────┬──────────┘
         └──────────┬───────────┘
                    │
                    ▼
  ┌─────────────────────────────────┐
  │  💾 LOG & EXPORT               │
  │  Persistent JSON on disk       │
  │  Export to Excel (.xlsx)       │
  └─────────────────────────────────┘
```

---

## 🤖 AI Model

### `intfloat/multilingual-e5-small`

The classification engine uses **[intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small)** from Hugging Face, loaded via `sentence-transformers`.

```
Model     : intfloat/multilingual-e5-small
Type      : Sentence Embedding (Dense Retrieval)
Languages : 100+ languages including Indonesian & English
Dimensions: 384
Library   : sentence-transformers
```

Reviews and category names are both encoded into vector space. **Cosine similarity** determines which category the review is closest to — the highest-scoring category becomes the prediction.

### Classification Pipeline

```
Review Text (input)
       │
       ▼
  MODEL.encode(review_text)          → text_embedding (384-dim)
  MODEL.encode(REPORT_CATEGORIES)    → category_embeddings (9 × 384)
       │
       ▼
  util.cos_sim(text_embedding, category_embeddings)
       │
       ▼
  argmax → predicted_category + confidence score (%)
       │
       ▼
  extract_key_tokens()
  ├─ Encode each word in review      → word_embeddings
  ├─ torch.matmul(word_emb, cat_emb) → per-word similarity score
  └─ Top-4 words → reason_tokens
       │
       ▼
  get_validation_details()
  ├─ Encode CATEGORY_DEFINITIONS[category]
  ├─ cos_sim(review, policy definitions)
  └─ Best-matching definition → PolicyReason
```

### Example Classifier Output

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

### Supported Violation Categories

| Category | Description |
|---|---|
| `Off topic` | Content unrelated to the business or location |
| `Spam` | Repetitive content, promotions, or suspicious links |
| `Conflict of interest` | Review from owner, employee, or competitor |
| `Profanity` | Offensive or inappropriate language |
| `Bullying` | Personal attacks or harassment |
| `Discrimination` | Discriminatory content toward any group |
| `Personal info` | Contains sensitive personal data of others |
| `Harmful` | Promotes violence or physical harm |
| `Legal issue` | Legal claims, defamation, or libel |

### Manual Category Override

AI predictions can be changed before submitting. Each review card has a dropdown to switch categories:

```
📑 Override Report Category for John Doe
┌──────────────────────────────────────────┐
│  Harmful                               ▼ │   ← Change to any category
└──────────────────────────────────────────┘

         [ 🚨 Single Automatic Report ]
```

---

## 🖥️ UI Preview

Each review is displayed as a card with full AI output:

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

## 📤 Output

All successfully reported reviews are logged to a **persistent JSON file** on disk and viewable as a table in the UI or downloaded as Excel.

### JSON Log Format

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

### Output Field Reference

| Field | Description |
|---|---|
| `Place` | Google Maps location name that was analyzed |
| `User` | Name of the review author |
| `Review Text` | Review content (empty = rating-only review with no text) |
| `Date` | Date the review was written |
| `Category report` | Violation category selected when the report was submitted |
| `Reported By` | Email of the Google account that sent the report |
| `Review Key` | SHA-256 unique hash per review — used by the anti-double-report system |
| `Reported Time` | Timestamp when the report was submitted (`YYYY-MM-DD HH:MM:SS`) |

### Saved Files
- **`report_history.json`** — Structured log per reporter email, used by the anti-double-report engine
- **`submitted_log.json`** — UI display log
- **`.xlsx`** — Downloadable directly from the UI

---

## 🗂 Project Structure

```
AI-Elysium/
│
├── 📄 app.py                    # Entry point — main Streamlit UI
│
├── 📁 components/
│   ├── auth_manager.py          # Google login & session cookie management
│   ├── scraper.py               # Selenium scraper for Google Maps reviews
│   └── reporter.py              # Auto-report engine + persistent JSON log
│
├── 📁 utils/
│   ├── helpers.py               # SentenceTransformer classifier + key token extractor
│   └── constants.py             # REPORT_CATEGORIES + CATEGORY_DEFINITIONS
│
├── 📁 styles/
│   └── main.css                 # Custom dark-theme CSS
│
├── 📁 static/
│   └── Background.jpg           # App background asset
│
└── 📄 README.md
```

---

## 🚀 Installation

### Prerequisites
- Python 3.10+
- Google Chrome installed
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/Daffanugraha/AI-Elysium.git
cd AI-Elysium

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

> ✅ ChromeDriver is downloaded automatically by `webdriver-manager`.  
> ✅ The `intfloat/multilingual-e5-small` model is downloaded automatically from Hugging Face on first run.

---

## 📖 Usage Guide

**Step 1 — Login Google Account**
Click **"➕ Login / Add New Account"**. A Chrome browser opens → log in to your Google account normally → cookies are saved automatically.

**Step 2 — Input Google Maps Link**
Paste the Google Maps URL of the location whose reviews you want to report.

**Step 3 — Start Analyze**
Click **"🚀 Start Analyze"**. The scraper collects all 1★ & 2★ reviews and the AI classifies each one using `intfloat/multilingual-e5-small`.

**Step 4 — Review & Override (Optional)**
Check the AI prediction on each card. If the category doesn't fit, change it via the **Override dropdown** before reporting.

**Step 5 — Report**
- **Single**: Click **"🚨 Single Automatic Report"** on any card
- **Bulk**: Click **"🚨 Start Page Report"** to report all reviews on the current page
- **Stop**: Click **"🚫 Stop Report Page"** at any time to halt the bulk process

**Step 6 — Export**
Click **"💾 Download Reviews (Excel)"** to download all data as a `.xlsx` file.

---

<div align="center">

## 👨‍💻 Built By

**Muhammad Daffa Nugraha**
*Freelance AI Engineer*

<br/>

<a href="https://github.com/Daffanugraha">
  <img src="https://img.shields.io/badge/GitHub-Daffanugraha-181717?style=for-the-badge&logo=github&logoColor=white" />
</a>
&nbsp;
<a href="https://www.linkedin.com/in/mdaffanugraha/">
  <img src="https://img.shields.io/badge/LinkedIn-mdaffanugraha-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" />
</a>
&nbsp;
<a href="mailto:nugrahadaffa568@gmail.com">
  <img src="https://img.shields.io/badge/Email-nugrahadaffa568@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white" />
</a>

<br/><br/>

*"Pure Intelligence. Think Beyond. Think Elysium."*

⭐ If this project was useful, leave a **Star** on GitHub!

</div>
