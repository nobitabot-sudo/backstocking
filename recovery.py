import dataclasses
import pandas as pd

REQUIRED = ["unit_id", "batch", "fault", "days_left_in_window"]


@dataclasses.dataclass
class Params:
    new_price: float = 2500.0
    cost: float = 1400.0
    refurb_cost: float = 250.0
    resale_pct: float = 0.75
    supplier_pct: float = 0.60
    liquidation_pct: float = 0.35
    stock_days: int = 60


def sample_df() -> pd.DataFrame:
    rows = []
    # 24 units inside supplier return window (batch HB-09, fault: mic failure)
    for i in range(1, 25):
        rows.append({
            "unit_id": f"HBP-{i:03d}",
            "batch": "HB-09",
            "fault": "Microphone issue",
            "days_left_in_window": 14 if i <= 10 else (2 if i <= 18 else 5)
        })
    # 4 units outside return window (batch HB-09, fault: mic failure) -> 28 total HB-09 mic fails (70%)
    for i in range(25, 29):
        rows.append({
            "unit_id": f"HBP-{i:03d}",
            "batch": "HB-09",
            "fault": "Microphone issue",
            "days_left_in_window": 0
        })
    # 12 remaining units with various faults outside return window
    faults = ["Bluetooth pairing", "Battery drain", "Physical scratch", "Audio distortion"]
    for i in range(29, 41):
        rows.append({
            "unit_id": f"HBP-{i:03d}",
            "batch": f"HB-0{1 + (i % 3)}",
            "fault": faults[i % len(faults)],
            "days_left_in_window": 0
        })
    return pd.DataFrame(rows)


def validate(df: pd.DataFrame) -> list[str]:
    return [c for c in REQUIRED if c not in df.columns]


def per_unit(p: Params) -> dict[str, float]:
    refurb_val = (p.new_price * p.resale_pct) - p.refurb_cost
    supplier_val = p.cost * p.supplier_pct
    liquidation_val = p.cost * p.liquidation_pct
    return {
        "Refurbish": refurb_val,
        "Supplier Return": supplier_val,
        "Liquidate": liquidation_val
    }


def plan(df: pd.DataFrame, p: Params) -> dict:
    pu = per_unit(p)
    n = len(df)
    
    days_left = pd.to_numeric(df["days_left_in_window"], errors="coerce").fillna(0)
    eligible_mask = days_left > 0
    n_sup = int(eligible_mask.sum())
    n_rest = n - n_sup
    
    rest_route = "Refurbish" if pu["Refurbish"] >= pu["Liquidate"] else "Liquidate"
    rest_val = pu[rest_route]
    
    sup_val = pu["Supplier Return"]
    sup_total = n_sup * sup_val
    rest_total = n_rest * rest_val
    total = sup_total + rest_total
    
    all_refurb = n * pu["Refurbish"]
    
    return {
        "n": n,
        "n_sup": n_sup,
        "sup_val": sup_val,
        "sup_total": sup_total,
        "n_rest": n_rest,
        "rest_route": rest_route,
        "rest_val": rest_val,
        "rest_total": rest_total,
        "total": total,
        "all_refurb": all_refurb
    }


def fault_alert(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"batch": "None", "fault": "None", "count": 0, "share": 0.0}
    
    grouped = df.groupby(["batch", "fault"]).size().reset_index(name="count")
    top = grouped.sort_values("count", ascending=False).iloc[0]
    total = len(df)
    
    return {
        "batch": top["batch"],
        "fault": top["fault"],
        "count": int(top["count"]),
        "share": float(top["count"] / total)
    }


def claim_text(df: pd.DataFrame, alert: dict, p: Params) -> str:
    return (
        f"SUPPLIER CLAIM DRAFT — REPETITIVE FAULT REPORT\n"
        f"---------------------------------------------\n"
        f"Batch Identifier: {alert['batch']}\n"
        f"Reported Defect:  {alert['fault']}\n"
        f"Affected Volume:  {alert['count']} of {len(df)} units ({alert['share']:.0%})\n\n"
        f"Summary:\n"
        f"An unusually high defect concentration has been detected in Batch {alert['batch']}. "
        f"Over {alert['share']:.0%} of returned units exhibit identical issues ({alert['fault']}).\n\n"
        f"Requested Action:\n"
        f"1. Acknowledge defect report for Batch {alert['batch']}.\n"
        f"2. Authorize full credit authorization at {p.supplier_pct:.0%} cost value (₹{p.cost * p.supplier_pct:,.2f}/unit).\n"
        f"3. Issue RMA for remaining uninspected stock from this batch."
    )
