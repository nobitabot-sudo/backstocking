import streamlit as st
import json
import pandas as pd
import plotly.express as px
from pathlib import Path
from src.agent import ReturnsAgent

# Path Resolution Fix
BASE_DIR = Path(__file__).parent.resolve()

st.set_page_config(page_title="Gadgetbay AI - Returns Agent", layout="wide")

st.title("📦 Gadgetbay AI — Returns & Recovery Control Tower")
st.caption("Agentic Decision Engine: Observe ➔ Reason ➔ Evaluate ➔ Decide ➔ Act (Cypher 2026)")

# Initialize Agent
catalog_file = BASE_DIR / "data" / "catalog.json"
agent = ReturnsAgent(catalog_path=catalog_file)

# Sidebar Controls
st.sidebar.header("🕹️ Agent Controls & Data Input")

# Feature 1: CSV Upload for Custom Test Data
uploaded_file = st.sidebar.file_uploader("Upload Custom Returns CSV (Optional)", type=["csv"])

if uploaded_file is not None:
    try:
        sample_returns = pd.read_csv(uploaded_file).to_dict(orient="records")
        st.sidebar.success("Custom CSV Loaded Successfully!")
    except Exception as e:
        st.sidebar.error(f"Error reading CSV: {e}")
        st.stop()
else:
    # Default JSON load
    returns_file = BASE_DIR / "data" / "returns.json"
    with open(returns_file, "r", encoding="utf-8") as f:
        sample_returns = json.load(f)

run_engine = st.sidebar.button("Run Intelligence Engine", type="primary")

if run_engine or st.session_state.get("ran", True):
    st.session_state["ran"] = True
    decision = agent.evaluate_returns_batch(sample_returns)

    # Top Metric Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Returns Analyzed", f"{decision['total_units']} Units")
    c2.metric("Projected Net Recovery", f"₹{decision['total_recovery']:,.2f}")
    c3.metric("RTV Eligible Units", f"{decision['rtv_count']} / {decision['total_units']}")
    c4.metric("Existing Inventory Cover", f"{decision['existing_stock_days']:.0f} Days")

    st.markdown("---")

    # Recommendation and Financial Visuals
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        st.subheader("🤖 Recommended Strategic Actions")
        st.info(f"""
        * **Route 1 (Return to Vendor):** Dispatch **{decision['rtv_count']} units** back to supplier for 60% credit (**₹{decision['rtv_unit_val']:,.0f}** / unit).
        * **Route 2 (Refurbish):** Refurbish remaining **{decision['refurb_count']} units** at ₹250 cost for resale (**₹{decision['refurb_unit_val']:,.0f}** net / unit).
        """)

        if decision["quality_alert"]:
            st.error(f"""
            🚨 **Supplier Quality Alert (Batch {decision['batch_id']})**
            * Defect Rate: **{decision['defect_rate']*100:.0f}%** for 'Defective Sound'.
            * **Recommendation:** Block future orders from Batch {decision['batch_id']} & raise vendor quality claim.
            """)
        else:
            st.success("No abnormal supplier batch defect rates detected.")

    with col_b:
        st.subheader("📊 Financial Recovery Distribution")
        # Feature 2: Interactive Plotly Chart
        chart_data = pd.DataFrame({
            "Route": ["Return To Vendor (RTV)", "Refurbish & Resell"],
            "Recovery Amount (₹)": [
                decision['rtv_count'] * decision['rtv_unit_val'],
                decision['refurb_count'] * decision['refurb_unit_val']
            ]
        })
        fig = px.bar(
            chart_data, 
            x="Route", 
            y="Recovery Amount (₹)", 
            color="Route",
            text_auto='.2s',
            title="Batch Recovery Value per Route"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Human Approval Gate
    st.subheader("⚡ Human Approval Gate")
    st.caption("No action is executed without explicit human authorization.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve Batch Split & Raise Claim", type="primary"):
            st.success(f"✅ Approved! Created RTV Order #RTV-9921 ({decision['rtv_count']} units) & Refurb Task #RF-1042.")
    with col2:
        if st.button("Reject / Manual Override"):
            st.warning("⚠️ Action rejected. Decision routed for manual review.")
