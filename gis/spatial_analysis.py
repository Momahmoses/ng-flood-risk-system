"""
GIS spatial analysis for flood risk: proximity scoring, hotspot detection,
and risk zone classification using GeoPandas and Shapely.
"""
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import folium
from folium.plugins import HeatMap, MarkerCluster
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from data.generate_data import generate_risk_scores, generate_flood_events

NIGERIA_RIVERS = [
    {"name": "Niger River", "lat": 6.5, "lon": 6.5},
    {"name": "Benue River", "lat": 7.8, "lon": 8.5},
    {"name": "Cross River", "lat": 5.5, "lon": 8.3},
    {"name": "Kaduna River", "lat": 10.2, "lon": 7.4},
]

RISK_COLORS = {"Red": "#d32f2f", "Orange": "#f57c00", "Green": "#388e3c"}
ALERT_COLORS = {"RED": "#d32f2f", "ORANGE": "#f57c00", "GREEN": "#388e3c"}


def build_geodataframe(risk_df: pd.DataFrame) -> gpd.GeoDataFrame:
    geometry = [Point(row.lon, row.lat) for _, row in risk_df.iterrows()]
    return gpd.GeoDataFrame(risk_df, geometry=geometry, crs="EPSG:4326")


def compute_flood_buffers(gdf: gpd.GeoDataFrame, risk_threshold: float = 0.5) -> gpd.GeoDataFrame:
    """Buffer high-risk points (projected to metres, then back to WGS84)."""
    high_risk = gdf[gdf["risk_score"] >= risk_threshold].copy()
    high_risk_m = high_risk.to_crs("EPSG:32632")
    high_risk_m["buffer"] = high_risk_m.geometry.buffer(30_000)  # 30 km buffer
    high_risk_m = high_risk_m.set_geometry("buffer")
    return high_risk_m.to_crs("EPSG:4326")


def spatial_join_rivers(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Compute distance (km) from each state centroid to the nearest major river."""
    river_points = gpd.GeoDataFrame(
        NIGERIA_RIVERS,
        geometry=[Point(r["lon"], r["lat"]) for r in NIGERIA_RIVERS],
        crs="EPSG:4326"
    ).to_crs("EPSG:32632")
    gdf_m = gdf.to_crs("EPSG:32632")
    gdf_m["nearest_river_km"] = gdf_m.geometry.apply(
        lambda pt: river_points.geometry.distance(pt).min() / 1000
    )
    return gdf_m.to_crs("EPSG:4326")


def classify_risk_zones(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    conditions = [
        gdf["risk_score"] >= 0.70,
        (gdf["risk_score"] >= 0.45) & (gdf["risk_score"] < 0.70),
    ]
    choices = ["High", "Moderate"]
    gdf["risk_class"] = np.select(conditions, choices, default="Low")
    return gdf


def build_folium_map(risk_gdf: gpd.GeoDataFrame,
                     events_df: pd.DataFrame) -> folium.Map:
    m = folium.Map(location=[9.0820, 8.6753], zoom_start=6,
                   tiles="CartoDB positron")

    # State risk circles
    for _, row in risk_gdf.iterrows():
        color = (RISK_COLORS.get(row.get("alert_level", "Green"), "#388e3c")
                 if "alert_level" in row.index
                 else ("#d32f2f" if row["risk_score"] >= 0.70
                       else "#f57c00" if row["risk_score"] >= 0.45
                       else "#388e3c"))
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=max(6, row["risk_score"] * 22),
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(
                f"<b>{row['state']}</b><br>"
                f"Risk Score: {row['risk_score']:.2f}<br>"
                f"Zone: {row['flood_zone']}<br>"
                f"Pop at Risk: {row.get('population_at_risk', 'N/A'):,}",
                max_width=220,
            ),
            tooltip=row["state"],
        ).add_to(m)

    # Heat map of flood events
    heat_data = [[r.lat, r.lon, r.flood_risk_score] for _, r in events_df.iterrows()]
    HeatMap(heat_data, radius=18, blur=15, min_opacity=0.4).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;background:white;
                padding:10px;border-radius:8px;border:1px solid #ccc;font-size:13px;">
      <b>Flood Risk Level</b><br>
      <span style="color:#d32f2f;">&#9679;</span> High (&ge;0.70)<br>
      <span style="color:#f57c00;">&#9679;</span> Moderate (0.45–0.70)<br>
      <span style="color:#388e3c;">&#9679;</span> Low (&lt;0.45)
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


def run_analysis(output_html: str = "app/flood_risk_map.html"):
    risk_df = generate_risk_scores()
    events_df = generate_flood_events()
    gdf = build_geodataframe(risk_df)
    gdf = classify_risk_zones(gdf)
    gdf = spatial_join_rivers(gdf)
    m = build_folium_map(gdf, events_df)
    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    m.save(output_html)
    print(f"Map saved to {output_html}")
    return gdf


if __name__ == "__main__":
    gdf = run_analysis()
    print(gdf[["state", "risk_score", "risk_class", "nearest_river_km"]].to_string())
