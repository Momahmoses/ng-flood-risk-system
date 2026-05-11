"""
Azure integration helpers for the Flood Risk System.
Services used:
  - Azure Blob Storage  : raw rainfall CSVs and model outputs
  - Azure Databricks    : PySpark pipeline execution
  - Azure Maps          : geocoding and routing for evacuation paths
  - Azure Event Hubs    : real-time IoT sensor ingestion (rainfall gauges)
"""
import os
from typing import Optional

# ── Environment variables ─────────────────────────────────────────────────────
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "ngfloodstorage")
AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY", "")
AZURE_CONTAINER_RAW = "flood-raw-data"
AZURE_CONTAINER_PROCESSED = "flood-processed"
AZURE_EVENTHUB_CONNECTION = os.getenv("AZURE_EVENTHUB_CONNECTION", "")
AZURE_EVENTHUB_NAME = "rainfall-sensors"
AZURE_MAPS_KEY = os.getenv("AZURE_MAPS_KEY", "")
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "https://<workspace>.azuredatabricks.net")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
DATABRICKS_CLUSTER_ID = os.getenv("DATABRICKS_CLUSTER_ID", "")


def get_blob_service_client():
    """Return an Azure BlobServiceClient. Requires azure-storage-blob installed."""
    try:
        from azure.storage.blob import BlobServiceClient
        return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    except ImportError:
        raise ImportError("Install azure-storage-blob: pip install azure-storage-blob")


def upload_csv_to_blob(local_path: str, blob_name: str,
                       container: str = AZURE_CONTAINER_RAW) -> str:
    client = get_blob_service_client()
    blob_client = client.get_blob_client(container=container, blob=blob_name)
    with open(local_path, "rb") as f:
        blob_client.upload_blob(f, overwrite=True)
    url = f"https://{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{container}/{blob_name}"
    print(f"Uploaded to {url}")
    return url


def download_blob(blob_name: str, local_path: str,
                  container: str = AZURE_CONTAINER_PROCESSED) -> None:
    client = get_blob_service_client()
    blob_client = client.get_blob_client(container=container, blob=blob_name)
    with open(local_path, "wb") as f:
        f.write(blob_client.download_blob().readall())
    print(f"Downloaded {blob_name} → {local_path}")


def get_databricks_job_config(script_path: str = "pipeline/spark_pipeline.py") -> dict:
    """Return a Databricks Jobs API payload to submit the PySpark pipeline."""
    return {
        "run_name": "FloodRiskPipeline",
        "existing_cluster_id": DATABRICKS_CLUSTER_ID,
        "spark_python_task": {
            "python_file": f"dbfs:/FileStore/{script_path}",
            "parameters": ["--data-path", f"wasbs://{AZURE_CONTAINER_RAW}@{AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/"]
        },
    }


def get_azure_maps_flood_zones(lat: float, lon: float, radius_km: float = 50) -> Optional[dict]:
    """Stub for Azure Maps flood zone lookup — replace with live call in production."""
    return {
        "location": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "flood_risk": "Moderate",
        "note": "Replace with real Azure Maps API call using AZURE_MAPS_KEY",
    }
