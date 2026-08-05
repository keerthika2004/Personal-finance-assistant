import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from frontend.utils.api_client import APIClient


def render_dashboard_view():
    st.header("📊 Financial Intelligence Dashboard")

    try:
        data = APIClient.get_analytics_summary()
    except Exception as e:
        st.error(f"Unable to load analytics summary from backend: {str(e)}")
        return

    # Top KPI Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Income", f"₹{data.get('total_income', 0.0):,.2f}")
    col2.metric("Total Expenses", f"₹{data.get('total_expenses', 0.0):,.2f}")
    col3.metric("Net Savings", f"₹{data.get('net_savings', 0.0):,.2f}")
    col4.metric("Savings Rate", f"{data.get('savings_rate', 0.0)}%")

    st.markdown("---")

    # LLM Insights Executive Report Banner
    insights_report = data.get("insights_report")
    if insights_report:
        with st.expander("🤖 **Groq AI Financial Executive Insights**", expanded=True):
            st.info(insights_report)

    st.markdown("---")

    # Visual Charts Row
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("🍕 Category Spending Breakdown")
        cat_data = data.get("category_breakdown", {})
        if cat_data:
            df_cat = pd.DataFrame([{"Category": k, "Amount": v} for k, v in cat_data.items()])
            fig_pie = px.pie(df_cat, names="Category", values="Amount", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expense data available for category chart.")

    with chart_col2:
        st.subheader("📈 Monthly Cash Flow Trend")
        monthly_data = data.get("monthly_trend", {})
        if monthly_data:
            df_monthly = []
            for month, vals in monthly_data.items():
                df_monthly.append({"Month": month, "Type": "Income", "Amount": vals["income"]})
                df_monthly.append({"Month": month, "Type": "Expenses", "Amount": vals["expenses"]})
            df_m = pd.DataFrame(df_monthly)
            fig_line = px.bar(df_m, x="Month", y="Amount", color="Type", barmode="group", color_discrete_map={"Income": "#2ecc71", "Expenses": "#e74c3c"})
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No monthly trend data available.")

    st.markdown("---")

    # Financial Goals Tracker Section
    st.subheader("🎯 Financial Savings Goals")
    
    # Goal Creation Form
    with st.expander("➕ Create New Financial Goal"):
        with st.form("create_goal_form"):
            g_name = st.text_input("Goal Name", placeholder="e.g. Emergency Fund")
            g_target = st.number_input("Target Amount (₹)", min_value=100.0, value=1000.0, step=100.0)
            g_current = st.number_input("Current Saved (₹)", min_value=0.0, value=250.0, step=50.0)
            submitted = st.form_submit_button("Save Goal")
            if submitted and g_name:
                try:
                    APIClient.create_goal(g_name, g_target, g_current)
                    st.success(f"Goal '{g_name}' created!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error creating goal: {ex}")

    goals = data.get("goals", [])
    if goals:
        for g in goals:
            target = float(g.get("target_amount", 1.0))
            current = float(g.get("current_amount", 0.0))
            pct = min(current / target * 100, 100.0) if target > 0 else 0.0
            
            st.write(f"**{g.get('goal_name')}** — `₹{current:,.2f}` / `₹{target:,.2f}` ({pct:.1f}%)")
            st.progress(pct / 100.0)
    else:
        st.info("No active savings goals. Create one above!")
