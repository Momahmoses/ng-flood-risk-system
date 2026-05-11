import pandas as pd
import numpy as np
import os

NIGERIA_STATES = [
    {"state": "Lagos", "lat": 6.5244, "lon": 3.3792, "flood_zone": "coastal", "elevation_m": 5},
    {"state": "Kogi", "lat": 7.7337, "lon": 6.6906, "flood_zone": "riverine", "elevation_m": 95},
    {"state": "Anambra", "lat": 6.2104, "lon": 6.9623, "flood_zone": "riverine", "elevation_m": 52},
    {"state": "Delta", "lat": 5.5320, "lon": 5.8987, "flood_zone": "coastal", "elevation_m": 12},
    {"state": "Bayelsa", "lat": 4.7719, "lon": 6.0699, "flood_zone": "coastal", "elevation_m": 8},
    {"state": "Rivers", "lat": 4.8156, "lon": 7.0498, "flood_zone": "coastal", "elevation_m": 10},
    {"state": "Edo", "lat": 6.3350, "lon": 5.6037, "flood_zone": "riverine", "elevation_m": 78},
    {"state": "Benue", "lat": 7.3369, "lon": 8.7404, "flood_zone": "riverine", "elevation_m": 97},
    {"state": "Niger", "lat": 10.0008, "lon": 5.5981, "flood_zone": "riverine", "elevation_m": 162},
    {"state": "Kebbi", "lat": 11.4943, "lon": 4.2333, "flood_zone": "riverine", "elevation_m": 248},
    {"state": "Abuja (FCT)", "lat": 9.0765, "lon": 7.3986, "flood_zone": "inland", "elevation_m": 840},
    {"state": "Kano", "lat": 12.0022, "lon": 8.5920, "flood_zone": "inland", "elevation_m": 472},
    {"state": "Kaduna", "lat": 10.5222, "lon": 7.4383, "flood_zone": "inland", "elevation_m": 614},
    {"state": "Plateau", "lat": 9.2182, "lon": 9.5179, "flood_zone": "highland", "elevation_m": 1280},
    {"state": "Adamawa", "lat": 9.3265, "lon": 12.3984, "flood_zone": "riverine", "elevation_m": 588},
    {"state": "Taraba", "lat": 7.9993, "lon": 10.7741, "flood_zone": "riverine", "elevation_m": 320},
    {"state": "Cross River", "lat": 5.9631, "lon": 8.3305, "flood_zone": "riverine", "elevation_m": 175},
    {"state": "Akwa Ibom", "lat": 5.0527, "lon": 7.9335, "flood_zone": "coastal", "elevation_m": 22},
    {"state": "Imo", "lat": 5.4527, "lon": 7.0201, "flood_zone": "riverine", "elevation_m": 91},
    {"state": "Ogun", "lat": 6.9980, "lon": 3.4737, "flood_zone": "inland", "elevation_m": 88},
    {"state": "Ondo", "lat": 7.0003, "lon": 5.0000, "flood_zone": "coastal", "elevation_m": 45},
    {"state": "Oyo", "lat": 7.3775, "lon": 3.9470, "flood_zone": "inland", "elevation_m": 214},
    {"state": "Osun", "lat": 7.5629, "lon": 4.5624, "flood_zone": "inland", "elevation_m": 302},
    {"state": "Ekiti", "lat": 7.6218, "lon": 5.2311, "flood_zone": "highland", "elevation_m": 495},
    {"state": "Kwara", "lat": 8.9669, "lon": 4.3873, "flood_zone": "riverine", "elevation_m": 311},
    {"state": "Nassarawa", "lat": 8.4994, "lon": 8.1997, "flood_zone": "riverine", "elevation_m": 268},
    {"state": "Enugu", "lat": 6.4584, "lon": 7.5464, "flood_zone": "highland", "elevation_m": 223},
    {"state": "Abia", "lat": 5.3671, "lon": 7.4948, "flood_zone": "riverine", "elevation_m": 104},
    {"state": "Ebonyi", "lat": 6.2649, "lon": 8.0137, "flood_zone": "riverine", "elevation_m": 136},
    {"state": "Sokoto", "lat": 13.0059, "lon": 5.2476, "flood_zone": "inland", "elevation_m": 272},
    {"state": "Zamfara", "lat": 12.1222, "lon": 6.2236, "flood_zone": "inland", "elevation_m": 461},
    {"state": "Katsina", "lat": 12.9908, "lon": 7.6018, "flood_zone": "inland", "elevation_m": 519},
    {"state": "Jigawa", "lat": 12.2280, "lon": 9.5616, "flood_zone": "inland", "elevation_m": 371},
    {"state": "Yobe", "lat": 12.2939, "lon": 11.4390, "flood_zone": "inland", "elevation_m": 347},
    {"state": "Bauchi", "lat": 10.3158, "lon": 9.8442, "flood_zone": "inland", "elevation_m": 621},
    {"state": "Borno", "lat": 11.8846, "lon": 13.1571, "flood_zone": "inland", "elevation_m": 305},
    {"state": "Gombe", "lat": 10.2791, "lon": 11.1673, "flood_zone": "inland", "elevation_m": 470},
]

FLOOD_RISK_BY_ZONE = {
    "coastal": (0.65, 0.95),
    "riverine": (0.45, 0.80),
    "inland": (0.10, 0.40),
    "highland": (0.05, 0.20),
}


def generate_rainfall_data(n_days: int = 365) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n_days)
    records = []
    for state_info in NIGERIA_STATES:
        # Nigeria rainy season: April–October
        for date in dates:
            month = date.month
            is_rainy = 4 <= month <= 10
            base = 12 if is_rainy else 2
            rainfall_mm = max(0, np.random.exponential(base) + np.random.normal(0, 1))
            records.append({
                "date": date,
                "state": state_info["state"],
                "lat": state_info["lat"],
                "lon": state_info["lon"],
                "rainfall_mm": round(rainfall_mm, 2),
                "elevation_m": state_info["elevation_m"],
                "flood_zone": state_info["flood_zone"],
            })
    return pd.DataFrame(records)


def generate_flood_events(n_events: int = 200) -> pd.DataFrame:
    np.random.seed(42)
    records = []
    for _ in range(n_events):
        state_info = NIGERIA_STATES[np.random.randint(len(NIGERIA_STATES))]
        lo, hi = FLOOD_RISK_BY_ZONE[state_info["flood_zone"]]
        severity = np.random.choice(["Low", "Moderate", "Severe", "Extreme"],
                                    p=[0.35, 0.35, 0.20, 0.10])
        records.append({
            "date": pd.Timestamp("2023-01-01") + pd.Timedelta(days=int(np.random.randint(365))),
            "state": state_info["state"],
            "lat": state_info["lat"] + np.random.uniform(-0.5, 0.5),
            "lon": state_info["lon"] + np.random.uniform(-0.5, 0.5),
            "flood_risk_score": round(np.random.uniform(lo, hi), 3),
            "severity": severity,
            "displaced_persons": int(np.random.exponential(5000)),
            "affected_area_km2": round(np.random.exponential(120), 1),
            "flood_zone": state_info["flood_zone"],
        })
    return pd.DataFrame(records)


def generate_risk_scores() -> pd.DataFrame:
    np.random.seed(42)
    records = []
    for state_info in NIGERIA_STATES:
        lo, hi = FLOOD_RISK_BY_ZONE[state_info["flood_zone"]]
        records.append({
            "state": state_info["state"],
            "lat": state_info["lat"],
            "lon": state_info["lon"],
            "elevation_m": state_info["elevation_m"],
            "flood_zone": state_info["flood_zone"],
            "risk_score": round(np.random.uniform(lo, hi), 3),
            "river_proximity_km": round(np.random.uniform(1, 80), 1),
            "drainage_quality": np.random.choice(["Poor", "Fair", "Good"], p=[0.4, 0.4, 0.2]),
            "population_at_risk": int(np.random.uniform(50000, 5000000)),
            "alert_level": "Red" if np.random.uniform(lo, hi) > 0.70 else
                           "Orange" if np.random.uniform(lo, hi) > 0.45 else "Green",
        })
    return pd.DataFrame(records)


def save_all(output_dir: str = "data"):
    os.makedirs(output_dir, exist_ok=True)
    generate_rainfall_data().to_csv(f"{output_dir}/rainfall.csv", index=False)
    generate_flood_events().to_csv(f"{output_dir}/flood_events.csv", index=False)
    generate_risk_scores().to_csv(f"{output_dir}/risk_scores.csv", index=False)
    print("Sample data generated.")


if __name__ == "__main__":
    save_all()
