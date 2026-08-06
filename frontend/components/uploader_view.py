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

    st.markdown("---")
    st.subheader("✍️ Manual Entry")
    with st.expander("➕ Add Single Transaction Manually"):
        with st.form("manual_entry_form", clear_on_submit=True):
            from datetime import datetime
            
            m_date = st.date_input("Transaction Date", value=datetime.today())
            m_desc = st.text_input("Description / Merchant", placeholder="e.g. Starbucks, Salary, etc.")
            
            col1, col2 = st.columns(2)
            m_type = col1.radio("Transaction Type", ["Expense (Debit)", "Income (Credit)"])
            m_amount = col2.number_input("Amount (₹)", min_value=0.01, value=10.0, step=10.0)
            
            submitted = st.form_submit_button("Add Transaction")
            
            if submitted:
                if not m_desc:
                    st.error("Please enter a description.")
                else:
                    # Convert to negative if it's an expense
                    final_amount = m_amount if "Income" in m_type else -m_amount
                    
                    # Convert date to standard ISO format
                    # Add dummy time so it looks like what our parser typically produces
                    date_str = m_date.strftime("%Y-%m-%d %H:%M:%S")
                    
                    try:
                        res = APIClient.add_manual_transaction(
                            date=date_str,
                            description=m_desc,
                            amount=final_amount
                        )
                        st.toast("✅ Transaction successfully added and processed!", icon="✅")
                        if res.get("requires_hitl"):
                            st.toast("⚠️ This transaction was flagged. Please check the Review Queue.", icon="⚠️")
                    except Exception as e:
                        st.toast(f"❌ Error adding transaction: {str(e)}", icon="❌")
