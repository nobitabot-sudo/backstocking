import streamlit as st
import json
import pandas as pd
from pathlib import Path
from src.agent import ReturnsAgent

# Get absolute path of the directory where app.py is located
BASE_DIR = Path(__file__).parent.resolve()

st.set_page_config(page_title="Gadgetbay AI - Returns Agent", layout="wide")

# Setup Agent with correct path
agent = ReturnsAgent(catalog_path=BASE_DIR / "data/catalog.json")

# Read returns.json with absolute path
returns_file_path = BASE_DIR / "data/returns.json"

with open(returns_file_path, "r") as f:
    sample_returns = json.load(f)
