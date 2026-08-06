import streamlit as st
import pandas as pd
from frontend.utils.api_client import APIClient

def render_transaction_history_view():
    st.header("📜 Transaction History")
    
    try:
        data = APIClient.get_analytics_summary()
    except Exception as e:
        st.error(f"Unable to load transactions from backend: {str(e)}")
        return
        
    transactions = data.get("transactions", [])
    if transactions:
        df_txs = pd.DataFrame(transactions)
        
        # Format the dataframe for display
        df_txs["Date"] = pd.to_datetime(df_txs["date"]).dt.strftime('%d/%m/%Y')
        df_txs["Merchant"] = df_txs["normalized_merchant"]
        df_txs["Category"] = df_txs["category"]
        
        # Format amount as currency string for display
        df_txs["Amount"] = df_txs["amount"].apply(lambda x: f"₹{x:,.2f}")
        
        # Reorder and filter columns
        df_display = df_txs[["Date", "Merchant", "Category", "Amount"]]
        
        # Display as a dataframe with some styling
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Add deletion UI
        with st.expander("🗑️ Delete a Transaction"):
            tx_options = {f"{t['date'][:10]} | {t['normalized_merchant']} | ₹{t['amount']} | {t['category']}": t['id'] for t in transactions}
            selected_tx = st.selectbox("Select Transaction to Delete", options=list(tx_options.keys()))
            if st.button("Delete Transaction", type="primary"):
                tx_id = tx_options[selected_tx]
                try:
                    APIClient.delete_transaction(tx_id)
                    st.success("✅ Transaction deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to delete transaction: {str(e)}")
    else:
        st.info("No approved transactions found. Upload a statement or add one manually!")
