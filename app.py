"""
Flood Risk Early Warning System — Streamlit Dashboard
Nigeria Case Study
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from data.generate_data import generate_risk_scores, generate_flood_events, generate_rainfall_data
from gis.spatial_analysis import build_geodataframe, classify_risk_zones, build_folium_map

st.set_page_config(
    page_title="Nigeria Flood Risk EWS",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card{background:#1e3a5f;border-radius:10px;padding:16px;text-align:center;color:white;}
.metric-value{font-size:2rem;font-weight:700;}
.metric-label{font-size:.85rem;opacity:.8;}
.alert-red{background:#d32f2f;color:white;padding:8px 14px;border-radius:6px;}
.alert-orange{background:#f57c00;color:white;padding:8px 14px;border-radius:6px;}
.alert-green{background:#388e3c;color:white;padding:8px 14px;border-radius:6px;}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    risk = generate_risk_scores()
    events = generate_flood_events(300)
    rainfall = generate_rainfall_data(365)
    return risk, events, rainfall


def alert_badge(level: str) -> str:
    cls = {"Red": "alert-red", "Orange": "alert-orange", "Green": "alert-green"}.get(level, "alert-green")
    return f'<span class="{cls}">{level}</span>'


def main():
    risk_df, events_df, rainfall_df = load_data()
    risk_gdf = build_geodataframe(risk_df)
    risk_gdf = classify_risk_zones(risk_gdf)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/79/Flag_of_Nigeria.svg/320px-Flag_of_Nigeria.svg.png",
                 width=120)
        st.title("Flood Risk EWS")
        st.caption("Nigeria Early Warning System")
        st.divider()

        selected_zone = st.multiselect(
            "Filter by Flood Zone",
            options=risk_df["flood_zone"].unique().tolist(),
            default=risk_df["flood_zone"].unique().tolist(),
        )
        risk_threshold = st.slider("Minimum Risk Score", 0.0, 1.0, 0.0, 0.05)
        st.divider()
        st.markdown("**Azure Services Active**")
        st.success("Azure Blob Storage")
        st.info("Azure Databricks")
        st.warning("Azure Event Hubs (IoT)")

    filtered = risk_df[
        risk_df["flood_zone"].isin(selected_zone) &
        (risk_df["risk_score"] >= risk_threshold)
    ]

    # ── Header ────────────────────────────────────────────────────────────────
    st.title("🌊 Nigeria Flood Risk Early Warning System")
    st.caption("Real-time flood risk monitoring powered by GIS · PySpark · Azure · Streamlit")
    st.divider()

    # ── KPI Row ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    red_states = filtered[filtered["alert_level"] == "Red"]
    orange_states = filtered[filtered["alert_level"] == "Orange"]
    with col1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(filtered)}</div>
            <div class="metric-label">States Monitored</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card" style="background:#c62828;">
            <div class="metric-value">{len(red_states)}</div>
            <div class="metric-label">Red Alert States</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card" style="background:#e65100;">
            <div class="metric-value">{len(orange_states)}</div>
            <div class="metric-label">Orange Alert States</div></div>""", unsafe_allow_html=True)
    with col4:
        total_pop = filtered["population_at_risk"].sum()
        st.markdown(f"""<div class="metric-card" style="background:#1b5e20;">
            <div class="metric-value">{total_pop/1e6:.1f}M</div>
            <div class="metric-label">Population at Risk</div></div>""", unsafe_allow_html=True)

    st.divider()

    # ── Map + Chart Row ───────────────────────────────────────────────────────
    map_col, chart_col = st.columns([3, 2])

    with map_col:
        st.subheader("🗺 Interactive Flood Risk Map")
        m = build_folium_map(risk_gdf[risk_gdf["flood_zone"].isin(selected_zone)], events_df)
        st_folium(m, width=700, height=480)

    with chart_col:
        st.subheader("📊 Risk Score by State")
        top_states = filtered.nlargest(15, "risk_score")
        color_map = {"Red": "#d32f2f", "Orange": "#f57c00", "Green": "#388e3c"}
        fig_bar = px.bar(
            top_states,
            x="risk_score", y="state",
            orientation="h",
            color="alert_level",
            color_discrete_map=color_map,
            labels={"risk_score": "Risk Score", "state": ""},
            height=460,
        )
        fig_bar.update_layout(showlegend=True, margin=dict(l=0, r=10, t=10, b=10),
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ── Rainfall Trend ────────────────────────────────────────────────────────
    st.subheader("🌧 Rainfall Trend (2023)")
    selected_state = st.selectbox("Select State", sorted(rainfall_df["state"].unique()))
    state_rain = (
        rainfall_df[rainfall_df["state"] == selected_state]
        .groupby("date")["rainfall_mm"]
        .sum()
        .reset_index()
    )
    fig_rain = px.area(state_rain, x="date", y="rainfall_mm",
                       color_discrete_sequence=["#1565c0"],
                       labels={"rainfall_mm": "Rainfall (mm)", "date": "Date"})
    fig_rain.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_rain, use_container_width=True)

    st.divider()

    # ── Flood Events Table ────────────────────────────────────────────────────
    st.subheader("📋 Recent Flood Events")
    display_cols = ["date", "state", "severity", "flood_risk_score",
                    "displaced_persons", "affected_area_km2"]
    st.dataframe(
        events_df[display_cols].sort_values("date", ascending=False).head(50)
        .style.background_gradient(subset=["flood_risk_score"], cmap="RdYlGn_r"),
        use_container_width=True,
        height=300,
    )

    # ── Scatter: Population vs Risk ───────────────────────────────────────────
    st.subheader("👥 Population at Risk vs Flood Risk Score")
    fig_scatter = px.scatter(
        filtered, x="risk_score", y="population_at_risk",
        color="flood_zone", size="population_at_risk",
        hover_name="state", size_max=40,
        labels={"risk_score": "Flood Risk Score", "population_at_risk": "Population at Risk"},
    )
    fig_scatter.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.caption("Data: Synthetic — replace with NIMET, NIHSA, and NEMA live feeds. "
               "Pipeline: Azure Databricks PySpark. Storage: Azure Blob Storage.")


if __name__ == "__main__":
    main()
