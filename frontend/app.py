import streamlit as st
from frontend.utils.api_client import APIClient
from frontend.components.dashboard_view import render_dashboard_view
from frontend.components.hitl_modal import render_hitl_view
from frontend.components.uploader_view import render_uploader_view
from frontend.components.chat_view import render_chat_view

st.set_page_config(
    page_title="Unified Financial AI Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark glassmorphism styling
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stMetric { background: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    .stAlert { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


def main():
    st.sidebar.title("💰 Financial AI Assistant")
    st.sidebar.markdown("---")

    # Backend Connection Status Badge
    is_healthy = APIClient.check_health()
    if is_healthy:
        st.sidebar.success("🟢 Backend Service: Online")
    else:
        st.sidebar.error("🔴 Backend Service: Offline / Connecting...")

    st.sidebar.markdown("---")

    # Navigation Menu
    navigation = st.sidebar.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "🚨 Review Queue (HITL)",
            "📄 Upload Statements",
            "💬 AI Advisor Chat"
        ]
    )

    st.sidebar.markdown("---")
    st.sidebar.info("Powered by **FastAPI + Streamlit + LangGraph + Groq LLM**")

    # Render selected view component
    if navigation == "📊 Dashboard":
        render_dashboard_view()
    elif navigation == "🚨 Review Queue (HITL)":
        render_hitl_view()
    elif navigation == "📄 Upload Statements":
        render_uploader_view()
    elif navigation == "💬 AI Advisor Chat":
        render_chat_view()


if __name__ == "__main__":
    main()
