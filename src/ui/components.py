"""Reusable UI components and styles for TruthLayer's SaaS interface."""

import streamlit as st
from typing import Callable, Optional
from src.models.schemas import (
    PDFExtractionResult,
    ClaimExtractionResponse,
    ExtractedClaimItem,
    DocumentEvidenceResult,
    ClaimEvidenceResult,
    VerificationReport,
    ClaimVerificationResult,
    VerificationStatus,
)
from src.core.report_generator import (
    generate_pdf_report,
    generate_markdown_report,
    generate_json_report,
)


def inject_custom_styles() -> None:
    """Inject clean, professional SaaS CSS styles for dark navy typography and subtle blue accents."""
    st.markdown(
        """
        <style>
        /* Base typography & clean background */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #0F172A;
        }

        /* Top navbar header */
        .brand-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.5rem 0 1.5rem 0;
            border-bottom: 1px solid #E2E8F0;
            margin-bottom: 2rem;
        }
        .brand-title {
            font-size: 1.85rem;
            font-weight: 700;
            color: #0F172A;
            letter-spacing: -0.025em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .brand-tagline {
            font-size: 0.95rem;
            color: #2563EB;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Hero Banner */
        .hero-section {
            background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 100%);
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: center;
        }
        .hero-heading {
            font-size: 2.1rem;
            font-weight: 800;
            color: #0F172A;
            margin-bottom: 0.75rem;
            letter-spacing: -0.03em;
        }
        .hero-description {
            font-size: 1.05rem;
            color: #475569;
            max-width: 650px;
            margin: 0 auto 1.25rem auto;
            line-height: 1.6;
        }

        /* Persona Pill Badges */
        .persona-container {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        .persona-badge {
            background-color: #EFF6FF;
            color: #1D4ED8;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.3rem 0.85rem;
            border-radius: 9999px;
            border: 1px solid #DBEAFE;
        }

        /* Document info card */
        .doc-card {
            background: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        .doc-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .doc-name {
            font-size: 1.15rem;
            font-weight: 700;
            color: #0F172A;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .doc-meta {
            font-size: 0.875rem;
            color: #64748B;
            margin-top: 0.35rem;
        }
        .status-pill-valid {
            background-color: #DCFCE7;
            color: #166534;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        /* Verification Status Badges */
        .badge-verified {
            background-color: #DCFCE7;
            color: #166534;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
            border: 1px solid #BBF7D0;
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }
        .badge-inaccurate {
            background-color: #FEF3C7;
            color: #92400E;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
            border: 1px solid #FDE68A;
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }
        .badge-false {
            background-color: #FEE2E2;
            color: #991B1B;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
            border: 1px solid #FECACA;
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }
        .badge-unverified {
            background-color: #F1F5F9;
            color: #475569;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 0.25rem 0.65rem;
            border-radius: 6px;
            border: 1px solid #E2E8F0;
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }

        /* Verification Card */
        .verify-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .verify-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.75rem;
        }
        .correction-box {
            background: #EFF6FF;
            border-left: 4px solid #2563EB;
            border-radius: 0 6px 6px 0;
            padding: 0.75rem 1rem;
            margin: 0.75rem 0;
            font-size: 0.9rem;
            color: #1E3A8A;
        }
        .explanation-text {
            font-size: 0.92rem;
            color: #334155;
            line-height: 1.6;
            margin: 0.5rem 0;
        }

        /* Evidence Card Styling */
        .evidence-box {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            padding: 0.85rem;
            margin-top: 0.65rem;
            margin-bottom: 0.65rem;
        }
        .evidence-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 0.25rem;
        }
        .evidence-meta {
            font-size: 0.78rem;
            color: #64748B;
            display: flex;
            gap: 0.65rem;
            align-items: center;
            margin-bottom: 0.45rem;
        }
        .domain-pill {
            background: #E0F2FE;
            color: #0369A1;
            padding: 0.1rem 0.45rem;
            border-radius: 4px;
            font-weight: 600;
        }
        .domain-pill-auth {
            background: #DCFCE7;
            color: #15803D;
            padding: 0.1rem 0.45rem;
            border-radius: 4px;
            font-weight: 600;
        }
        .evidence-snippet {
            font-size: 0.875rem;
            color: #334155;
            line-height: 1.5;
            background: #FFFFFF;
            border-left: 3px solid #CBD5E1;
            padding: 0.5rem 0.75rem;
            border-radius: 0 4px 4px 0;
        }
        .query-tag {
            background: #F1F5F9;
            color: #475569;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-family: monospace;
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
        .bar-segment-verified {
            background-color: #16A34A;
            transition: width 0.3s ease;
        }
        .bar-segment-inaccurate {
            background-color: #D97706;
            transition: width 0.3s ease;
        }
        .bar-segment-false {
            background-color: #DC2626;
            transition: width 0.3s ease;
        }
        .bar-segment-unverified {
            background-color: #94A3B8;
            transition: width 0.3s ease;
        }

        /* Status Legend Chips */
        .status-legend-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1.25rem;
        }
        .legend-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.8rem;
            color: #334155;
            font-weight: 500;
        }
        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
        }

        /* Evidence Type Badges */
        .type-pill-supporting {
            background-color: #DCFCE7;
            color: #166534;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.03em;
        }
        .type-pill-contradicting {
            background-color: #FEE2E2;
            color: #991B1B;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.03em;
        }
        .type-pill-contextual {
            background-color: #EFF6FF;
            color: #1D4ED8;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.03em;
        }

        /* Empty State */
        .empty-filter-card {
            background: #F8FAFC;
            border: 1px dashed #CBD5E1;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            color: #64748B;
            margin: 1.5rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header() -> None:
    """Render top brand identity and tagline."""
    st.markdown(
        """
        <div class="brand-header">
            <div class="brand-title">
                🛡️ TruthLayer
            </div>
            <div class="brand-tagline">
                Verify Facts. Build Trust.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero_section() -> None:
    """Render the hero introduction and persona badges."""
    st.markdown(
        """
        <div class="hero-section">
            <div class="hero-heading">AI-Powered PDF Fact-Checking</div>
            <div class="hero-description">
                Upload your business document, report, or whitepaper. TruthLayer extracts factual claims,
                cross-references live web evidence, and flags inaccurate or fabricated information.
            </div>
            <div class="persona-container">
                <span class="persona-badge">Marketing Professionals</span>
                <span class="persona-badge">Content Writers & Editors</span>
                <span class="persona-badge">Business Analysts</span>
                <span class="persona-badge">Researchers</span>
                <span class="persona-badge">Agencies</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_feature_pillars() -> None:
    """Render the 3 core value proposition cards."""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <div class="feature-title">Empirical Claim Parsing</div>
                <div class="feature-text">Automatically identifies numbers, statistics, historical dates, and market metrics while filtering opinions.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">🌐</div>
                <div class="feature-title">Live Web Verification</div>
                <div class="feature-text">Corroborates claims against real-time, authoritative search data to catch outdated figures and hallucinations.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📑</div>
                <div class="feature-title">Transparent Provenance</div>
                <div class="feature-text">Provides traceable evidence URLs, publication dates, and suggested corrections before you publish.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_document_card(file_name: str, formatted_size: str, page_count: Optional[int] = None) -> None:
    """Render structured details of a validated uploaded PDF."""
    page_info = f" • {page_count} pages" if page_count else ""
    st.markdown(
        f"""
        <div class="doc-card">
            <div class="doc-card-header">
                <div>
                    <div class="doc-name">📄 {file_name}</div>
                    <div class="doc-meta">File Size: {formatted_size}{page_info}</div>
                </div>
                <div class="status-pill-valid">
                    ✓ Validated PDF Document
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_extraction_preview(extraction_result: PDFExtractionResult) -> None:
    """Render page-by-page extracted text preview with stats and empty page indicators."""
    st.subheader("Extracted Document Content")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Pages", f"{extraction_result.total_pages}")
    with m2:
        st.metric("Extracted Characters", f"{extraction_result.total_characters:,}")
    with m3:
        non_empty_count = sum(1 for p in extraction_result.pages if not p.is_empty)
        st.metric("Text-Bearing Pages", f"{non_empty_count} of {extraction_result.total_pages}")

    st.write("")

    for page in extraction_result.pages:
        header = f"Page {page.page_number} ({page.character_count:,} characters)"
        if page.is_empty:
            header += " — [EMPTY PAGE]"

        with st.expander(header, expanded=(page.page_number == 1 and not page.is_empty)):
            if page.is_empty:
                st.markdown(
                    f'<div class="empty-page-alert">⚠️ Page {page.page_number}: No extractable text found on this page.</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.text_area(
                    label=f"Content for Page {page.page_number}",
                    value=page.text,
                    height=180,
                    disabled=True,
                    key=f"preview_page_{page.page_number}",
                )


def render_claims_list(claims_result: ClaimExtractionResponse) -> None:
    """Render structured cards for all extracted claims."""
    st.subheader(f"Extracted Factual Claims ({claims_result.total_claims})")
    model_badge = claims_result.extraction_model_used or "AI Model"
    st.caption(f"Identified using **{model_badge}**. All claims are isolated and ready for live web verification.")

    if claims_result.total_claims == 0:
        st.info("No factual claims were identified in this document.")
        return

    claim_types = sorted(list(set(c.claim_type for c in claims_result.claims)))
    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        selected_type = st.selectbox(
            "Filter by Claim Type",
            options=["All Types"] + claim_types,
            key="filter_claim_type",
        )
    with search_col:
        search_query = st.text_input(
            "Search within extracted claims",
            placeholder="Type keyword or number...",
            key="search_claims_query",
        )

    filtered_claims = claims_result.claims
    if selected_type != "All Types":
        filtered_claims = [c for c in filtered_claims if c.claim_type == selected_type]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_claims = [c for c in filtered_claims if q in c.original_claim.lower()]

    st.write(f"Showing **{len(filtered_claims)}** of {claims_result.total_claims} claims:")

    for claim in filtered_claims:
        entity_pills = "".join(f'<span class="pill-entity">🏷️ {e}</span>' for e in claim.entities)
        number_pills = "".join(f'<span class="pill-number">🔢 {n}</span>' for n in claim.numbers)
        date_pills = "".join(f'<span class="pill-date">📅 {d}</span>' for d in claim.dates)

        st.markdown(
            f"""
            <div class="claim-card">
                <div class="claim-header">
                    <div class="claim-badges">
                        <span class="badge-id">{claim.claim_id}</span>
                        <span class="badge-page">Page {claim.page_number}</span>
                        <span class="badge-type">{claim.claim_type}</span>
                    </div>
                </div>
                <div class="claim-body">"{claim.original_claim}"</div>
                <div class="claim-meta-row">
                    {entity_pills}
                    {number_pills}
                    {date_pills}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_evidence_drawer(evidence_result: DocumentEvidenceResult) -> None:
    """Render structured live web evidence records with clickable links and source provenance."""
    st.subheader(f"Live Web Evidence Retrieval ({evidence_result.total_sources_retrieved} Sources)")
    st.caption("Live search results retrieved via Tavily Search API. Ready for fact verification.")

    em1, em2, em3 = st.columns(3)
    with em1:
        st.metric("Researched Claims", f"{evidence_result.total_claims_researched}")
    with em2:
        st.metric("Sources Retrieved", f"{evidence_result.total_sources_retrieved}")
    with em3:
        avg_src = (
            f"{evidence_result.total_sources_retrieved / max(1, evidence_result.total_claims_researched):.1f}"
        )
        st.metric("Avg Sources / Claim", avg_src)

    st.write("")

    for claim_rec in evidence_result.claims_evidence:
        source_count = len(claim_rec.evidence)
        status_label = f"({source_count} sources)" if source_count > 0 else "— [NO SOURCES FOUND]"
        header_title = f"{claim_rec.claim_id}: \"{claim_rec.original_claim[:70]}...\" {status_label}"

        with st.expander(header_title, expanded=(source_count > 0)):
            st.markdown(f"**Target Claim:** *\"{claim_rec.original_claim}\"*")
            queries_html = " ".join(f'<span class="query-tag">🔍 {q}</span>' for q in claim_rec.search_queries)
            st.markdown(f"**Targeted Queries Executed:** {queries_html}", unsafe_allow_html=True)
            st.write("")

            if not claim_rec.evidence:
                st.warning(
                    f"⚠️ **No external web evidence found for {claim_rec.claim_id}.** "
                    "This claim will conservatively default to `Unverified` during verification reasoning."
                )
            else:
                for idx, ev in enumerate(claim_rec.evidence, start=1):
                    is_auth = (
                        any(ev.source_domain.endswith(tld) for tld in (".gov", ".edu", ".org", ".int"))
                        or ev.source_domain in ["reuters.com", "bloomberg.com", "apnews.com", "bbc.com", "wsj.com"]
                    )
                    domain_class = "domain-pill-auth" if is_auth else "domain-pill"
                    date_info = f"📅 Published: {ev.publication_date}" if ev.publication_date else "📅 Date not specified"
                    score_info = f" • Match Score: {int(ev.relevance_score * 100)}%" if ev.relevance_score else ""

                    st.markdown(
                        f"""
                        <div class="evidence-box">
                            <div class="evidence-title">
                                <a href="{ev.source_url}" target="_blank" style="color: #2563EB; text-decoration: none; font-weight: 600;">
                                    🔗 {idx}. {ev.source_title}
                                </a>
                            </div>
                            <div class="evidence-meta">
                                <span class="{domain_class}">🌐 {ev.source_domain}</span>
                                <span>{date_info}{score_info}</span>
                            </div>
                            <div class="evidence-snippet">
                                "{ev.content_snippet}"
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


def render_verification_results(report: VerificationReport) -> None:
    """Render executive scorecard, visual status breakdown, download buttons, and verified claim cards."""
    st.subheader("Document Fact-Checking Dashboard")
    date_str = (
        report.processed_at.strftime("%B %d, %Y • %H:%M UTC")
        if hasattr(report.processed_at, "strftime")
        else str(report.processed_at)
    )
    st.caption(f"Comprehensive audit for `{report.document_name}` • Evaluated on {date_str} • {report.total_claims} claim(s) analyzed.")

    # 1. Executive Scorecard Metrics
    sc1, sc2, sc3, sc4, sc5 = st.columns(5)
    with sc1:
        st.metric("Total Claims", f"{report.total_claims}")
    with sc2:
        st.metric("🟢 Verified", f"{report.verified_count}")
    with sc3:
        st.metric("🟠 Inaccurate", f"{report.inaccurate_count}")
    with sc4:
        st.metric("🔴 False", f"{report.false_count}")
    with sc5:
        st.metric("⚪ Unverified", f"{report.unverified_count}")

    # 2. Visual Breakdown Bar
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

    # 3. Downloadable Reports Section
    st.markdown("#### Export Audit Reports")
    dl_col1, dl_col2, dl_col3 = st.columns(3)

    # Pre-generate downloadable artifacts
    pdf_bytes = generate_pdf_report(report)
    md_text = generate_markdown_report(report)
    json_text = generate_json_report(report)

    clean_base_name = report.document_name.replace(".pdf", "").replace(" ", "_")

    with dl_col1:
        st.download_button(
            label="📄 Download PDF Audit Report",
            data=pdf_bytes,
            file_name=f"{clean_base_name}_verification_audit.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="btn_download_pdf",
        )
    with dl_col2:
        st.download_button(
            label="📝 Download Markdown (.md)",
            data=md_text,
            file_name=f"{clean_base_name}_verification_report.md",
            mime="text/markdown",
            use_container_width=True,
            key="btn_download_md",
        )
    with dl_col3:
        st.download_button(
            label="⚙️ Download Data Certificate (.json)",
            data=json_text,
            file_name=f"{clean_base_name}_verification_data.json",
            mime="application/json",
            use_container_width=True,
            key="btn_download_json",
        )

    st.write("")
    st.markdown("---")

    # 4. Filter Bar & Search Controls
    filter_col, search_col = st.columns([1, 2])
    with filter_col:
        status_options = [
            f"All Statuses ({report.total_claims})",
            f"Verified ({report.verified_count})",
            f"Inaccurate ({report.inaccurate_count})",
            f"False ({report.false_count})",
            f"Unverified ({report.unverified_count})",
        ]
        selected_option = st.selectbox(
            "Filter by Verification Status",
            options=status_options,
            key="verify_status_filter_selector",
        )
        # Parse status keyword from option
        status_filter = selected_option.split(" (")[0]

    with search_col:
        search_kw = st.text_input(
            "Search within verified claims or explanations",
            placeholder="Type keyword, entity, or number...",
            key="verify_search_keyword",
        )

    # Apply Filtering
    filtered_results = report.results
    if status_filter != "All Statuses":
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

    st.write(f"Displaying **{len(filtered_results)}** of {report.total_claims} claims:")

    # 5. Empty State Handling
    if not filtered_results:
        st.markdown(
            f"""
            <div class="empty-filter-card">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🔍</div>
                <div style="font-weight: 600; font-size: 1rem; color: #0F172A; margin-bottom: 0.25rem;">
                    No claims match your current filter criteria
                </div>
                <div>Filter: <code>{status_filter}</code> | Query: <code>{search_kw or 'None'}</code></div>
                <div style="margin-top: 0.5rem; font-size: 0.85rem;">
                    Try selecting "All Statuses" or clearing your search keywords.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # 6. Individual Claim Cards
    for item in filtered_results:
        # Determine badge style
        if item.status == VerificationStatus.VERIFIED:
            badge_html = '<span class="badge-verified">✓ VERIFIED</span>'
            border_color = "#16A34A"
        elif item.status == VerificationStatus.INACCURATE:
            badge_html = '<span class="badge-inaccurate">⚠️ INACCURATE</span>'
            border_color = "#D97706"
        elif item.status == VerificationStatus.FALSE:
            badge_html = '<span class="badge-false">✕ FALSE</span>'
            border_color = "#DC2626"
        else:
            badge_html = '<span class="badge-unverified">? UNVERIFIED</span>'
            border_color = "#94A3B8"

        # Confidence qualitative context
        conf_pct = int(item.confidence * 100)
        if item.confidence >= 0.90:
            conf_label = f"Confidence: {conf_pct}% (High Confidence)"
        elif item.confidence >= 0.70:
            conf_label = f"Confidence: {conf_pct}% (Moderate Confidence)"
        elif item.confidence > 0.0:
            conf_label = f"Confidence: {conf_pct}% (Low Confidence)"
        else:
            conf_label = "Confidence: 0% (No Evidence Found)"

        st.markdown(
            f"""
            <div class="verify-card" style="border-left: 4px solid {border_color};">
                <div class="verify-card-header">
                    <div>
                        <span class="badge-id">{item.claim_id}</span>
                        <span class="badge-page">Page {item.page_number}</span>
                        <span style="font-size: 0.8rem; color: #64748B; margin-left: 0.5rem;">{conf_label}</span>
                    </div>
                    <div>
                        {badge_html}
                    </div>
                </div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; margin-bottom: 0.5rem;">
                    "{item.claim_text}"
                </div>
                <div class="explanation-text">
                    <strong>Evaluation:</strong> {item.explanation}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Show correction if available
        if item.corrected_information:
            st.markdown(
                f"""
                <div class="correction-box">
                    <strong>💡 Verified Correction:</strong> {item.corrected_information}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Show evidence summary if available
        if item.evidence_summary:
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.65rem 0.85rem; font-size: 0.875rem; color: #475569; margin-bottom: 0.5rem;">
                    <strong>🔍 Evidence Summary:</strong> {item.evidence_summary}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Show verification notes if available
        if item.verification_notes:
            st.markdown(
                f"""
                <div style="background: #FFFBEB; border-left: 3px solid #F59E0B; border-radius: 0 4px 4px 0; padding: 0.5rem 0.75rem; font-size: 0.85rem; color: #92400E; margin-bottom: 0.5rem;">
                    <strong>📌 Context & Reporting Notes:</strong> {item.verification_notes}
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Citations expander
        if item.sources:
            with st.expander(f"📚 View {len(item.sources)} Corroborating Source Citations for {item.claim_id}"):
                for s_idx, src in enumerate(item.sources, start=1):
                    pub_str = f" • Published: {src.publication_date}" if src.publication_date else " • Date not specified"
                    
                    # Pill class based on evidence_type
                    ev_type = (src.evidence_type or "supporting").lower()
                    if ev_type == "supporting":
                        pill_class = "type-pill-supporting"
                        type_label = "Supporting"
                    elif ev_type == "contradicting":
                        pill_class = "type-pill-contradicting"
                        type_label = "Contradicting"
                    else:
                        pill_class = "type-pill-contextual"
                        type_label = "Contextual"

                    snippet_html = f'<div class="evidence-snippet">"{src.content_snippet}"</div>' if src.content_snippet else ""

                    st.markdown(
                        f"""
                        <div class="evidence-box">
                            <div class="evidence-title">
                                <span class="{pill_class}">{type_label}</span>
                                <a href="{src.url}" target="_blank" style="color: #2563EB; text-decoration: none; font-weight: 600; margin-left: 0.35rem;">
                                    🔗 {s_idx}. {src.title}
                                </a>
                            </div>
                            <div class="evidence-meta">
                                <span class="domain-pill">🌐 {src.source_domain}</span>
                                <span>{pub_str}</span>
                            </div>
                            {snippet_html}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        st.write("")
