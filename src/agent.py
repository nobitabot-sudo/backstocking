import json
import pandas as pd

class ReturnsAgent:
    def __init__(self, catalog_path="data/catalog.json"):
        with open(catalog_path, "r") as f:
            self.catalog = json.load(f)

    def evaluate_returns_batch(self, returns_data):
        df = pd.DataFrame(returns_data)
        if df.empty:
            return None

        sku = df["sku"].iloc[0]
        batch_id = df["supplier_batch"].iloc[0]
        total_units = len(df)

        prod = self.catalog["products"][sku]
        vendor = self.catalog["vendor_terms"][sku]
        refurb = self.catalog["refurbishment"][prod["category"]]

        # Financial recovery per route
        rtv_recovery = prod["cost_price"] * vendor["credit_pct"]
        refurb_recovery = (prod["selling_price"] * refurb["resale_pct"]) - refurb["cost"]
        liquidation_recovery = prod["cost_price"] * self.catalog["liquidation"]["B"]

        # Batch Splitting Logic
        rtv_units = df[df["days_since_purchase"] <= vendor["window_days"]]
        rtv_count = len(rtv_units)
        refurb_count = total_units - rtv_count

        total_net_recovery = (rtv_count * rtv_recovery) + (refurb_count * refurb_recovery)

        # Quality Anomaly Detection
        defect_count = (df["reason_code"] == "Defective Sound").sum()
        defect_rate = defect_count / total_units
        quality_alert = defect_rate >= 0.50

        return {
            "sku": sku,
            "product_name": prod["name"],
            "batch_id": batch_id,
            "total_units": total_units,
            "rtv_count": rtv_count,
            "rtv_unit_val": rtv_recovery,
            "refurb_count": refurb_count,
            "refurb_unit_val": refurb_recovery,
            "liquidation_unit_val": liquidation_recovery,
            "total_recovery": total_net_recovery,
            "quality_alert": quality_alert,
            "defect_rate": defect_rate,
            "existing_stock_days": prod["current_stock"] / prod["avg_daily_demand"]
        }
