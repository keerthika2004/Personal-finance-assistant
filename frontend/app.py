import streamlit as st
from frontend.utils.api_client import APIClient
from frontend.components.dashboard_view import render_dashboard_view
from frontend.components.hitl_modal import render_hitl_view
from frontend.components.uploader_view import render_uploader_view
from frontend.components.chat_view import render_chat_view
from frontend.components.transaction_history_view import render_transaction_history_view

st.set_page_config(
    page_title="Unified Financial AI Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark glassmorphism styling, typography, and animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main { 
        background: linear-gradient(135deg, #0e1117 0%, #151b23 100%); 
        animation: fadeIn 0.8s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stMetric { 
        background: rgba(31, 41, 55, 0.7); 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid rgba(55, 65, 81, 0.5); 
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3), 0 0 15px rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.3);
    }
    
    .stAlert { 
        border-radius: 8px; 
        animation: slideInRight 0.5s ease-out;
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.sidebar.title("💰 Financial AI Assistant")
    st.sidebar.markdown("---")

    # Financial Health Score
    try:
        data = APIClient.get_analytics_summary()
        # Fetch the advanced health score calculated by the backend
        health_score = data.get("health_score", 50)
        
        # Color coding based on health score
        if health_score >= 80:
            color = "#10b981" # Green
        elif health_score >= 50:
            color = "#f59e0b" # Yellow
        else:
            color = "#ef4444" # Red
            
        st.sidebar.markdown(f"""
        <div style="background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; text-align: center; margin-bottom: 10px;">
            <p style="margin: 0; font-size: 14px; color: #9ca3af;">Health Score</p>
            <h2 style="margin: 0; font-size: 36px; color: {color};">{health_score}<span style="font-size: 20px; color: #9ca3af;">/100</span></h2>
        </div>
        """, unsafe_allow_html=True)
    except Exception:
        # Fallback if backend is down
        if APIClient.check_health():
            st.sidebar.success("🟢 Backend Service: Online")
        else:
            st.sidebar.error("🔴 Backend Service: Offline")

    st.sidebar.markdown("---")

    # Navigation Menu
    navigation = st.sidebar.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "📜 Transaction History",
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
    elif navigation == "📜 Transaction History":
        render_transaction_history_view()
    elif navigation == "🚨 Review Queue (HITL)":
        render_hitl_view()
    elif navigation == "📄 Upload Statements":
        render_uploader_view()
    elif navigation == "💬 AI Advisor Chat":
        render_chat_view()


if __name__ == "__main__":
    main()

# Force streamlit reload
