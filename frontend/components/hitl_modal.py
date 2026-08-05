import streamlit as st
from frontend.utils.api_client import APIClient


def render_hitl_view():
    st.header("🚨 Human-in-the-Loop (HITL) Review Queue")
    st.markdown("Review transactions flagged by the **LangGraph Reconciliation Engine** for duplicates or suspicious activity before committing to the main ledger.")

    try:
        pending_items = APIClient.get_pending_hitl_items()
    except Exception as e:
        st.error(f"Failed to fetch pending review queue: {str(e)}")
        return

    if not pending_items:
        st.success("🎉 Review queue is clear! No flagged transactions waiting for approval.")
        return

    st.warning(f"⚠️ **{len(pending_items)} transaction(s)** require your review and approval.")

    for tx in pending_items:
        with st.container():
            st.markdown("---")
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                st.markdown(f"### **{tx.get('normalized_merchant') or tx.get('raw_description')}**")
                st.markdown(f"**Amount:** `₹{tx.get('amount'):,.2f}` | **Category:** `{tx.get('category')}` | **Date:** `{tx.get('date')[:10]}`")
                
                if tx.get("is_duplicate"):
                    st.error("🔁 **FLAGGED AS DUPLICATE TRANSACTION**")
                if tx.get("is_suspicious"):
                    st.error(f"⚠️ **SUSPICIOUS ACTIVITY SCORE:** `{tx.get('anomaly_score')}/100`")
                    st.info(f"**Reason:** {tx.get('anomaly_reason')}")

            with col_actions:
                st.write("")
                if st.button("✅ Approve", key=f"approve_{tx['id']}", type="primary"):
                    try:
                        APIClient.submit_hitl_decision(tx["id"], "APPROVE")
                        st.success("Approved!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

                if st.button("❌ Flag as Fraud", key=f"reject_{tx['id']}"):
                    try:
                        APIClient.submit_hitl_decision(tx["id"], "REJECT", "User marked as fraud/invalid")
                        st.warning("Rejected!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
