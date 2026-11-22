# 🛡️ TruthLayer

> **Verify what's inside your documents.**  
> An executive AI-powered PDF fact-checking platform that ingests business documents, extracts empirical assertions, cross-references live web evidence in real-time with parallel retrieval, and generates verifiable audit reports with traceable provenance.

[![Next.js](https://img.shields.io/badge/Next.js-14.2%20App%20Router-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20GenAI-gemini--3.5--flash--lite-4285F4.svg)](https://ai.google.dev/)
[![Tavily Search](https://img.shields.io/badge/Tavily%20Search%20API-live%20web-green.svg)](https://tavily.com/)
[![Groq Fallback](https://img.shields.io/badge/Groq%20Fallback-qwen--27b-F55036.svg)](https://groq.com/)
[![Test Suite](https://img.shields.io/badge/Tests-96%20Passed%20(100%25)-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📌 The Problem

Marketing decks, analyst reports, whitepapers, and corporate presentations are frequently published with outdated statistics, misattributed quotes, hallucinated figures, and unverified factual assertions. Verifying these claims manually requires tedious searches across disparate sources, leaving organizations vulnerable to reputational risk, compliance violations, and eroded reader trust.

## 💡 The Solution

**TruthLayer** acts as an automated, objective editorial truth layer. Upload any digitally-authored PDF document, and TruthLayer executes an end-to-end multi-agent verification pipeline that isolates discrete factual assertions, gathers live corroborating or contradicting web evidence via parallel web search, assigns transparent classification verdicts, and produces publication-ready PDF, Markdown, and JSON audit certificates.

---

## 🎨 Modern SaaS Architecture & UI/UX

TruthLayer is built as a high-performance modern web application inspired by **Perplexity**, **Linear**, and executive AI research platforms (**rundocs.ai**, **parafactai.com**, and **basebright.ai**):

* **Executive Top Navigation:** TruthLayer logo, live system health indicator, user profile badge, and smooth navigation across **Dashboard**, **Audit History**, and **Settings**.
* **Streamlined Document Upload Zone:** Soft blue-tinted dropzone with circular upload glyph, file metadata pill (format, size, pages), format badge (`PDF • Max 4.0 MB`), and dual action CTAs (`✨ Full Document Analysis` & `🔍 Step-by-Step Mode`).
* **Interactive Step-by-Step Inspection:** Walk through each verification phase individually (PyMuPDF Text Parsing $\rightarrow$ Claim Isolation $\rightarrow$ Live Web Search $\rightarrow$ AI Fact Verification $\rightarrow$ Audit Certificate).
* **Zero-Scroll Split Inspector Mode:** Dual-column review layout where the left column displays a compact scrollable claims feed and the right column stays fixed to inspect the active claim's evaluation, confidence score, verified corrections, and primary source citations without page scrolling.
* **3 Switchable View Modes:**
  1. `◫ Split Inspector`: Side-by-side claim feed and detailed inspection panel.
  2. `≡ Compact List`: High-density single-line accordion rows with "Expand All" / "Collapse All" controls.
  3. `▢ Cards`: Classic full-width cards.
* **Credibility Scorecard & Breakdown:**
  - **Document Credibility Score Gauge:** Dynamic overall credibility percentage (`85% High Credibility`) with color-coded gauge.
  - **Metric Summary Cards:** Total Claims, Verified (green), Inaccurate (amber), False (red), and Unverified (grey).
  - **Claims Accuracy Distribution Bar:** Proportional distribution bar and interactive status filters.
* **One-Click Export Suite:** Instant downloads for PDF Audit Reports (ReportLab `NumberedCanvas`), Markdown summaries (`.md`), and JSON audit data certificates (`.json`).

---

## 🏗️ Architecture & Pipeline Flow

TruthLayer uses a modern decoupled architecture: **Next.js 14 App Router** (React 18, TypeScript, Tailwind CSS) for the presentation layer and **FastAPI** (`api/index.py`) for the backend AI verification engine.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NEXT.JS 14 FRONTEND                             │
│   React 18, TypeScript, Tailwind CSS, Lucide Icons                     │
│   (Dropzone, Stepper, Split Inspector, Scorecard, Export Suite)        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Proxied via /api/py/*
┌───────────────────────────────────▼────────────────────────────────────┐
│                        FASTAPI REST BACKEND                            │
│   Python 3.10 - 3.14 (api/index.py)                                   │
└───────────────┬───────────────────┬───────────────────┬────────────────┘
                │ 1. Extract Text   │ 2. Extract Claims │ 3. Retrieve Evidence (Parallel)
┌───────────────▼──────────┐ ┌──────▼─────────────┐ ┌───▼────────────────┐
│   PDF Extraction Module  │ │  Claim Extraction  │ │   Search Retrieval  │
│      (PyMuPDF / fitz)    │ │   (Gemini 3.5 Lite)│ │  (Tavily Basic +   │
│                          │ │  + Groq Fallback   │ │   Query Cache)     │
└──────────────────────────┘ └────────────────────┘ └───┬────────────────┘
                                                        │ 4. Synthesize Reasoning
                                             ┌──────────▼────────────────┐
                                             │    Verification Engine    │
                                             │ (Gemini 3.5 Lite / Flash  │
                                             │     + Groq Fallback)      │
                                             └──────────┬────────────────┘
                                                        │ 5. Generate Audit
                                             ┌──────────▼────────────────┐
                                             │     Report Generator      │
                                             │    (PDF / MD / JSON)      │
                                             └───────────────────────────┘
```

---

## 🎯 Standardized Verification Status Taxonomy

| Status | Badge | Description | Required Output |
| :--- | :---: | :--- | :--- |
| **`VERIFIED`** | 🟢 | Reliable public web evidence sufficiently corroborates the claim. | Verified sources and reasoning. |
| **`INACCURATE`** | 🟠 | The claim has factual basis, but specific metrics, percentages, dates, or context are inaccurate or outdated. | **Mandatory Verified Correction** + sources. |
| **`FALSE`** | 🔴 | Reliable public evidence directly contradicts the assertion (e.g. fabricated facts, wrong entities). | **Mandatory Verified Correction** + refuting sources. |
| **`UNVERIFIED`** | ⚪ | Available public evidence is insufficient, ambiguous, or absent. | Conservative fallback (**Confidence: 0.0%**; missing evidence is never proof of falsity). |

---

## 📂 Project Structure

```
TruthLayer/
├── api/
│   └── index.py                  # FastAPI REST backend (routes for Next.js / Vercel)
├── app/
│   ├── layout.tsx                # Next.js root layout with typography and metadata
│   ├── globals.css               # Tailwind CSS and sleek custom scrollbars
│   └── page.tsx                  # Next.js main dashboard (dual modes & export)
├── components/
│   ├── Navbar.tsx                # Header navigation and API health status pill
│   ├── Dropzone.tsx              # Centered upload dropzone with dual action CTAs
│   ├── HowItWorks.tsx            # 4-stage pipeline explainer cards
│   ├── Stepper.tsx               # Real 6-stage verification progress tracker
│   ├── Scorecard.tsx             # Credibility gauge, metric cards & breakdown bar
│   ├── ClaimCard.tsx             # Expandable claim card with diff correction
│   ├── ClaimsViewer.tsx          # Zero-scroll Split Inspector & high-density views
│   └── StepByStepAnalysis.tsx    # Interactive step-by-step verification explorer
├── types/
│   └── index.ts                  # Shared TypeScript interfaces & API schemas
├── src/
│   ├── config.py                 # Pydantic Settings configuration manager
│   ├── core/
│   │   ├── pdf_processor.py      # PyMuPDF page-by-page text extractor
│   │   ├── claim_extractor.py    # Gemini 3.5 Flash Lite & Groq claim extractor
│   │   ├── search_service.py     # Tavily live web retrieval with query caching
│   │   ├── verifier.py           # Fact verification reasoning and citation reconciliation
│   │   ├── report_generator.py   # Multi-format report engine (PDF, Markdown, JSON)
│   │   └── pipeline.py           # Synchronous pipeline coordinator
│   ├── models/
│   │   └── schemas.py            # Pydantic data schemas and validation models
│   ├── ui/                       # Optional Streamlit legacy UI components
│   └── utils/
│       ├── file_validator.py     # PDF validation, magic bytes (%PDF-), and size limits
│       ├── logger.py             # Structured telemetry and formatted console logger
│       ├── security.py           # Prompt injection scanner, tag defusing, secret masking
│       └── exceptions.py         # Custom application exception hierarchy
├── tests/                        # 96 unit, integration, and security tests
├── public/                       # Static public assets
├── .env.example                  # Environment configuration template
├── .gitignore                    # Secrets, node_modules, and cache exclusion rules
├── package.json                  # Next.js & React dependencies
├── next.config.mjs               # Next.js config with FastAPI rewrites
├── tailwind.config.js            # Tailwind CSS styling configuration
├── tsconfig.json                 # TypeScript compiler configuration
├── vercel.json                   # Vercel serverless deployment routing
├── requirements.txt              # Python dependencies
└── README.md                     # Comprehensive project documentation
```

---

## 🚀 Quickstart & Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.10, 3.11, 3.12, or 3.14
- Google Gemini API Key ([Get a key](https://aistudio.google.com/))
- Tavily Search API Key ([Get a key](https://tavily.com/))
- *(Optional)* Groq API Key for automated fallback ([Get a key](https://console.groq.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/Himanshukla23/TruthLayer.git
cd TruthLayer
```

### 2. Set Up Python Backend Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# Install Python requirements
pip install -r requirements.txt
```

### 3. Install Node.js Frontend Dependencies
```bash
npm install
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and insert your API credentials:
```bash
cp .env.example .env
```

Edit `.env`:
```ini
# Google Gemini API Configuration (Primary LLM)
GEMINI_API_KEY="your-gemini-api-key"
GEMINI_MODEL="gemini-3.5-flash-lite"

# Tavily Search API Configuration (Live Web Evidence)
TAVILY_API_KEY="tvly-your-tavily-api-key"

# Groq API Configuration (Automated Fallback LLM)
GROQ_API_KEY="gsk_your-groq-api-key"
GROQ_MODEL="qwen/qwen3.8-27b"
```

### 5. Launch the Application

In terminal 1, start the FastAPI backend:
```bash
python -m uvicorn api.index:app --host 127.0.0.1 --port 8000
```

In terminal 2, start the Next.js frontend:
```bash
npm run dev
```

Open your browser at **`http://localhost:3000`**.

---

## 🧪 Testing & Verification

Run the complete automated test suite (96 tests across 8 modules):
```bash
python -m pytest tests/ -v
```

All 96 unit and security tests pass with 100% test coverage over file validation, claim isolation, live search query formulation, evidence ranking, and ReportLab PDF generation.

---

## ☁️ Deployment Guide (Vercel)

TruthLayer is configured for zero-config deployment on Vercel:
1. Push your repository to GitHub. Ensure `.env` is **NOT** committed (enforced by `.gitignore`).
2. Import the project in [Vercel](https://vercel.com/).
3. In the project settings, add your Environment Variables:
   - `GEMINI_API_KEY`
   - `TAVILY_API_KEY`
   - `GROQ_API_KEY`
4. Click **Deploy**. Vercel will build the Next.js frontend and host `api/index.py` as a serverless Python function.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

*TruthLayer — Verify what's inside your documents.*
