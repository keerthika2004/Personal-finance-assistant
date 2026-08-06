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
        
        # Parse dates for accurate sorting
        df_txs["date_parsed"] = pd.to_datetime(df_txs["date"], format='mixed')
        
        # Sort by date ascending as requested
        df_txs = df_txs.sort_values(by="date_parsed", ascending=True)
        
        # Format the dataframe for display
        df_txs["Date"] = df_txs["date_parsed"].dt.strftime('%d/%m/%Y')
        df_txs["Merchant"] = df_txs["normalized_merchant"]
        df_txs["Category"] = df_txs["category"]
        
        # Format amount as raw float instead of string so it can be edited nicely
        df_txs["Amount"] = df_txs["amount"].astype(float)
        
        # Keep ID to know which row was edited
        df_txs["ID"] = df_txs["id"]
        
        # Small universal filter
        search_query = st.text_input("🔍 Search Transactions", placeholder="Filter by date, merchant, category, or amount...").strip().lower()
        
        if search_query:
            # Filter rows where any of the columns contain the search query
            mask = (
                df_txs["Date"].str.lower().str.contains(search_query) |
                df_txs["Merchant"].astype(str).str.lower().str.contains(search_query) |
                df_txs["Category"].astype(str).str.lower().str.contains(search_query) |
                df_txs["Amount"].astype(str).str.contains(search_query)
            )
            df_txs = df_txs[mask]
        
        # Reorder and filter columns
        df_display = df_txs[["ID", "Date", "Merchant", "Category", "Amount"]]
        
        st.caption(f"Showing {len(df_display)} transactions. Double-click any cell to edit it.")
        
        edited_df = st.data_editor(
            df_display, 
            use_container_width=True, 
            hide_index=True,
            key="tx_editor",
            column_config={
                "ID": None, # Hide the ID column
                "Amount": st.column_config.NumberColumn(
                    "Amount (₹)",
                    format="₹%f"
                )
            }
        )
        
        # Check if edits were made
        if st.session_state.get("tx_editor") and st.session_state["tx_editor"].get("edited_rows"):
            st.warning("You have unsaved changes.")
            if st.button("Save Changes", type="primary"):
                try:
                    for row_idx_str, modifications in st.session_state["tx_editor"]["edited_rows"].items():
                        row_idx = int(row_idx_str)
                        tx_id = df_display.iloc[row_idx]["ID"]
                        
                        updates = {}
                        if "Date" in modifications:
                            updates["date"] = modifications["Date"]
                        if "Merchant" in modifications:
                            updates["normalized_merchant"] = modifications["Merchant"]
                        if "Category" in modifications:
                            updates["category"] = modifications["Category"]
                        if "Amount" in modifications:
                            updates["amount"] = float(modifications["Amount"])
                            
                        APIClient.update_transaction(tx_id, updates)
                        
                    st.success("✅ Changes saved successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to save changes: {str(e)}")
        
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
