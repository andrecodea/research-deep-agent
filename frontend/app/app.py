"""
Deep Research Agent - Streamlit App

Structure:
- Home: landing page with project overview
- Research: I/O interface with real-time agent activity and report export
- Info: architecture diagrams, stack, and performance benchmarks
"""

import streamlit as st


def main():
    st.set_page_config(
        page_title="Deep Research Agent",
        page_icon=":material/science:",
        layout="wide",
    )

    pages = [
        st.Page("pages/home.py", title="Home", icon=":material/home:"),
        st.Page("pages/research.py", title="Research", icon=":material/science:"),
        st.Page("pages/info.py", title="Info", icon=":material/info:"),
    ]

    page = st.navigation(pages)
    page.run()

    st.sidebar.caption(
        "Built with [deepagents](https://github.com/langchain-ai/deepagents) + LangGraph. "
        "Uses [Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk) "
        "and [Space Mono](https://fonts.google.com/specimen/Space+Mono)."
    )


if __name__ == "__main__":
    main()
