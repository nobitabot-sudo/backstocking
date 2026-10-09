# 📦 ReTrack AI — Returns Decision & Recovery Control Tower

ReTrack AI is an intelligent returns management dashboard built for Cypher 4.0 (Challenge 10: "What Came Back"). It helps retail and e-commerce operations maximize recovery value from returned inventory.

## Key Features
- **Automated Financial Routing:** Calculates trade-offs between Supplier Returns (RTV), Refurbishing, and Liquidation.
- **Supplier Return Deadline Radar:** Identifies time-sensitive stock nearing vendor warranty expiration dates.
- **Batch Quality Alert Engine:** Flags repeated defect trends across manufacturing batches (e.g., 70% defect rate in Batch HB-09).
- **Automated Claim Generator:** Generates downloadable vendor claims for bad batches.
- **Human-in-the-Loop Simulation:** Requires explicit manager approval with built-in audit logs.

## Setup & Running Locally
```bash
pip install -r requirements.txt
streamlit run app.py
