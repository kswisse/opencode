"""Overview page — campus map, risk summary, hotspot alerts."""
import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from heat_intelligence.config import HeatIntelligenceConfig
from heat_intelligence.risk.engine import compute_risk_score
from heat_intelligence.hotspot.detector import detect_hotspots
from heat_intelligence.models.schemas import ZoneReading

def render(data: list, config: HeatIntelligenceConfig):
    st.header("Campus Overview")
    df = pd.DataFrame([r.model_dump() for r in data])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    latest = df.sort_values("timestamp").groupby("zone_id").last().reset_index()

    risk_scores = []
    for _, row in latest.iterrows():
        reading = ZoneReading(**row.to_dict())
        rs = compute_risk_score(reading, config)
        risk_scores.append(rs)

    hotspots = detect_hotspots(risk_scores, config)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Zones Monitored", len(latest))
    with col2:
        avg_risk = sum(r.score for r in hotspots) / len(hotspots) if hotspots else 0
        st.metric("Average Risk", f"{avg_risk:.1f}")
    with col3:
        hotspot_count = sum(1 for r in hotspots if "HOTSPOT" in r.label)
        st.metric("Hotspot Zones", hotspot_count)

    st.subheader("Campus Heat Map")
    m = folium.Map(location=[latest["lat"].mean(), latest["lon"].mean()], zoom_start=16)
    for rs in hotspots:
        color = "red" if rs.score > 75 else "orange" if rs.score > 50 else "green"
        folium.CircleMarker(
            location=[latest[latest["zone_id"] == rs.zone_id]["lat"].values[0],
                      latest[latest["zone_id"] == rs.zone_id]["lon"].values[0]],
            radius=15, color=color, fill=True, fill_color=color,
            popup=f"{rs.zone_name}: {rs.score:.1f} ({rs.label})",
        ).add_to(m)
    st_folium(m, width=700, height=400)

    st.subheader("Hotspot Alerts")
    for rs in hotspots:
        if "HOTSPOT" in rs.label:
            st.error(f"🔥 **{rs.zone_name}** — Risk: {rs.score:.1f} ({rs.label})")