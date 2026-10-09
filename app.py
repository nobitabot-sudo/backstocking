import streamlit as st
import json
import pandas as pd
from pathlib import Path
from src.agent import ReturnsAgent

# Path Resolution Fix (Streamlit Cloud FileNotFoundError prevent karne ke liye)
BASE_DIR = Path(__file__).parent.resolve()

st.set_page_config(page_title="Gadgetbay AI - Returns Agent", layout="wide")

# Styling & Title
st.title("📦 Gadgetbay AI — Returns & Recovery Control Tower")
st.caption("Agentic Decision Engine: Observe ➔ Reason ➔ Evaluate ➔ Decide ➔ Act (Cypher 2026)")

# Initialize Agent
catalog_file = BASE_DIR / "data" / "catalog.json"
agent = ReturnsAgent(catalog_path=catalog_file)

# Load Returns Data
returns_file = BASE_DIR / "data" / "returns.json"
try:
    with open(returns_file, "r", encoding="utf-8") as f:
        sample_returns = json.load(f)
except Exception as e:
    st.error(f"Error loading returns data file from {returns_file}: {e}")
    st.stop()

# Sidebar Control
st.sidebar.header("Agent Controls")
if st.sidebar.button("Run Intelligence Engine", type="primary"):
    st.session_state["ran"] = True

if st.session_state.get("ran", True):
    decision = agent.evaluate_returns_batch(sample_returns)

    # Top Metric Summary Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Returns Analyzed", f"{decision['total_units']} Units")
    c2.metric("Projected Net Recovery", f"₹{decision['total_recovery']:,.2f}")
    c3.metric("RTV Eligible Units", f"{decision['rtv_count']} / {decision['total_units']}")
    c4.metric("Existing Inventory Cover", f"{decision['existing_stock_days']:.0f} Days")

    st.markdown("---")

    # Agent Recommendation Section
    st.subheader("🤖 Recommended Strategic Actions")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.write("### 🔀 Batch Split Strategy")
        st.info(f"""
        * **Route 1 (Return to Vendor):** Dispatch **{decision['rtv_count']} units** back to supplier for 60% credit (**₹{decision['rtv_unit_val']:,.0f}** / unit).
        * **Route 2 (Refurbish):** Refurbish remaining **{decision['refurb_count']} units** at ₹250 cost for resale (**₹{decision['refurb_unit_val']:,.0f}** net / unit).
        """)

    with col_b:
        st.write("### 🚨 Supplier Quality Insight")
        if decision["quality_alert"]:
            st.error(f"""
            **Defect Alert on Batch {decision['batch_id']}**
            * Defect Rate: **{decision['defect_rate']*100:.0f}%** for 'Defective Sound'.
            * **Recommendation:** Block future orders from Batch {decision['batch_id']} & raise vendor quality claim.
            """)
        else:
            st.success("No abnormal supplier batch defect rates detected.")

    st.markdown("---")

    # Human Approval Gate (Mandatory Agentic Pattern)
    st.subheader("⚡ Human Approval Gate")
    st.caption("No action is executed without explicit human authorization.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve Batch Split & Raise Claim", type="primary"):
            st.success(f"✅ Approved! Created RTV Order #RTV-9921 ({decision['rtv_count']} units) & Refurb Task #RF-1042.")
    with col2:
        if st.button("Reject / Manual Override"):
            st.warning("⚠️ Action rejected. Decision routed for manual review.")
