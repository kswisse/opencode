#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
pip install -e ".[dev]"
streamlit run src/heat_intelligence/dashboard/app.py
