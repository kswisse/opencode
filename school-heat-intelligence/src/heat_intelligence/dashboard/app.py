"""School Heat Intelligence — Main Dashboard Application.

Simplified submission-ready MVP: single Overview page.
Backend modules are preserved for future development.
"""
import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import streamlit as st

st.set_page_config(page_title="School Heat Intelligence", page_icon="🌡️", layout="wide")
st.title("🌡️ School Heat Intelligence")
st.caption("Campus heat risk detection, forecasting, and intervention simulation")
st.info("**Data Provenance:** 🟡 Synthetic demo data | 🟠 Model predictions | 🔴 Simulations\n\nAll weights are illustrative heuristic parameters, NOT empirically calibrated.")

from heat_intelligence.data import load_data
from heat_intelligence.config import load_config

config = load_config()
data_path = Path(__file__).parent.parent.parent.parent / "data" / "demo_campus.csv"
data = load_data(str(data_path))

from heat_intelligence.dashboard.pages import _p1_overview
_p1_overview.render(data, config)

st.divider()
st.caption(
    "MVP hiện tại tập trung vào màn hình Tổng quan; "
    "các module phân tích chuyên sâu được giữ trong hệ thống backend để phát triển tiếp."
)
