"""Dashboard and upload views for TruthLayer's Streamlit frontend."""

import streamlit as st
from typing import Optional
from src.config import get_settings
from src.utils.logger import get_logger
from src.utils.file_validator import validate_uploaded_pdf, FileValidationResult
from src.core.pdf_processor import extract_text_from_pdf
from src.core.claim_extractor import extract_claims_from_document
from src.core.search_service import search_evidence_for_document
from src.core.verifier import verify_claims_for_document
from src.core.pipeline import run_full_pipeline
from src.models.schemas import (
    PDFExtractionResult,
    ClaimExtractionResponse,
    DocumentEvidenceResult,
    VerificationReport,
)
from src.ui.components import (
    inject_custom_styles,
    render_brand_header,
    render_hero_section,
    render_feature_pillars,
    render_document_card,
    render_extraction_preview,
    render_claims_list,
    render_evidence_drawer,
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
    if "extraction_result" not in st.session_state:
        st.session_state.extraction_result = None
    if "claims_result" not in st.session_state:
        st.session_state.claims_result = None
    if "evidence_result" not in st.session_state:
        st.session_state.evidence_result = None
    if "verification_report" not in st.session_state:
        st.session_state.verification_report = None
    if "fact_check_triggered" not in st.session_state:
        st.session_state.fact_check_triggered = False


def reset_uploaded_file() -> None:
    """Clear the currently uploaded file and reset application state."""
    st.session_state.uploaded_file_bytes = None
    st.session_state.uploaded_file_name = None
    st.session_state.validation_result = None
    st.session_state.extraction_result = None
    st.session_state.claims_result = None
    st.session_state.evidence_result = None
    st.session_state.verification_report = None
    st.session_state.fact_check_triggered = False
    logger.info("Uploaded document cleared by user.")


def render_upload_dashboard() -> None:
    """Render the complete SaaS upload dashboard with Phase 6 Fact Verification Engine."""
    init_session_state()
    settings = get_settings()

    # Inject SaaS CSS Styles
    inject_custom_styles()

    # Render Header & Hero Section
    render_brand_header()
    render_hero_section()

    # Render Core Value Propositions
    render_feature_pillars()

    st.write("")
    st.write("")

    # Main Upload Section
    st.subheader("Document Ingestion & Verification Pipeline")
    st.caption("Upload a marketing report, presentation, or whitepaper in PDF format.")

    # Upload Container Card
    upload_col, info_col = st.columns([7, 3])

    with upload_col:
        # File uploader widget accepting strictly PDF files
        uploaded_file = st.file_uploader(
            label="Upload PDF Document",
            type=["pdf"],
            accept_multiple_files=False,
            help=f"Select or drag-and-drop a PDF file up to {settings.max_upload_size_mb} MB.",
            key="pdf_uploader",
        )

        # Handle file upload event
        if uploaded_file is not None:
            if (
                st.session_state.uploaded_file_name != uploaded_file.name
                or st.session_state.uploaded_file_bytes is None
            ):
                file_bytes = uploaded_file.getvalue()
                logger.info(f"File uploaded: {uploaded_file.name} ({len(file_bytes)} bytes)")

                # Execute File Validation
                val_result: FileValidationResult = validate_uploaded_pdf(
                    file_name=uploaded_file.name,
                    file_bytes=file_bytes,
                    max_size_mb=settings.max_upload_size_mb,
                )

                st.session_state.uploaded_file_bytes = file_bytes
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.validation_result = val_result
                st.session_state.extraction_result = None
                st.session_state.claims_result = None
                st.session_state.evidence_result = None
                st.session_state.verification_report = None
                st.session_state.fact_check_triggered = False

        # Render Validation Results and Action Options
        val_result = st.session_state.validation_result
        if val_result is not None:
            if not val_result.is_valid:
                # Validation Failure Alert
                st.error(f"❌ **Validation Failed:** {val_result.error_message}")
                if st.button("🔄 Try Another Document", key="btn_clear_invalid"):
                    reset_uploaded_file()
                    st.rerun()
            else:
                # Validation Passed: Render Document Information Card
                render_document_card(
                    file_name=val_result.file_name,
                    formatted_size=val_result.formatted_size,
                    page_count=val_result.page_count,
                )

                # Quick Full Pipeline Action + Remove
                action_col1, action_col2 = st.columns([3, 1])
                with action_col1:
                    full_pipeline_btn = st.button(
                        "⚡ Run Full End-to-End Verification",
                        type="primary",
                        use_container_width=True,
                        key="btn_run_full_pipeline",
                    )
                    if full_pipeline_btn:
                        p_bar = st.progress(0)
                        p_status = st.empty()

                        def update_full_pipe(stage_msg, progress_val):
                            p_bar.progress(progress_val)
                            p_status.markdown(f"**{stage_msg}**")

                        with st.spinner("Executing end-to-end TruthLayer verification..."):
                            report = run_full_pipeline(
                                file_name=val_result.file_name,
                                file_bytes=st.session_state.uploaded_file_bytes,
                                settings=settings,
                                progress_callback=update_full_pipe,
                            )
                            st.session_state.verification_report = report
                            p_status.empty()
                            p_bar.empty()

                with action_col2:
                    if st.button("🗑️ Remove File", use_container_width=True, key="btn_remove_file"):
                        reset_uploaded_file()
                        st.rerun()

                st.write("")
                st.markdown("#### Step-by-Step Pipeline Controls")

                # Step 1: Text Extraction
                step1_col, _ = st.columns([3, 1])
                with step1_col:
                    extract_btn = st.button(
                        "📄 Step 1: Extract Document Text",
                        use_container_width=True,
                        key="btn_extract_text",
                    )
                    if extract_btn:
                        st.session_state.fact_check_triggered = True
                        with st.spinner("Extracting text page-by-page with PyMuPDF..."):
                            extraction_result = extract_text_from_pdf(
                                file_name=val_result.file_name,
                                file_bytes=st.session_state.uploaded_file_bytes,
                                max_pages=settings.max_pdf_pages,
                            )
                            st.session_state.extraction_result = extraction_result
                            st.session_state.claims_result = None
                            st.session_state.evidence_result = None
                            st.session_state.verification_report = None

                # Render Extraction Results
                extraction_result = st.session_state.extraction_result
                if extraction_result is not None:
                    if extraction_result.is_scanned_document:
                        st.warning(f"⚠️ **Scanned Document Detected:** {extraction_result.error_message}")
                    elif extraction_result.extraction_status == "empty":
                        st.warning(f"⚠️ **Empty Document:** {extraction_result.error_message}")
                    elif extraction_result.extraction_status == "failed":
                        st.error(f"❌ **Extraction Error:** {extraction_result.error_message}")
                    else:
                        render_extraction_preview(extraction_result)

                        # Step 2: AI Claim Extraction
                        st.write("")
                        st.markdown("---")
                        step2_col, _ = st.columns([3, 1])
                        with step2_col:
                            extract_claims_btn = st.button(
                                "🤖 Step 2: Extract Factual Claims with AI",
                                use_container_width=True,
                                key="btn_extract_claims",
                            )
                            if extract_claims_btn:
                                with st.spinner("Analyzing document text with Gemini (Groq fallback)..."):
                                    claims_res = extract_claims_from_document(
                                        extraction_result=extraction_result,
                                        settings=settings,
                                    )
                                    st.session_state.claims_result = claims_res
                                    st.session_state.evidence_result = None
                                    st.session_state.verification_report = None

                        # Render Claims Results
                        claims_result = st.session_state.claims_result
                        if claims_result is not None:
                            if claims_result.error_message:
                                st.error(f"❌ **Claim Extraction Error:** {claims_result.error_message}")
                            else:
                                render_claims_list(claims_result)

                                # Step 3: Live Web Research
                                if claims_result.total_claims > 0:
                                    st.write("")
                                    st.markdown("---")
                                    step3_col, _ = st.columns([3, 1])
                                    with step3_col:
                                        research_btn = st.button(
                                            "🌐 Step 3: Research Claims on Live Web (Tavily)",
                                            use_container_width=True,
                                            key="btn_research_claims",
                                        )
                                        if research_btn:
                                            progress_bar = st.progress(0)
                                            status_text = st.empty()

                                            def update_progress(curr, total, claim_text):
                                                pct = curr / total
                                                progress_bar.progress(pct)
                                                status_text.markdown(
                                                    f"Searching evidence for claim **{curr}/{total}**: *\"{claim_text[:60]}...\"*"
                                                )

                                            with st.spinner("Querying Tavily Search API for live web evidence..."):
                                                evidence_res = search_evidence_for_document(
                                                    claims_response=claims_result,
                                                    settings=settings,
                                                    progress_callback=update_progress,
                                                )
                                                st.session_state.evidence_result = evidence_res
                                                st.session_state.verification_report = None
                                                status_text.empty()
                                                progress_bar.empty()

                                    # Render Evidence Results
                                    evidence_result = st.session_state.evidence_result
                                    if evidence_result is not None:
                                        if evidence_result.error_message:
                                            st.error(f"❌ **Search Retrieval Error:** {evidence_result.error_message}")
                                        else:
                                            render_evidence_drawer(evidence_result)

                                            # Step 4: Fact Verification Engine
                                            st.write("")
                                            st.markdown("---")
                                            step4_col, _ = st.columns([3, 1])
                                            with step4_col:
                                                verify_btn = st.button(
                                                    "⚖️ Step 4: Run Fact Verification Engine",
                                                    type="primary",
                                                    use_container_width=True,
                                                    key="btn_verify_claims",
                                                )
                                                if verify_btn:
                                                    v_bar = st.progress(0)
                                                    v_status = st.empty()

                                                    def update_v_progress(curr, total, claim_text):
                                                        v_bar.progress(curr / total)
                                                        v_status.markdown(
                                                            f"Verifying claim **{curr}/{total}**: *\"{claim_text[:60]}...\"*"
                                                        )

                                                    with st.spinner("Reasoning over evidence with Gemini (Groq fallback)..."):
                                                        report = verify_claims_for_document(
                                                            claims_response=claims_result,
                                                            evidence_doc=evidence_result,
                                                            settings=settings,
                                                            progress_callback=update_v_progress,
                                                        )
                                                        st.session_state.verification_report = report
                                                        v_status.empty()
                                                        v_bar.empty()

                # Render Final Verification Results
                v_report = st.session_state.verification_report
                if v_report is not None:
                    st.write("")
                    st.markdown("---")
                    render_verification_results(v_report)
        else:
            st.info(
                f"Drag and drop your PDF here, or click **Browse files**. Supported format: **.pdf** (up to {settings.max_upload_size_mb} MB)."
            )

    with info_col:
        st.markdown("#### Document Guidelines")
        st.markdown(
            """
            * **Format:** Digitally authored text-based PDFs.
            * **Max Size:** 20 MB per file.
            * **Page Guidance:** 1 to 10 pages recommended for fastest verification.
            * **Privacy Guarantee:** Uploads are processed purely in-memory. Documents are never permanently stored.
            """
        )

    # Render Sidebar Context
    render_sidebar(settings)


def render_sidebar(settings) -> None:
    """Render application sidebar with system status and phase roadmap."""
    with st.sidebar:
        st.header("TruthLayer Control")
        st.markdown("**Current Phase:** Phase 9 (Production Ready)")
        st.markdown("**Status:** Verified & Deployment Ready")

        st.divider()

        st.markdown("### Integration Readiness")
        if settings.is_gemini_configured:
            st.success(f"✅ **Gemini:** `{settings.gemini_model}`")
        else:
            st.warning("⏳ **Gemini:** Not configured")

        if settings.is_groq_configured:
            st.success(f"✅ **Groq:** `{settings.groq_model}`")
        else:
            st.info("ℹ️ **Groq:** Fallback available")

        if settings.is_tavily_configured:
            st.success("✅ **Tavily Search API:** Configured")
        else:
            st.warning("⏳ **Tavily Search API:** Not configured")

        st.divider()

        st.markdown("### Sequential Roadmap")
        st.markdown("✅ **Phase 1:** Project Foundation")
        st.markdown("✅ **Phase 2:** Frontend & PDF Upload")
        st.markdown("✅ **Phase 3:** PDF Text Extraction")
        st.markdown("✅ **Phase 4:** AI Claim Extraction")
        st.markdown("✅ **Phase 5:** Live Web Search")
        st.markdown("✅ **Phase 6:** Fact Verification Engine")
        st.markdown("✅ **Phase 7:** Results Dashboard & Reports")
        st.markdown("✅ **Phase 8:** Security & Optimization")
        st.markdown("✅ **Phase 9:** Deployment & Submission")
