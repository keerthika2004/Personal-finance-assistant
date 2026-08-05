import streamlit as st
from frontend.utils.api_client import APIClient


def render_uploader_view():
    st.header("📄 Upload Bank Statements")
    st.markdown("Upload your bank statement PDF, CSV, or Image (PNG/JPG) file. The **LangGraph Reconciliation Engine** will parse, normalize, check for duplicates, and score suspicious transactions automatically.")

    uploaded_file = st.file_uploader("Choose a PDF, CSV, or Image bank statement file", type=["pdf", "csv", "png", "jpg", "jpeg"])

    if uploaded_file is not None:
        if st.button("🚀 Process Statement", type="primary"):
            with st.spinner("Processing statement with LangGraph Multi-Agent Engine..."):
                try:
                    file_bytes = uploaded_file.getvalue()
                    res = APIClient.upload_statement(file_bytes, uploaded_file.name)

                    st.success(f"✅ Statement processed successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Parsed Transactions", res.get("total_parsed", 0))
                    col2.metric("Flagged Items (HITL)", res.get("flagged_count", 0))
                    col3.metric("Status", res.get("status", "UNKNOWN"))

                    if res.get("requires_hitl"):
                        st.warning("⚠️ Suspicious or duplicate items detected! Please go to the **Review Queue (HITL)** tab to review and approve transactions.")
                    else:
                        st.info("🎉 All transactions reconciled automatically without flagged anomalies.")

                except Exception as e:
                    st.error(f"❌ Error processing statement: {str(e)}")
