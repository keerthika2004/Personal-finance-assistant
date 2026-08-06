import streamlit as st
import requests
from streamlit_lottie import st_lottie
from frontend.utils.api_client import APIClient

@st.cache_data
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

def render_chat_view():
    c_col1, c_col2 = st.columns([1, 4])
    with c_col1:
        # AI Bot Animation
        lottie_ai = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_tijmpky4.json")
        if lottie_ai:
            st_lottie(lottie_ai, height=120, key="chat_anim")
    with c_col2:
        st.header("💬 AI Financial Advisor Chat")
        st.markdown("Ask questions about your transactions, spending habits, savings goals, or budget advice powered by **Groq + LangGraph RAG Agent**.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I am your AI Financial Advisor. Ask me anything like *'How much did I spend on dining this month?'* or *'Am I on track for my savings goal?'*"}
        ]

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask a question about your personal finances...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing financial history with Groq AI..."):
                try:
                    res = APIClient.send_chat_message(user_input)
                    bot_response = res.get("response", "No response returned.")
                    st.markdown(bot_response)
                    st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
                except Exception as e:
                    err_msg = f"❌ Error communicating with AI Advisor: {str(e)}"
                    st.error(err_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
