"""TruthLayer - AI-Powered PDF Fact-Checking Application.

Main Streamlit Application Entry Point.
"""

import streamlit as st
from src.ui.views import render_upload_dashboard

# Application Page Configuration
st.set_page_config(
    page_title="TruthLayer — AI Document Fact-Checking",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    """Main application lifecycle runner."""
    render_upload_dashboard()


if __name__ == "__main__":
    main()
