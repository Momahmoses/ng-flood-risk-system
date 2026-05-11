# 🌊 Nigeria Flood Risk Early Warning System

A full-stack geospatial application for real-time flood risk monitoring across Nigeria's 36 states and FCT, combining **GIS spatial analysis**, **PySpark big-data pipelines**, **Azure cloud services**, and a **Streamlit interactive dashboard**.

## Problem Statement
Nigeria loses billions of naira annually to flooding. States like Kogi, Anambra, Bayelsa, and Delta face catastrophic riverine and coastal floods displacing millions. This system provides an early warning dashboard for emergency managers and NEMA officials.

## Tech Stack
| Layer | Technology |
|---|---|
| Geospatial | GeoPandas, Shapely, Folium, Azure Maps |
| Big Data | PySpark 3.5 on Azure Databricks |
| Cloud | Azure Blob Storage, Azure Event Hubs, Azure Databricks |
| Dashboard | Streamlit + Plotly |

## Project Structure
```
ng-flood-risk-system/
├── app.py                        # Streamlit dashboard (entry point)
├── pipeline/spark_pipeline.py    # PySpark ETL + GBT severity model
├── gis/spatial_analysis.py       # GeoPandas risk zones + Folium maps
├── data/generate_data.py         # Synthetic rainfall & event data
├── azure/azure_config.py         # Azure Blob, Databricks, Event Hubs helpers
└── requirements.txt
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate sample data
python data/generate_data.py

# 3. Run GIS analysis
python gis/spatial_analysis.py

# 4. Launch dashboard
streamlit run app.py
```

## Azure Deployment
1. **Storage**: Upload CSVs to Azure Blob container `flood-raw-data`
2. **Pipeline**: Submit `pipeline/spark_pipeline.py` as a Databricks job
3. **Real-time**: Wire rainfall IoT sensors to Azure Event Hubs
4. **Dashboard**: Deploy `streamlit run app.py` on Azure App Service

Set environment variables:
```env
AZURE_STORAGE_CONNECTION_STRING=...
AZURE_STORAGE_KEY=...
AZURE_EVENTHUB_CONNECTION=...
AZURE_MAPS_KEY=...
DATABRICKS_HOST=...
DATABRICKS_TOKEN=...
```

## Dashboard Features
- Interactive flood risk map with state-level risk circles and event heatmap
- KPI cards: red/orange alert counts, total population at risk
- Rainfall trend area chart per state (2023)
- Top-15 highest-risk states bar chart
- Flood events table with severity and displacement data
- Population at risk vs risk score scatter plot

## Data Sources (Production)
- **NIMET** — Nigeria Meteorological Agency (rainfall data)
- **NIHSA** — Nigeria Hydrological Services Agency (river levels)
- **NEMA** — National Emergency Management Agency (flood events)
- **NBS** — National Bureau of Statistics (population data)
