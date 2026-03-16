import streamlit as st

st.title("Deep Research Agent")
st.caption("Multi-agent web research powered by Claude Sonnet · Built with LangGraph + deepagents")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Research")
    st.markdown(
        "Submit a query and watch the agent search, think, and synthesize "
        "a structured report in real time."
    )

with col2:
    st.markdown("#### Multi-agent")
    st.markdown(
        "An orchestrator delegates to specialized research sub-agents "
        "running in parallel when needed."
    )

with col3:
    st.markdown("#### Export")
    st.markdown(
        "Download the final report as Markdown, open it directly in Obsidian, "
        "or send it to Slack."
    )

st.divider()
st.page_link("pages/research.py", label="Start researching", icon=":material/science:")
