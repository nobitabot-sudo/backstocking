import datetime as dt
import pandas as pd
import plotly.express as px
import streamlit as st
from src.recovery import (REQUIRED, Params, claim_text, fault_alert, per_unit,
                          plan, sample_df, validate)

st.set_page_config(page_title="ReTrack AI", page_icon="📦", layout="wide")
st.title("📦 ReTrack AI — Returns Decision Assistant")
st.caption("Cypher 4.0 · Challenge 10 “What Came Back” · Gadgetbay. "
           "All figures are estimates based on the challenge scenario. Actions are simulated.")

# ---------- Sidebar ----------
sb = st.sidebar
sb.header("Data")
up = sb.file_uploader("Upload returns CSV (optional)", type=["csv"])
sb.download_button("Download CSV template", sample_df().to_csv(index=False),
                   "returns_template.csv", "text/csv")

if up is not None:
    df = pd.read_csv(up)
    missing = validate(df)
    if missing:
        sb.error(f"Missing columns: {', '.join(missing)}")
        st.stop()
    sb.success("Your CSV is loaded.")
else:
    df = sample_df()
    sb.info("Showing the challenge example: 40 Grade B headphones.")

with sb.expander("What-if inputs (challenge defaults)"):
    p = Params(
        new_price=st.number_input("New selling price (₹)", value=2500.0, step=50.0),
        cost=st.number_input("Cost price (₹)", value=1400.0, step=50.0),
        refurb_cost=st.number_input("Refurbishing cost (₹)", value=250.0, step=10.0),
        resale_pct=st.slider("Refurbished resale, % of new price", 0, 100, 75) / 100,
        supplier_pct=st.slider("Supplier credit, % of cost", 0, 100, 60) / 100,
        liquidation_pct=st.slider("Liquidation, % of cost", 0, 100, 35) / 100,
        stock_days=st.number_input("New stock cover (days)", value=60, step=5),
    )

alert_pct = sb.slider("Alert when one batch+fault share is at least (%)", 10, 100, 50)
urgent_days = sb.slider("Mark as urgent when days left is at most", 1, 14, 3)

pl, al, u = plan(df, p), fault_alert(df), per_unit(p)

# ---------- Metrics ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Returns analysed", f"{pl['n']} units")
c2.metric("Estimated recovery", f"₹{pl['total']:,.0f}")
c3.metric("Supplier-eligible", f"{pl['n_sup']} / {pl['n']}")
c4.metric("New stock cover", f"{p.stock_days} days")
st.caption("Estimate before handling or shipping costs (not provided in the challenge).")

t1, t2, t3, t4, t5 = st.tabs(["Plan", "Options", "Deadline radar", "Quality alert", "Approval"])

with t1:
    st.subheader("Recommended plan")
    st.info(
        f"**{pl['n_sup']} units → supplier return** at ₹{pl['sup_val']:,.0f} each "
        f"= ₹{pl['sup_total']:,.0f}\n\n"
        f"**{pl['n_rest']} units → {pl['rest_route'].lower()}** at ₹{pl['rest_val']:,.0f} each "
        f"= ₹{pl['rest_total']:,.0f}\n\n"
        f"**Estimated total: ₹{pl['total']:,.0f}**"
    )
    with st.expander("Why this plan?", expanded=True):
        st.write("- Units still inside the return window can earn supplier credit.")
        st.write("- The other units are refurbished (or liquidated if that pays more).")
        st.write(f"- New stock already covers {p.stock_days} days of demand, so restocking is not urgent.")
        st.write(f"- Refurbishing all {pl['n']} units would look higher on paper "
                 f"(₹{pl['all_refurb']:,.0f}), but {al['share']:.0%} of returns share one fault "
                 f"from batch {al['batch']}. The manager decides this trade-off.")

with t2:
    st.subheader("Recovery per unit (estimate)")
    tbl = pd.DataFrame({"Option": list(u), "Per unit (₹)": [round(v) for v in u.values()]})
    tbl.loc[len(tbl)] = ["Restock", None]
    st.dataframe(tbl, hide_index=True, use_container_width=True)
    st.caption("Supplier credit applies only to eligible units. Restock value was not provided; "
               "with 60 days of new stock, restocking is not the priority.")
    st.plotly_chart(px.bar(tbl.dropna(), x="Option", y="Per unit (₹)", text="Per unit (₹)",
                           color="Option"), use_container_width=True)

with t3:
    st.subheader("Supplier return deadline radar")
    radar = df[pd.to_numeric(df["days_left_in_window"], errors="coerce") > 0].copy()
    radar["status"] = radar["days_left_in_window"].apply(
        lambda d: "🔴 Urgent" if d <= urgent_days else "🟢 OK")
    radar = radar.sort_values("days_left_in_window")
    st.metric("Units that lose supplier credit if nobody acts soon",
              int((radar["days_left_in_window"] <= urgent_days).sum()))
    st.dataframe(radar[["unit_id", "batch", "fault", "days_left_in_window", "status"]],
                 hide_index=True, use_container_width=True)

with t4:
    st.subheader("Repeated-fault check")
    if al["share"] * 100 >= alert_pct:
        st.error(f"🚨 {al['share']:.0%} of returns ({al['count']} of {pl['n']}) share the fault "
                 f"“{al['fault']}” from batch {al['batch']}. Suggested action: flag the batch "
                 "for supplier review.")
    else:        st.success("No repeated fault above the alert level.")
    st.download_button("Download supplier claim draft", claim_text(df, al, p),
                       "supplier_claim_draft.txt")

with t5:
    st.subheader("Manager approval")
    st.caption("ReTrack AI only recommends. Nothing happens without approval, and the "
               "action is recorded as a simulation only.")
    log = st.session_state.setdefault("log", [])
    a, b = st.columns(2)
    stamp = dt.datetime.now().strftime("%H:%M:%S")
    if a.button("Approve plan", type="primary"):
        log.append({"time": stamp, "decision": "Approved (simulated)",
                    "supplier_units": pl["n_sup"], "other_units": pl["n_rest"],
                    "estimate_₹": round(pl["total"])})
    if b.button("Reject / manual review"):
        log.append({"time": stamp, "decision": "Rejected: manual review",
                    "supplier_units": 0, "other_units": 0, "estimate_₹": 0})
    if log:
        st.success("Recorded as a simulation. No real system was changed.")
        st.dataframe(pd.DataFrame(log), hide_index=True, use_container_width=True)
