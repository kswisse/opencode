"""Research Analysis page — synthetic data QC, statistics, and outputs."""
import streamlit as st
import pandas as pd
from pathlib import Path

from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.models.schemas import ZoneReading


def render(data: list, config: HeatIntelligenceConfig):
    st.header("Research Analysis")

    # Synthetic data provenance warning
    st.warning(
        "**DỮ LIỆU MÔ PHỎNG — KHÔNG PHẢI KẾT QUẢ THỰC NGHIỆM**\n\n"
        "All data shown on this page is synthetically generated for research protocol "
        "demonstration. Relationships and statistics are illustrative heuristics, "
        "NOT empirically calibrated findings."
    )

    # Load synthetic environmental data if available
    env_csv = Path(__file__).parent.parent.parent.parent.parent / "data" / "research_synthetic_environmental.csv"
    student_csv = Path(__file__).parent.parent.parent.parent.parent / "data" / "research_synthetic_students.csv"

    # QC Summary
    st.subheader("Data Quality Control")
    qc_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "research_qc_report.json"
    if qc_path.exists():
        import json
        with open(qc_path) as f:
            qc = json.load(f)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", qc.get("total_rows", 0))
        with col2:
            st.metric("Overall Pass", "✓ Pass" if qc.get("overall_pass") else "✗ Fail")
        with col3:
            n_issues = (
                len(qc.get("missing_values", {})) +
                len(qc.get("duplicate_timestamps", [])) +
                len(qc.get("invalid_ranges", {})) +
                len(qc.get("missing_zones", [])) +
                len(qc.get("temporal_gaps", []))
            )
            st.metric("Issues Found", n_issues)

        if qc.get("temporal_gaps"):
            st.info(f"Temporal gaps: {len(qc['temporal_gaps'])} (gaps > 1 hour)")
        if qc.get("duplicate_timestamps"):
            st.info(f"Duplicate timestamps: {len(qc['duplicate_timestamps'])}")
    else:
        st.info("Run `python scripts/generate_all.py` to generate QC report.")

    # Descriptive Statistics
    st.subheader("Descriptive Statistics")
    stats_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "research_outputs" / "summary_stats.csv"
    if stats_path.exists():
        df_stats = pd.read_csv(stats_path)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
    else:
        st.info("Run `python scripts/generate_all.py` to generate statistics.")

    # Correlation / Effect Sizes
    st.subheader("Correlation & Effect Sizes")
    corr_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "research_outputs" / "correlation_matrix.csv"
    es_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "research_outputs" / "effect_sizes.csv"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Correlation Matrix**")
        if corr_path.exists():
            df_corr = pd.read_csv(corr_path)
            st.dataframe(df_corr, use_container_width=True, hide_index=True)
        else:
            st.info("Not yet generated.")

    with col2:
        st.markdown("**Effect Sizes (Cohen's d)**")
        if es_path.exists():
            df_es = pd.read_csv(es_path)
            st.dataframe(df_es, use_container_width=True, hide_index=True)
        else:
            st.info("Not yet generated.")

    # Forecast Validation
    st.subheader("Forecast Validation")
    fv_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "research_outputs" / "forecast_validation.csv"
    if fv_path.exists():
        df_fv = pd.read_csv(fv_path)
        st.dataframe(df_fv, use_container_width=True, hide_index=True)
    else:
        st.info("Run forecast evaluation to generate this table.")

    # Intervention Comparison
    st.subheader("Intervention Comparison")
    iv_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "research_outputs" / "intervention_comparison.csv"
    if iv_path.exists():
        df_iv = pd.read_csv(iv_path)
        st.dataframe(df_iv, use_container_width=True, hide_index=True)
    else:
        st.info("Run intervention simulation to generate this table.")

    # Figures
    st.subheader("Research Figures")
    fig_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "research_outputs" / "fig"
    if fig_dir.exists():
        fig_files = sorted(fig_dir.glob("*.png"))
        for fig_file in fig_files:
            st.image(str(fig_file), caption=fig_file.stem.replace("_", " ").title(), use_container_width=True)
    else:
        st.info("Run `python scripts/generate_all.py` to generate figures.")

    st.markdown("---")
    st.caption(
        "Synthetic research pipeline — all weights and coefficients are illustrative "
        "heuristics, NOT empirically calibrated. Rerun with real data after field collection."
    )
