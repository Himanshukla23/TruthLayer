"""Dashboard and upload views for TruthLayer's modern SaaS frontend."""

import streamlit as st
from datetime import datetime, timezone
from typing import Optional
from src.config import get_settings
from src.utils.logger import get_logger
from src.utils.file_validator import validate_uploaded_pdf, FileValidationResult
from src.core.pipeline import run_full_pipeline
from src.models.schemas import VerificationReport
from src.ui.components import (
    inject_custom_styles,
    render_top_navigation,
    render_hero_heading,
    render_how_it_works_section,
    render_selected_document_card,
    render_verification_results,
)

logger = get_logger("truthlayer.ui.views")


def init_session_state() -> None:
    """Initialize Streamlit session state keys for the entire verification workflow."""
    if "uploaded_file_bytes" not in st.session_state:
        st.session_state.uploaded_file_bytes = None
    if "uploaded_file_name" not in st.session_state:
        st.session_state.uploaded_file_name = None
    if "validation_result" not in st.session_state:
        st.session_state.validation_result = None
    if "verification_report" not in st.session_state:
        st.session_state.verification_report = None
    if "is_analyzing" not in st.session_state:
        st.session_state.is_analyzing = False
    if "active_nav" not in st.session_state:
        st.session_state.active_nav = "Dashboard"
    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []


def reset_uploaded_file() -> None:
    """Clear the currently uploaded file and reset application state."""
    st.session_state.uploaded_file_bytes = None
    st.session_state.uploaded_file_name = None
    st.session_state.validation_result = None
    st.session_state.verification_report = None
    st.session_state.is_analyzing = False
    logger.info("Uploaded document cleared by user.")


def render_sidebar_navigation(settings) -> None:
    """Render modern left sidebar navigation inspired by rundocs.ai and basebright.ai."""
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 1.5rem;">
                <div style="width: 32px; height: 32px; background: #2563EB; color: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem;">🛡️</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A;">TruthLayer</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; margin-bottom: 0.5rem;'>MAIN NAVIGATION</p>", unsafe_allow_html=True)
        selected_nav = st.radio(
            label="Navigation",
            options=["Dashboard", "History", "Settings"],
            index=["Dashboard", "History", "Settings"].index(st.session_state.active_nav),
            label_visibility="collapsed",
            key="sidebar_nav_radio",
        )
        if selected_nav != st.session_state.active_nav:
            st.session_state.active_nav = selected_nav
            st.rerun()

        st.divider()

        st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; margin-bottom: 0.5rem;'>AI & SEARCH ENGINES</p>", unsafe_allow_html=True)
        if settings.is_gemini_configured:
            st.markdown(f"🟢 **Gemini AI:** `{settings.gemini_model}`")
        else:
            st.markdown("🔴 **Gemini AI:** Unconfigured")

        if settings.is_tavily_configured:
            st.markdown("🟢 **Tavily Live Web Search:** Ready")
        else:
            st.markdown("🟡 **Tavily:** Key Missing")

        if settings.is_groq_configured:
            st.markdown(f"🟢 **Groq Fallback:** `{settings.groq_model}`")

        st.divider()
        st.markdown(
            """
            <div style="font-size: 0.78rem; color: #64748B; line-height: 1.5;">
                <strong>TruthLayer v1.0 Enterprise</strong><br>
                Empirical PDF Fact-Checking & Provenance Audit
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_upload_dashboard() -> None:
    """Render the complete modern SaaS dashboard with PDF ingestion and Fact Verification."""
    init_session_state()
    settings = get_settings()

    # Inject SaaS CSS Styles
    inject_custom_styles()

    # Render Sidebar Navigation
    render_sidebar_navigation(settings)

    # Top Navigation Bar
    render_top_navigation(active_tab=st.session_state.active_nav)

    # Handle History View
    if st.session_state.active_nav == "History":
        render_history_view()
        return

    # Handle Settings View
    if st.session_state.active_nav == "Settings":
        render_settings_view(settings)
        return

    # --- MAIN DASHBOARD VIEW ---

    # If verification results are already available, display the results dashboard directly
    if st.session_state.verification_report is not None:
        render_verification_results(
            report=st.session_state.verification_report,
            on_reset_callback=reset_uploaded_file,
        )
        return

    # If currently running analysis, display the real 6-stage loading experience
    if st.session_state.is_analyzing:
        render_processing_experience(settings)
        return

    # Otherwise, display the Hero and rundocs.ai style PDF Upload Zone
    render_hero_heading()

    # Center upload container
    upload_container = st.container()
    with upload_container:
        st.markdown(
            """
            <div class="rundocs-dropzone">
                <div class="upload-icon-circle">⭳</div>
                <div class="dropzone-title">Drop PDF document here</div>
                <div class="dropzone-desc">
                    Get extracted claims, live web source corroboration, and accuracy scorecards with verifiable citations.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            label="Upload Document",
            type=["pdf"],
            accept_multiple_files=False,
            help=f"Select or drag-and-drop a PDF file up to {settings.max_upload_size_mb} MB.",
            key="saas_pdf_uploader",
            label_visibility="collapsed",
        )

        # Handle file upload event
        if uploaded_file is not None:
            if (
                st.session_state.uploaded_file_name != uploaded_file.name
                or st.session_state.uploaded_file_bytes is None
            ):
                file_bytes = uploaded_file.getvalue()
                val_result: FileValidationResult = validate_uploaded_pdf(
                    file_name=uploaded_file.name,
                    file_bytes=file_bytes,
                    max_size_mb=settings.max_upload_size_mb,
                )

                st.session_state.uploaded_file_bytes = file_bytes
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.validation_result = val_result
                st.session_state.verification_report = None
                st.session_state.is_analyzing = False

        # Render validation results & CTA
        val_result = st.session_state.validation_result
        if val_result is not None:
            if not val_result.is_valid:
                st.error(f"❌ **Upload Validation Error:** {val_result.error_message}")
                if st.button("🔄 Try Another File", key="btn_clear_val_err"):
                    reset_uploaded_file()
                    st.rerun()
            else:
                # Valid PDF selected
                render_selected_document_card(
                    file_name=val_result.file_name,
                    formatted_size=val_result.formatted_size,
                    page_count=val_result.page_count,
                )

                # Primary Action CTA Button & Remove Action
                cta_col, rm_col = st.columns([3, 1])
                with cta_col:
                    analyze_btn = st.button(
                        "✨ Analyze Document",
                        type="primary",
                        use_container_width=True,
                        key="btn_analyze_document",
                    )
                    if analyze_btn:
                        st.session_state.is_analyzing = True
                        st.rerun()

                with rm_col:
                    if st.button("🗑️ Remove File", use_container_width=True, key="btn_remove_uploaded"):
                        reset_uploaded_file()
                        st.rerun()

    st.write("")
    st.write("")

    # What happens to your documents section (rundocs.ai style)
    render_how_it_works_section()


def render_processing_experience(settings) -> None:
    """Display real 6-stage verification progress interface without fake completion."""
    file_name = st.session_state.uploaded_file_name
    file_bytes = st.session_state.uploaded_file_bytes

    st.markdown(
        f"""
        <div class="stepper-container">
            <div class="stepper-header">Auditing Factual Claims...</div>
            <div class="stepper-desc">Analyzing <strong>{file_name}</strong> across reliable live sources and AI verification engines.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prog_bar = st.progress(0.05)
    status_msg = st.empty()

    # Real stages callback
    def progress_callback(stage_text: str, progress_float: float) -> None:
        prog_bar.progress(progress_float)
        status_msg.markdown(f"**Current Stage:** `{stage_text}`")

    try:
        report = run_full_pipeline(
            file_name=file_name,
            file_bytes=file_bytes,
            settings=settings,
            progress_callback=progress_callback,
        )

        st.session_state.verification_report = report
        st.session_state.is_analyzing = False

        # Add to session history
        st.session_state.analysis_history.append(
            {
                "document_name": report.document_name,
                "timestamp": datetime.now(timezone.utc).strftime("%b %d, %Y • %H:%M UTC"),
                "total_claims": report.total_claims,
                "verified_count": report.verified_count,
                "inaccurate_count": report.inaccurate_count,
                "false_count": report.false_count,
                "unverified_count": report.unverified_count,
                "report": report,
            }
        )

        st.rerun()

    except Exception as exc:
        st.session_state.is_analyzing = False
        st.error(f"❌ **Analysis Failed:** {str(exc)}")
        if st.button("🔄 Return to Dashboard"):
            reset_uploaded_file()
            st.rerun()


def render_history_view() -> None:
    """Render audit history from current session."""
    st.markdown("### Document Audit History")
    st.caption("Review previous fact-checking reports generated during this session.")

    history = st.session_state.analysis_history
    if not history:
        st.info("No documents have been analyzed in this session yet. Upload a document on the Dashboard to get started.")
        if st.button("Go to Dashboard"):
            st.session_state.active_nav = "Dashboard"
            st.rerun()
        return

    for idx, item in enumerate(reversed(history)):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
        with c1:
            st.markdown(f"**📄 {item['document_name']}**")
            st.caption(item["timestamp"])
        with c2:
            st.markdown(f"**Claims:** {item['total_claims']}")
            st.caption(f"✓ {item['verified_count']} | ⚠️ {item['inaccurate_count']} | ✕ {item['false_count']}")
        with c3:
            tot = max(1, item["total_claims"])
            score = int((item["verified_count"] / tot) * 100)
            st.markdown(f"**Credibility:** `{score}%`")
        with c4:
            if st.button("View Report", key=f"btn_hist_view_{idx}"):
                st.session_state.verification_report = item["report"]
                st.session_state.active_nav = "Dashboard"
                st.rerun()
        st.divider()


def render_settings_view(settings) -> None:
    """Render settings and API configuration status."""
    st.markdown("### System & API Configuration")
    st.caption("Verify your connected AI models and web search credentials.")

    st.markdown("#### API Integrations")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.25rem;">
                <div style="font-weight: 700; font-size: 1.05rem; margin-bottom: 0.5rem;">Google Gemini API</div>
                <div style="color: #64748B; font-size: 0.85rem; margin-bottom: 0.75rem;">Primary reasoning model for claim extraction and factual analysis.</div>
            """,
            unsafe_allow_html=True,
        )
        if settings.is_gemini_configured:
            st.success(f"Connected: `{settings.gemini_model}`")
        else:
            st.error("Missing `GEMINI_API_KEY`")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.25rem;">
                <div style="font-weight: 700; font-size: 1.05rem; margin-bottom: 0.5rem;">Tavily Search API</div>
                <div style="color: #64748B; font-size: 0.85rem; margin-bottom: 0.75rem;">Live web search engine collecting authoritative evidence.</div>
            """,
            unsafe_allow_html=True,
        )
        if settings.is_tavily_configured:
            st.success("Connected: Active")
        else:
            st.error("Missing `TAVILY_API_KEY`")
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("#### Operational Limits")
    st.markdown(
        f"""
        * **Max File Size:** `{settings.max_upload_size_mb} MB`
        * **Max Pages Processed:** `{settings.max_pdf_pages} pages`
        * **Default Timeout:** `{settings.api_timeout_seconds}s`
        * **Groq Fallback:** `{'Enabled' if settings.is_groq_configured else 'Disabled'}`
        """
    )
