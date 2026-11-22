"""Reusable UI components and styles for TruthLayer's modern SaaS interface.

Inspired by Perplexity, Linear, and leading AI research platforms (rundocs.ai, parafactai.com, basebright.ai).
"""

import streamlit as st
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional
from src.models.schemas import (
    PDFExtractionResult,
    ClaimExtractionResponse,
    ExtractedClaimItem,
    DocumentEvidenceResult,
    ClaimEvidenceResult,
    VerificationReport,
    ClaimVerificationResult,
    VerificationStatus,
    VerificationSourceCitation,
)
from src.core.report_generator import (
    generate_pdf_report,
    generate_markdown_report,
    generate_json_report,
)


def inject_custom_styles() -> None:
    """Inject clean, modern, high-end SaaS CSS styles with refined typography, shadows, and interactive components."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

        /* Hide Streamlit default clutter */
        #MainMenu { visibility: hidden !important; }
        footer { visibility: hidden !important; }
        header[data-testid="stHeader"] { background: rgba(255, 255, 255, 0.9) !important; backdrop-filter: blur(8px) !important; }
        .stAppDeployButton { display: none !important; }

        /* Global typography & canvas */
        html, body, [class*="css"], .stApp {
            font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            color: #0F172A !important;
            background-color: #FAFAFC !important;
        }

        /* Container width & padding */
        .block-container {
            max-width: 1120px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 4rem !important;
        }

        /* Top navbar header */
        .brand-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 0 1.25rem 0;
            border-bottom: 1px solid #E2E8F0;
            margin-bottom: 2rem;
        }
        .brand-left {
            display: flex;
            align-items: center;
            gap: 2rem;
        }
        .brand-title {
            font-size: 1.5rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.035em;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            text-decoration: none;
        }
        .brand-icon {
            width: 34px;
            height: 34px;
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
            color: white;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            box-shadow: 0 2px 6px rgba(37, 99, 235, 0.3);
        }
        .nav-links {
            display: flex;
            align-items: center;
            gap: 1.5rem;
        }
        .nav-link {
            font-size: 0.9rem;
            font-weight: 600;
            color: #64748B;
            text-decoration: none;
            transition: color 0.15s ease;
        }
        .nav-link.active {
            color: #2563EB;
        }
        .brand-right {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .status-pill-online {
            background-color: #ECFDF5;
            color: #059669;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            border: 1px solid #A7F3D0;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }
        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 9999px;
            background: #E2E8F0;
            color: #475569;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 700;
        }

        /* Hero Heading & Subtitle */
        .hero-title-area {
            text-align: center;
            max-width: 720px;
            margin: 1.5rem auto 2.5rem auto;
        }
        .main-heading {
            font-size: 2.4rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.04em;
            line-height: 1.2;
            margin-bottom: 0.75rem;
        }
        .main-heading span {
            background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .main-subtitle {
            font-size: 1.1rem;
            color: #475569;
            line-height: 1.6;
            margin: 0 auto;
        }

        /* rundocs.ai style Dropzone */
        .rundocs-dropzone {
            background: #F0F7FF;
            border: 2px dashed #BFDBFE;
            border-radius: 20px;
            padding: 3rem 2rem 2.5rem 2rem;
            text-align: center;
            transition: all 0.2s ease-in-out;
            margin-bottom: 2.5rem;
        }
        .rundocs-dropzone:hover {
            border-color: #2563EB;
            background: #EFF6FF;
            box-shadow: 0 8px 30px rgba(37, 99, 235, 0.08);
        }
        .upload-icon-circle {
            width: 56px;
            height: 56px;
            background-color: #2563EB;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.6rem;
            margin: 0 auto 1.25rem auto;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        }
        .dropzone-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 0.5rem;
        }
        .dropzone-desc {
            font-size: 0.95rem;
            color: #64748B;
            max-width: 480px;
            margin: 0 auto 1.5rem auto;
            line-height: 1.5;
        }
        .format-badge-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 1.25rem;
            font-size: 0.78rem;
            color: #64748B;
        }
        .format-pill {
            background: #DBEAFE;
            color: #1E40AF;
            padding: 0.15rem 0.6rem;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.72rem;
        }

        /* Streamlit File Uploader Makeover */
        [data-testid="stFileUploadDropzone"] {
            background-color: #FFFFFF !important;
            border: 2px dashed #93C5FD !important;
            border-radius: 16px !important;
            padding: 2rem 1.5rem !important;
            text-align: center !important;
            box-shadow: 0 4px 16px -2px rgba(37, 99, 235, 0.04) !important;
            transition: all 0.2s ease-in-out !important;
        }
        [data-testid="stFileUploadDropzone"]:hover {
            border-color: #2563EB !important;
            background-color: #F8FAFC !important;
            box-shadow: 0 6px 24px -2px rgba(37, 99, 235, 0.08) !important;
        }
        [data-testid="stFileUploadDropzone"] button {
            background: #FFFFFF !important;
            color: #1E293B !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.2rem !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
            transition: all 0.15s ease !important;
        }
        [data-testid="stFileUploadDropzone"] button:hover {
            border-color: #2563EB !important;
            color: #2563EB !important;
            background: #EFF6FF !important;
        }

        /* Primary Action Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #1E40AF 0%, #2563EB 100%) !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            padding: 0.65rem 1.5rem !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.22) !important;
            transition: all 0.15s ease-in-out !important;
        }
        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.32) !important;
            color: #FFFFFF !important;
        }
        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* Feature Cards (What happens to your documents) */
        .section-subhead {
            font-size: 0.8rem;
            font-weight: 700;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            text-align: center;
            margin-bottom: 1.25rem;
        }
        .feature-card {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 14px !important;
            padding: 1.5rem !important;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.03) !important;
            transition: all 0.2s ease-in-out !important;
            height: 100% !important;
        }
        .feature-card:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06) !important;
            border-color: #BFDBFE !important;
        }
        .feature-icon-purple {
            font-size: 1.3rem;
            margin-bottom: 0.75rem;
            background: #FAF5FF;
            color: #7E22CE;
            width: 40px;
            height: 40px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
        }
        .feature-icon-yellow {
            font-size: 1.3rem;
            margin-bottom: 0.75rem;
            background: #FEFCE8;
            color: #A16207;
            width: 40px;
            height: 40px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
        }
        .feature-icon-green {
            font-size: 1.3rem;
            margin-bottom: 0.75rem;
            background: #F0FDF4;
            color: #15803D;
            width: 40px;
            height: 40px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
        }
        .feature-icon-blue {
            font-size: 1.3rem;
            margin-bottom: 0.75rem;
            background: #EFF6FF;
            color: #2563EB;
            width: 40px;
            height: 40px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
        }
        .feature-title {
            font-size: 1.02rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 0.4rem;
        }
        .feature-text {
            font-size: 0.875rem;
            color: #64748B;
            line-height: 1.6;
        }

        /* Selected Document Card */
        .selected-doc-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.25rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }
        .selected-doc-info {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .pdf-icon-badge {
            width: 42px;
            height: 42px;
            background: #FEE2E2;
            color: #DC2626;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: 800;
        }
        .doc-title-text {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0F172A;
        }
        .doc-meta-text {
            font-size: 0.85rem;
            color: #64748B;
            margin-top: 0.15rem;
        }

        /* Metrics & Scorecards (basebright.ai style) */
        [data-testid="stMetric"] {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 14px !important;
            padding: 1.25rem 1.5rem !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03) !important;
            transition: transform 0.15s ease !important;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05) !important;
        }
        [data-testid="stMetricValue"] {
            font-size: 2.1rem !important;
            font-weight: 800 !important;
            color: #0F172A !important;
            letter-spacing: -0.04em !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            color: #64748B !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
        }

        /* Score Gauge Card (parafactai.com style) */
        .credibility-gauge-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .gauge-info {
            flex: 1;
        }
        .gauge-label {
            font-size: 0.85rem;
            font-weight: 700;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }
        .gauge-score-value {
            font-size: 2.2rem;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.04em;
        }
        .gauge-bar-container {
            width: 100%;
            height: 10px;
            background: #E2E8F0;
            border-radius: 9999px;
            overflow: hidden;
            margin-top: 0.6rem;
        }
        .gauge-bar-fill {
            height: 100%;
            border-radius: 9999px;
            transition: width 0.5s ease;
        }

        /* Visual Breakdown Bar */
        .status-breakdown-bar {
            display: flex;
            height: 14px;
            border-radius: 9999px;
            overflow: hidden;
            background: #E2E8F0;
            margin: 0.75rem 0 1rem 0;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.06);
        }
        .bar-segment-verified { background-color: #16A34A; }
        .bar-segment-inaccurate { background-color: #D97706; }
        .bar-segment-false { background-color: #DC2626; }
        .bar-segment-unverified { background-color: #94A3B8; }

        .status-legend-row {
            display: flex;
            flex-wrap: wrap;
            gap: 1.25rem;
            margin-bottom: 1.5rem;
        }
        .legend-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.85rem;
            color: #334155;
            font-weight: 600;
        }
        .legend-dot {
            width: 9px;
            height: 9px;
            border-radius: 50%;
        }

        /* Claim Cards (parafactai.com style) */
        .parafact-claim-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.5rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.02);
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .parafact-claim-card:hover {
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
            border-color: #CBD5E1;
        }
        .claim-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.85rem;
        }
        .claim-meta-badges {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .badge-page-pill {
            background: #F1F5F9;
            color: #475569;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
        }
        .badge-conf-pill {
            background: #EFF6FF;
            color: #1E40AF;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
        }
        .badge-verified {
            background-color: #DCFCE7;
            color: #15803D;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            border: 1px solid #BBF7D0;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }
        .badge-inaccurate {
            background-color: #FEF3C7;
            color: #B45309;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            border: 1px solid #FDE68A;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }
        .badge-false {
            background-color: #FEE2E2;
            color: #B91C1C;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            border: 1px solid #FECACA;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }
        .badge-unverified {
            background-color: #F1F5F9;
            color: #64748B;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            border: 1px solid #E2E8F0;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        .original-claim-text {
            font-size: 1.05rem;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.5;
            margin-bottom: 0.85rem;
        }

        /* Diff style Correction Box */
        .diff-correction-box {
            background: #FEF2F2;
            border: 1px solid #FECACA;
            border-left: 4px solid #DC2626;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin: 0.85rem 0;
            font-size: 0.9rem;
        }
        .diff-verified-box {
            background: #F0FDF4;
            border: 1px solid #BBF7D0;
            border-left: 4px solid #16A34A;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin: 0.85rem 0;
            font-size: 0.9rem;
        }
        .diff-label-stated {
            font-weight: 700;
            color: #991B1B;
            display: block;
            margin-bottom: 0.25rem;
        }
        .diff-label-fact {
            font-weight: 700;
            color: #15803D;
            display: block;
            margin-bottom: 0.25rem;
        }

        .explanation-text {
            font-size: 0.92rem;
            color: #334155;
            line-height: 1.6;
            margin-bottom: 0.85rem;
        }

        /* Evidence source box */
        .evidence-box {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin-top: 0.65rem;
            margin-bottom: 0.65rem;
        }
        .evidence-title {
            font-size: 0.92rem;
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .evidence-meta {
            font-size: 0.78rem;
            color: #64748B;
            display: flex;
            gap: 0.75rem;
            align-items: center;
            margin-bottom: 0.45rem;
        }
        .domain-pill {
            background: #EFF6FF;
            color: #1D4ED8;
            padding: 0.1rem 0.5rem;
            border-radius: 4px;
            font-weight: 600;
        }
        .evidence-snippet {
            font-size: 0.85rem;
            color: #334155;
            line-height: 1.5;
            background: #FFFFFF;
            border-left: 3px solid #CBD5E1;
            padding: 0.5rem 0.75rem;
            border-radius: 0 4px 4px 0;
        }

        /* Loading Stepper Experience */
        .stepper-container {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 2.5rem 2rem;
            margin: 2rem auto;
            max-width: 680px;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
            text-align: center;
        }
        .stepper-header {
            font-size: 1.4rem;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 0.5rem;
        }
        .stepper-desc {
            font-size: 0.95rem;
            color: #64748B;
            margin-bottom: 2rem;
        }
        .stepper-row {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            text-align: left;
            max-width: 480px;
            margin: 0 auto;
        }
        .step-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.65rem 1rem;
            border-radius: 8px;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
        }
        .step-item.active {
            background: #EFF6FF;
            border-color: #93C5FD;
        }
        .step-num {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: #CBD5E1;
            color: white;
            font-size: 0.75rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .step-item.active .step-num {
            background: #2563EB;
        }
        .step-item.completed .step-num {
            background: #16A34A;
        }
        .step-text {
            font-size: 0.9rem;
            font-weight: 600;
            color: #334155;
        }
        .step-item.active .step-text {
            color: #1E40AF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_navigation(active_tab: str = "Dashboard") -> None:
    """Render top brand identity, navigation links, and user status."""
    st.markdown(
        f"""
        <div class="brand-header">
            <div class="brand-left">
                <div class="brand-title">
                    <div class="brand-icon">🛡️</div>
                    <span>TruthLayer</span>
                </div>
            </div>
            <div class="brand-right">
                <span class="status-pill-online">● System Ready</span>
                <div class="user-avatar" title="Active Analyst Account">TL</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero_heading() -> None:
    """Render the primary heading and subtitle."""
    st.markdown(
        """
        <div class="hero-title-area">
            <div class="main-heading">Verify what's inside <span>your documents.</span></div>
            <div class="main-subtitle">
                Upload a PDF and let TruthLayer identify, research and verify factual claims using reliable sources.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_how_it_works_section() -> None:
    """Render the 4-step 'How it works / What happens to your documents' cards inspired by rundocs.ai."""
    st.markdown('<div class="section-subhead">WHAT HAPPENS TO YOUR DOCUMENTS</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon-purple">📄</div>
                <div class="feature-title">Step 1: Upload PDF</div>
                <div class="feature-text">Drag & drop your marketing brief, research report or whitepaper.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon-yellow">🔍</div>
                <div class="feature-title">Step 2: Extract Claims</div>
                <div class="feature-text">AI isolates factual statements, statistics, and dates page-by-page.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon-blue">🌐</div>
                <div class="feature-title">Step 3: Web Verification</div>
                <div class="feature-text">Tavily queries live authoritative sources to collect real-time evidence.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon-green">🛡️</div>
                <div class="feature-title">Step 4: Review Analysis</div>
                <div class="feature-text">Audit transparent ratings, verified corrections, and citation provenance.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_selected_document_card(file_name: str, formatted_size: str, page_count: Optional[int] = None) -> None:
    """Render a clean card representing the selected PDF file."""
    page_info = f" • {page_count} pages" if page_count else ""
    st.markdown(
        f"""
        <div class="selected-doc-card">
            <div class="selected-doc-info">
                <div class="pdf-icon-badge">PDF</div>
                <div>
                    <div class="doc-title-text">{file_name}</div>
                    <div class="doc-meta-text">{formatted_size}{page_info} • Supported format: PDF</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_credibility_score_card(report: VerificationReport) -> None:
    """Render overall document accuracy/credibility score inspired by parafactai.com."""
    tot = max(1, report.total_claims)
    accuracy_score = int(round((report.verified_count / tot) * 100))

    if accuracy_score >= 80:
        bar_color = "#16A34A"
        grade_text = "High Credibility"
        grade_badge = '<span style="color: #16A34A; font-weight: 700; background: #DCFCE7; padding: 0.2rem 0.6rem; border-radius: 6px;">✓ High Credibility</span>'
    elif accuracy_score >= 50:
        bar_color = "#D97706"
        grade_text = "Moderate Credibility"
        grade_badge = '<span style="color: #D97706; font-weight: 700; background: #FEF3C7; padding: 0.2rem 0.6rem; border-radius: 6px;">⚠️ Needs Review</span>'
    else:
        bar_color = "#DC2626"
        grade_text = "Low Credibility"
        grade_badge = '<span style="color: #DC2626; font-weight: 700; background: #FEE2E2; padding: 0.2rem 0.6rem; border-radius: 6px;">✕ Low Credibility</span>'

    st.markdown(
        f"""
        <div class="credibility-gauge-card">
            <div class="gauge-info">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem;">
                    <div class="gauge-label">Writing & Document Credibility Score</div>
                    <div>{grade_badge}</div>
                </div>
                <div class="gauge-score-value">{accuracy_score}% <span style="font-size: 1rem; color: #64748B; font-weight: 500;">({report.verified_count} of {report.total_claims} claims verified)</span></div>
                <div class="gauge-bar-container">
                    <div class="gauge-bar-fill" style="width: {accuracy_score}%; background: {bar_color};"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_verification_results(report: VerificationReport, on_reset_callback: Optional[Callable[[], None]] = None) -> None:
    """Render executive scorecard, visual breakdown, claim verification cards, and exports."""
    date_str = (
        report.processed_at.strftime("%B %d, %Y • %H:%M UTC")
        if hasattr(report.processed_at, "strftime")
        else str(report.processed_at)
    )

    # Header with metadata & Actions
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown(f"### Analysis Overview: `{report.document_name}`")
        st.caption(f"Evaluated on {date_str} • {report.total_pages} page(s) • {report.total_claims} factual claim(s) audited.")
    with h_col2:
        if st.button("🔄 Analyze Another Document", use_container_width=True, key="btn_reset_from_results"):
            if on_reset_callback:
                on_reset_callback()
            st.rerun()

    st.write("")

    # 1. Credibility Score Card (parafactai.com)
    render_credibility_score_card(report)

    # 2. Executive Metric Scorecards (basebright.ai style)
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    with sc1:
        st.metric("Total Claims", f"{report.total_claims}")
    with sc2:
        st.metric("Verified", f"{report.verified_count}", delta="Supported" if report.verified_count > 0 else None)
    with sc3:
        st.metric("Inaccurate", f"{report.inaccurate_count}", delta="Minor discrepancy" if report.inaccurate_count > 0 else None, delta_color="inverse")
    with sc4:
        st.metric("False", f"{report.false_count}", delta="Refuted" if report.false_count > 0 else None, delta_color="inverse")
    with sc5:
        st.metric("Unverified", f"{report.unverified_count}", delta="No web evidence" if report.unverified_count > 0 else None, delta_color="off")

    # 3. Visual Breakdown Bar
    tot = max(1, report.total_claims)
    pct_v = round((report.verified_count / tot) * 100, 1)
    pct_i = round((report.inaccurate_count / tot) * 100, 1)
    pct_f = round((report.false_count / tot) * 100, 1)
    pct_u = round((report.unverified_count / tot) * 100, 1)

    st.markdown(
        f"""
        <div class="status-breakdown-bar">
            <div class="bar-segment-verified" style="width: {pct_v}%;" title="Verified: {pct_v}%"></div>
            <div class="bar-segment-inaccurate" style="width: {pct_i}%;" title="Inaccurate: {pct_i}%"></div>
            <div class="bar-segment-false" style="width: {pct_f}%;" title="False: {pct_f}%"></div>
            <div class="bar-segment-unverified" style="width: {pct_u}%;" title="Unverified: {pct_u}%"></div>
        </div>
        <div class="status-legend-row">
            <span class="legend-chip"><span class="legend-dot" style="background: #16A34A;"></span> Verified ({report.verified_count} • {pct_v}%)</span>
            <span class="legend-chip"><span class="legend-dot" style="background: #D97706;"></span> Inaccurate ({report.inaccurate_count} • {pct_i}%)</span>
            <span class="legend-chip"><span class="legend-dot" style="background: #DC2626;"></span> False ({report.false_count} • {pct_f}%)</span>
            <span class="legend-chip"><span class="legend-dot" style="background: #94A3B8;"></span> Unverified ({report.unverified_count} • {pct_u}%)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. Export Buttons
    st.markdown("#### Document Comparison & Export")
    pdf_bytes = generate_pdf_report(report)
    md_text = generate_markdown_report(report)
    json_text = generate_json_report(report)
    clean_base_name = report.document_name.replace(".pdf", "").replace(" ", "_")

    dl_col1, dl_col2, dl_col3 = st.columns(3)
    with dl_col1:
        st.download_button(
            label="📄 Download PDF Audit Report",
            data=pdf_bytes,
            file_name=f"{clean_base_name}_verification_audit.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="btn_dl_pdf",
        )
    with dl_col2:
        st.download_button(
            label="📝 Download Markdown (.md)",
            data=md_text,
            file_name=f"{clean_base_name}_verification_report.md",
            mime="text/markdown",
            use_container_width=True,
            key="btn_dl_md",
        )
    with dl_col3:
        st.download_button(
            label="⚙️ Download JSON Certificate",
            data=json_text,
            file_name=f"{clean_base_name}_verification_data.json",
            mime="application/json",
            use_container_width=True,
            key="btn_dl_json",
        )

    st.write("")
    st.divider()

    # 5. Filter & Search Controls (parafactai.com)
    st.markdown("### Factcheck Results")
    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        status_options = [
            f"All Claims ({report.total_claims})",
            f"Verified ({report.verified_count})",
            f"Inaccurate ({report.inaccurate_count})",
            f"False ({report.false_count})",
            f"Unverified ({report.unverified_count})",
        ]
        selected_option = st.selectbox(
            "Filter by Status",
            options=status_options,
            key="results_status_filter",
        )
        status_filter = selected_option.split(" (")[0]

    with search_col:
        search_kw = st.text_input(
            "Search within extracted claims",
            placeholder="Type keyword, figure, or entity...",
            key="results_search_kw",
        )

    # Filter logic
    filtered_results = report.results
    if status_filter != "All Claims":
        filtered_results = [
            r for r in filtered_results if r.status.value.lower() == status_filter.lower()
        ]
    if search_kw.strip():
        kw = search_kw.strip().lower()
        filtered_results = [
            r for r in filtered_results
            if (
                kw in r.original_claim.lower()
                or kw in r.explanation.lower()
                or (r.corrected_information and kw in r.corrected_information.lower())
                or (r.claim_id.lower() == kw)
            )
        ]

    st.caption(f"Showing **{len(filtered_results)}** of {report.total_claims} claims:")

    if not filtered_results:
        st.info("No claims matched your current filter criteria.")
        return

    # 6. Render Individual Claim Cards (parafactai.com style)
    for item in filtered_results:
        if item.status == VerificationStatus.VERIFIED:
            status_badge = '<span class="badge-verified">✓ Verified</span>'
            border_color = "#16A34A"
        elif item.status == VerificationStatus.INACCURATE:
            status_badge = '<span class="badge-inaccurate">⚠️ Inaccurate</span>'
            border_color = "#D97706"
        elif item.status == VerificationStatus.FALSE:
            status_badge = '<span class="badge-false">✕ False</span>'
            border_color = "#DC2626"
        else:
            status_badge = '<span class="badge-unverified">? Unverified</span>'
            border_color = "#94A3B8"

        conf_pct = int(item.confidence * 100)
        conf_pill = f'<span class="badge-conf-pill">{conf_pct}% Confidence</span>' if conf_pct > 0 else '<span class="badge-conf-pill" style="background:#F1F5F9; color:#64748B;">No Web Evidence</span>'

        st.markdown(
            f"""
            <div class="parafact-claim-card" style="border-left: 4px solid {border_color};">
                <div class="claim-card-header">
                    <div class="claim-meta-badges">
                        <span class="badge-page-pill">Page {item.page_number}</span>
                        <span class="badge-page-pill">{item.claim_type}</span>
                        {conf_pill}
                    </div>
                    <div>
                        {status_badge}
                    </div>
                </div>
                <div class="original-claim-text">
                    "{item.claim_text}"
                </div>
                <div class="explanation-text">
                    <strong>Justification:</strong> {item.explanation}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Verified correction if inaccurate or false
        if item.corrected_information:
            st.markdown(
                f"""
                <div class="diff-verified-box">
                    <span class="diff-label-fact">💡 Verified Correction:</span>
                    <div>{item.corrected_information}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Supporting & Contradicting Evidence Source Accordion
        if item.sources:
            with st.expander(f"🔗 View {len(item.sources)} Verified Sources & Excerpts for {item.claim_id}"):
                for s_idx, src in enumerate(item.sources, start=1):
                    pub_info = f" • Published: {src.publication_date}" if src.publication_date else ""
                    type_label = (src.evidence_type or "Supporting").capitalize()
                    snippet_html = f'<div class="evidence-snippet">"{src.content_snippet}"</div>' if src.content_snippet else ""

                    st.markdown(
                        f"""
                        <div class="evidence-box">
                            <div class="evidence-title">
                                <a href="{src.url}" target="_blank" style="color: #2563EB; text-decoration: none; font-weight: 600;">
                                    {s_idx}. {src.title}
                                </a>
                                <span class="format-pill">{type_label}</span>
                            </div>
                            <div class="evidence-meta">
                                <span class="domain-pill">🌐 {src.source_domain}</span>
                                <span>{pub_info}</span>
                            </div>
                            {snippet_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        st.write("")
