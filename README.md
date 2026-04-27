# 📄 AI Resume Screening Agent

An intelligent resume screening system powered by semantic embeddings, multi-factor scoring, and optional LLM analysis. Automatically screen, rank, and analyze resumes against job descriptions in real-time.

---

## ✨ Features

✅ **Multi-Resume Processing** – Upload and screen multiple resumes simultaneously  
✅ **Semantic Matching** – `paraphrase-multilingual-mpnet-base-v2` for accurate multilingual understanding  
✅ **Multi-Factor Scoring** – Weighted algorithm: embeddings (40%), required skills (35%), preferred skills (15%), experience (10%)  
✅ **Structured Extraction** – Detects email, phone, years of experience, skills, education, certifications  
✅ **LLM Analysis** – Optional detailed candidate analysis via Google Gemini 2.0 Flash or Anthropic Claude 3.5  
✅ **Interactive Dashboard** – Analytics, filtering by score/experience level, candidate comparison  
✅ **Configurable Weights** – Adjust scoring weights from the sidebar  
✅ **Export Functionality** – Download results as CSV, JSON, or Excel (.xlsx)  
✅ **Production-Ready** – Caching, error handling, logging, Docker, CI/CD  

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI Layer                       │
│        (Job Description Input + Resume Upload)              │
└────────┬────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────┐
│              extraction.py – PDF Parsing Layer              │
│  Email · Phone · Years Exp · Skills · Education · Certs     │
└────────┬────────────────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────────┐
│          scoring.py – Multi-Factor Scoring Layer            │
│  Embeddings 40% · Required Skills 35%                       │
│  Preferred Skills 15% · Experience 10%                      │
└────────┬────────────────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────────┐
│         utils.py – LLM Analysis & Export Layer              │
│  Google Gemini 2.0 Flash / Anthropic Claude 3.5 (optional)  │
│  CSV · JSON · Excel export                                   │
└────────┬────────────────────────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────────────────────────────────┐
│                 Results Dashboard                            │
│    Ranked table · Detailed profiles · Comparison · Export   │
└──────────────────────────────────────────────────────────────┘
```

**Tech Stack:**
- **Frontend:** Streamlit ≥ 1.40
- **Embeddings:** Sentence Transformers – `paraphrase-multilingual-mpnet-base-v2`
- **ML:** scikit-learn (cosine similarity)
- **LLM (optional):** Google Gemini 2.0 Flash · Anthropic Claude 3.5 Sonnet
- **PDF Processing:** pdfplumber
- **Data:** Pandas, NumPy
- **Export:** openpyxl (Excel)

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- (Optional) Google API Key – [makersuite.google.com](https://makersuite.google.com)
- (Optional) Anthropic API Key – [console.anthropic.com](https://console.anthropic.com)

### 2. Installation

```bash
git clone <repo-url>
cd resumea
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration

```bash
cp env.example .env
# Edit .env and add your API keys (optional)
```

### 4. Run

```bash
streamlit run app.py
```

Opens at **http://localhost:8501**

---

## 🐳 Docker

```bash
# Build and run with Docker Compose
docker compose up --build

# Or manually
docker build -t resume-screener .
docker run -p 8501:8501 -e GOOGLE_API_KEY=<key> resume-screener
```

---

## 📊 Scoring Methodology

| Component | Default Weight | Description |
|-----------|---------------|-------------|
| **Semantic Embedding** | 40% | Cosine similarity via `paraphrase-multilingual-mpnet-base-v2` |
| **Required Skills** | 35% | Percentage of JD skills found in resume |
| **Preferred Skills** | 15% | Bonus for matching nice-to-have skills |
| **Experience** | 10% | Years of experience vs. JD requirements |

Weights are fully configurable from the sidebar.

---

## 📤 Output

### Summary Table
| Rank | Candidate | Score | Recommendation | Experience Level | Skills |
|------|-----------|-------|----------------|-----------------|--------|
| 1 | alice.pdf | 87% | ✅ Strongly Recommend | Senior | 12 |

### Detailed Profile per Candidate
- Score breakdown (4-factor progress bars)
- Contact info (email, phone)
- Education & certifications
- Matched required / preferred skills
- LLM-generated hiring recommendation (when API key provided)

### Export Formats
- **CSV** – Summary for HR team
- **JSON** – Full data for integrations
- **Excel** – Formatted spreadsheet

---

## 📁 Project Structure

```
resumea/
├── app.py               # Main Streamlit application
├── config.py            # Configuration & scoring weights
├── extraction.py        # PDF parsing & structured extraction
├── scoring.py           # Multi-factor scoring engine
├── utils.py             # LLM analysis & export helpers
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker Compose for local dev
├── env.example          # Environment variable template
├── tests/               # Unit tests
│   └── test_core.py
├── .github/workflows/
│   └── ci.yml           # GitHub Actions CI/CD
└── README.md
```

---

## 🛠️ Development

```bash
# Run tests
pytest tests/ -v

# Lint
flake8 . --max-line-length=120 --exclude=.git,__pycache__
```

---

## 📝 Limitations

- PDF quality directly affects text extraction accuracy
- LLM analysis requires a valid API key and network access
- Scanned (image-only) PDFs are not supported without OCR (Tesseract)

---

## 📄 License

Open source | Created for Roomans AI Challenge 2025

---

**Built with ❤️ using Sentence Transformers, Streamlit, and optional Gemini/Claude LLMs**
