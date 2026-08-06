import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
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

def render_dashboard_view():
    d_col1, d_col2 = st.columns([1, 4])
    with d_col1:
        # Finance/Wallet Animation
        lottie_anim = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_kuhijlvx.json")
        if lottie_anim:
            st_lottie(lottie_anim, height=120, key="dash_anim")
            
    with d_col2:
        st.title("📊 Financial Dashboard")
        st.markdown("Overview of your financial health, forecasts, and AI-driven insights.")

    @st.dialog("Success")
    def show_success_dialog(msg: str):
        st.write(msg)
        if st.button("Close"):
            st.rerun()


    # NLP Quick Add Section
    with st.expander("⚡ NLP Quick Add Expense (Powered by Groq)", expanded=False):
        st.markdown("Type a transaction naturally (e.g., *'Bought coffee for ₹250 today'*, *'Spent 4500 on groceries last Monday'*). The AI will extract it and run it through the reconciliation pipeline!")
        
        with st.form("nlp_quick_add_form", clear_on_submit=True):
            nlp_input = st.text_input("Transaction text:")
            if st.form_submit_button("Add Transaction"):
                if nlp_input.strip():
                    with st.spinner("Processing..."):
                        try:
                            res = APIClient.submit_chat_transaction(nlp_input)
                            if res.get("requires_hitl"):
                                show_success_dialog("⚠️ Transaction was parsed but requires manual review in the HITL Queue.")
                            else:
                                show_success_dialog("✅ Transaction added successfully!")
                        except Exception as e:
                            st.error(f"Failed to add transaction: {str(e)}")
                else:
                    st.warning("Please enter some text.")

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

    # Forecasting Section
    st.subheader("🔮 30-Day Cumulative Balance Forecast (Prophet AI)")
    st.caption("This AI model predicts your overall bank balance trend for the next 30 days based on your historical spending and income.")
    forecast_data = data.get("forecast", {})
    if forecast_data and forecast_data.get("dates"):
        df_f = pd.DataFrame({
            "Date": forecast_data["dates"],
            "Predicted": forecast_data["yhat"],
            "Lower Bound": forecast_data["yhat_lower"],
            "Upper Bound": forecast_data["yhat_upper"]
        })
        
        fig_forecast = go.Figure([
            go.Scatter(
                name='Predicted Balance',
                x=df_f['Date'],
                y=df_f['Predicted'],
                mode='lines',
                line=dict(color='rgb(31, 119, 180)'),
            ),
            go.Scatter(
                name='Upper Bound',
                x=df_f['Date'],
                y=df_f['Upper Bound'],
                mode='lines',
                marker=dict(color="#444"),
                line=dict(width=0),
                showlegend=False
            ),
            go.Scatter(
                name='Lower Bound',
                x=df_f['Date'],
                y=df_f['Lower Bound'],
                marker=dict(color="#444"),
                line=dict(width=0),
                mode='lines',
                fillcolor='rgba(68, 68, 68, 0.3)',
                fill='tonexty',
                showlegend=False
            )
        ])
        fig_forecast.update_layout(
            yaxis_title='Predicted Cumulative Balance (₹)',
            hovermode="x"
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
    else:
        st.info("Not enough historical data to generate a reliable AI forecast.")

    st.markdown("---")
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
    goal_coaching = data.get("goal_coaching", {})
    if goals:
        for g in goals:
            g_id = g.get("id")
            g_name = g.get("goal_name")
            target = float(g.get("target_amount", 1.0))
            current = float(g.get("current_amount", 0.0))
            pct = min(current / target * 100, 100.0) if target > 0 else 0.0
            
            st.write(f"**{g_name}** — `₹{current:,.2f}` / `₹{target:,.2f}` ({pct:.1f}%)")
            st.progress(pct / 100.0)
            
            # AI Coaching for this specific goal
            coaching_tip = goal_coaching.get(g_name)
            if coaching_tip:
                st.info(f"💡 **AI Tip:** {coaching_tip}")
            
            # Interactive Actions
            col1, col2 = st.columns([1, 1])
            with col1:
                with st.popover("💰 Add Funds"):
                    with st.form(key=f"add_funds_{g_id}"):
                        add_amt = st.number_input("Amount to Add (₹)", min_value=1.0, step=100.0)
                        if st.form_submit_button("Add"):
                            try:
                                APIClient.add_funds_to_goal(g_id, add_amt)
                                st.success("Funds added!")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error: {ex}")
            with col2:
                if st.button("🗑️ Delete Goal", key=f"del_goal_{g_id}"):
                    try:
                        APIClient.delete_goal(g_id)
                        st.success("Goal deleted!")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error: {ex}")
            st.write("") # Spacer
    else:
        st.info("💡 **Tip: Financial Savings Goals**\n\nGoals help you track your progress towards a financial target. If you don't have any yet, try setting one up!")
        
        scol1, scol2, scol3 = st.columns(3)
        with scol1:
            st.markdown("🚗 **New Car**\n\n*Target: ₹500,000*")
        with scol2:
            st.markdown("✈️ **Vacation**\n\n*Target: ₹50,000*")
        with scol3:
            st.markdown("🚨 **Emergency Fund**\n\n*Target: ₹100,000*")


# Force streamlit reload
