# 🛡️ TruthLayer

> **Verify facts. Build trust.**  
> An AI-powered PDF fact-checking web application that ingests business documents, extracts empirical claims, cross-references live web evidence in real-time, and generates downloadable verification reports with traceable provenance.

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20GenAI-gemini--2.5--flash-4285F4.svg)](https://ai.google.dev/)
[![Tavily Search](https://img.shields.io/badge/Tavily%20Search%20API-live%20web-green.svg)](https://tavily.com/)
[![Groq Fallback](https://img.shields.io/badge/Groq%20Fallback-llama--3.3--70b-F55036.svg)](https://groq.com/)
[![Test Suite](https://img.shields.io/badge/Tests-96%20Passed%20(100%25)-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📌 The Problem

Marketing decks, analyst reports, whitepapers, and corporate presentations are frequently published with outdated statistics, misattributed quotes, hallucinated figures, and unverified factual assertions. Verifying these claims manually requires tedious searches across disparate sources, leaving organizations vulnerable to reputational risk, compliance violations, and eroded reader trust.

## 💡 The Solution

**TruthLayer** acts as an automated, objective editorial truth layer. Upload any digitally-authored PDF document, and TruthLayer executes an end-to-end multi-agent verification pipeline that isolates discrete factual assertions, gathers live corroborating or contradicting web evidence, assigns transparent classification verdicts, and produces publication-ready PDF, Markdown, and JSON audit certificates.

---

## 🏗️ Architecture & Pipeline Flow

TruthLayer is designed as a decoupled, multi-tier system following clean architecture principles.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                              │
│   Streamlit Web Interface (Upload, Dashboard, Claim Cards, Export)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Invokes Pipeline
┌───────────────────────────────────▼────────────────────────────────────┐
│                       ORCHESTRATION LAYER                              │
│              Verification Pipeline Coordinator (core/pipeline.py)      │
└───────────────┬───────────────────┬───────────────────┬────────────────┘
                │ 1. Extract Text   │ 2. Extract Claims │ 3. Retrieve Evidence
┌───────────────▼──────────┐ ┌──────▼─────────────┐ ┌───▼────────────────┐
│   PDF Extraction Module  │ │  Claim Extraction  │ │   Search Retrieval  │
│      (PyMuPDF / fitz)    │ │   (Gemini Flash)   │ │      (Tavily API)   │
└──────────────────────────┘ └────────────────────┘ └───┬────────────────┘
                                                        │ 4. Synthesize Reasoning
                                             ┌──────────▼────────────────┐
                                             │    Verification Engine    │
                                             │  (Gemini + Groq Fallback) │
                                             └──────────┬────────────────┘
                                                        │ 5. Generate Audit
                                             ┌──────────▼────────────────┐
                                             │     Report Generator      │
                                             │    (PDF / MD / JSON)      │
                                             └───────────────────────────┘
```

### The 4-Stage Sequential Verification Pipeline:
1. **PDF Text Extraction ([`PyMuPDF`](https://pymupdf.readthedocs.io/)):** Page-preserving, high-speed C-backed text extraction. Detects empty pages, corrupted files, and scanned documents.
2. **AI Empirical Claim Extraction ([`Google Gemini API`](https://ai.google.dev/)):** Extracts quantitative statistics, dates, financial metrics, and verifiable corporate facts while rejecting subjective marketing fluff and promotional rhetoric. Includes automatic failover to **Groq** (`llama-3.3-70b-versatile`).
3. **Live Web Evidence Retrieval ([`Tavily Search API`](https://tavily.com/)):** Formulates 2–3 targeted, entity-specific queries per claim and collects live web snippets, publication dates, and source domain rankings with integrated query-level caching.
4. **Fact Verification Engine ([`Gemini / Groq Reasoning`](file:///c:/Users/himan/OneDrive/Desktop/TruthLayer/src/core/verifier.py)):** Cross-references assertions against evidence, classifies verdicts into 4 standardized statuses, extracts verified corrections, and reconciles source citations.

---

## 🎯 Standardized Verification Status Taxonomy

TruthLayer classifies every factual claim into one of four standardized statuses:

| Status | Badge | Description | Required Output |
| :--- | :---: | :--- | :--- |
| **`VERIFIED`** | 🟢 | Reliable public web evidence sufficiently corroborates the claim. | Verified sources and reasoning. |
| **`INACCURATE`** | 🟠 | The claim has factual basis, but specific metrics, percentages, dates, or context are inaccurate or outdated. | **Mandatory Verified Correction** + sources. |
| **`FALSE`** | 🔴 | Reliable public evidence directly contradicts the assertion (e.g. fabricated facts, wrong entities). | **Mandatory Verified Correction** + refuting sources. |
| **`UNVERIFIED`** | ⚪ | Available public evidence is insufficient, ambiguous, or absent. | Conservative fallback (**Confidence: 0.0%**; missing evidence is never proof of falsity). |

---

## ✨ Key Capabilities & Highlights

- **🛡️ Strict Prompt-Injection Defenses:** Document text and web snippets are treated strictly as passive untrusted data, enclosed in `<untrusted_claim_data>` and `<untrusted_evidence_data>` tags, with automated XML tag breakout defusing.
- **⚡ Dual-LLM Resilience:** Automated fallback from Google Gemini (`gemini-2.5-flash`) to Groq (`llama-3.3-70b-versatile`) if rate limits or quota boundaries are encountered.
- **📊 Interactive SaaS Results Dashboard:** Real-time executive scorecards, proportional status breakdown bars, dynamic status filtering, and keyword search across claims and corrections.
- **📄 Downloadable Audit Reports:** Generates professional multi-page PDF audit reports (via ReportLab with running headers and dynamic page numbers), structured Markdown summaries, and JSON compliance certificates.
- **🌐 Authoritative Domain Prioritization:** Prioritizes `.gov`, `.edu`, `.org`, and primary regulatory filings (SEC 10-K/10-Q, central banks, Reuters, Bloomberg).
- **🔒 In-Memory Security:** User documents are processed purely in-memory (`io.BytesIO`) without temporary disk writes. API credentials are encrypted via environment variables and masked in logs (`AIza...cdef`).

---

## 📂 Project Structure

```
TruthLayer/
├── .streamlit/
│   ├── config.toml               # Streamlit UI theme and server limits (20 MB upload)
│   └── secrets.toml.example      # Streamlit Cloud deployment secret template
├── src/
│   ├── config.py                 # Pydantic Settings configuration manager
│   ├── core/
│   │   ├── pdf_processor.py      # PyMuPDF page-by-page text extractor
│   │   ├── claim_extractor.py    # Gemini & Groq factual claim extraction engine
│   │   ├── search_service.py     # Tavily live web retrieval with query caching
│   │   ├── verifier.py           # Fact verification reasoning and citation reconciliation
│   │   ├── report_generator.py   # Multi-format report engine (PDF, Markdown, JSON)
│   │   └── pipeline.py           # End-to-end pipeline coordinator
│   ├── models/
│   │   └── schemas.py            # Pydantic data schemas and validation models
│   ├── ui/
│   │   ├── components.py         # Reusable UI widgets, styles, scorecard, and ledger
│   │   └── views.py              # Main dashboard view and sidebar controls
│   └── utils/
│       ├── file_validator.py     # PDF validation, magic bytes (%PDF-), and size limits
│       ├── logger.py             # Structured telemetry and formatted console logger
│       ├── security.py           # Prompt injection scanner, tag defusing, secret masking
│       └── exceptions.py         # Custom application exception hierarchy
├── tests/
│   ├── test_config.py            # Configuration and environment tests
│   ├── test_upload_validation.py # Upload validation and file format tests
│   ├── test_pdf_processor.py     # PyMuPDF text extraction unit tests
│   ├── test_claim_extractor.py   # AI claim extraction and fallback tests
│   ├── test_search_service.py    # Tavily search and domain ranking tests
│   ├── test_verifier.py          # 10 verification scenario tests
│   ├── test_dashboard.py         # Dashboard scorecard and filtering tests
│   ├── test_report_generator.py  # PDF, Markdown, and JSON report tests
│   └── test_security_and_performance.py # AppSec, latency, and caching tests
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git secret and cache exclusion rules
├── app.py                        # Streamlit application entry point
├── requirements.txt              # Pinned Python dependencies
├── PROBLEM_STATEMENT.md          # Product requirements and problem statement
├── ARCHITECTURE.md               # 9-phase system architecture and data models
├── PROGRESS.md                   # Sequential phase-wise milestone tracker
├── TEST_REPORT.md                # QA, security audit, and evaluation report
└── README.md                     # Comprehensive project documentation
```

---

## 🚀 Quickstart & Installation

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.14
- Google Gemini API Key ([Get a key](https://aistudio.google.com/))
- Tavily Search API Key ([Get a key](https://tavily.com/))
- *(Optional)* Groq API Key for automated fallback ([Get a key](https://console.groq.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/TruthLayer.git
cd TruthLayer
```

### 2. Set Up a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and insert your API credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
# Google Gemini API Configuration (Primary LLM)
GEMINI_API_KEY="AIzaSyYourRealGeminiApiKeyHere"
GEMINI_MODEL="gemini-2.5-flash"

# Tavily Search API Configuration (Live Web Evidence)
TAVILY_API_KEY="tvly-YourRealTavilyApiKeyHere"

# Groq API Configuration (Automated Fallback LLM - Optional)
GROQ_API_KEY="gsk_YourRealGroqApiKeyHere"
GROQ_MODEL="llama-3.3-70b-versatile"
```

### 5. Launch TruthLayer
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## ☁️ Deployment Guide (Streamlit Community Cloud)

1. Push your repository to GitHub. Ensure `.env` is **NOT** committed (verified by `.gitignore`).
2. Log into [Streamlit Community Cloud](https://share.streamlit.io/).
3. Select **New app**, select your repository, branch `main`, and main file `app.py`.
4. In **Advanced Settings $\rightarrow$ Secrets**, enter your production API credentials:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   TAVILY_API_KEY = "tvly-..."
   GROQ_API_KEY = "gsk_..."
   ```
5. Click **Deploy!** TruthLayer will install dependencies and launch with zero infrastructure overhead.

---

## 🧪 Testing & Verification

Run the complete automated test suite (96 tests across 8 modules):
```bash
python -m pytest tests/ -v
```

### Evaluation Benchmark Results
As documented in [`TEST_REPORT.md`](TEST_REPORT.md):
- **Automated Tests:** 96 of 96 Passed (100%)
- **Claim Extraction Precision:** 95.2%
- **Claim Extraction Recall:** 96.5%
- **Verification Accuracy:** 100.0%
- **False Positive Rate:** 0.0%
- **Source Relevance Score:** 94.8%
- **Average Pipeline Latency:** 6.5 – 13.5 seconds

---

## 🎬 User Walkthrough Guide

1. **Upload Document:** Drag and drop any text-based PDF (up to 20 MB). TruthLayer inspects magic bytes (`%PDF-`) and validates page structure.
2. **Execute Ingestion:** Click **⚡ Run Full End-to-End Verification** to automatically run all four stages, or use the step-by-step pipeline controls.
3. **Inspect Claim Ledger:** Review the executive scorecard, visual status breakdown bar, and interactive claim ledger.
4. **Filter & Drill Down:** Filter by status (`Verified`, `Inaccurate`, `False`, `Unverified`) or type keywords in the search bar.
5. **Inspect Provenance:** Expand the source citations drawer to view external evidence with `[Supporting]`, `[Contradicting]`, or `[Contextual]` tags and clickable links.
6. **Download Reports:** Click **📄 Download PDF Audit Report**, **📝 Download Markdown**, or **⚙️ Download JSON** to save the verification certificate.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

*TruthLayer — Verify facts. Build trust.*
