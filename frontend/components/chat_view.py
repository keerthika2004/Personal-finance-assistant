import streamlit as st
from frontend.utils.api_client import APIClient


def render_chat_view():
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
