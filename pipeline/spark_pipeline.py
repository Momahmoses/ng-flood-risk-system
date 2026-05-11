"""
Flood Risk PySpark Pipeline
Deploy on Azure Databricks: attach to a cluster and run as a notebook or job.
"""
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.regression import GBTRegressor
from pyspark.ml import Pipeline
from pyspark.sql.types import DoubleType
import os


def get_spark(app_name: str = "FloodRiskPipeline") -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        # Azure Blob Storage — replace with your storage account details
        .config("fs.azure.account.key.<STORAGE_ACCOUNT>.blob.core.windows.net",
                os.getenv("AZURE_STORAGE_KEY", ""))
        .getOrCreate()
    )


def load_data(spark: SparkSession, data_path: str = "data/"):
    rainfall = spark.read.csv(f"{data_path}rainfall.csv", header=True, inferSchema=True)
    events = spark.read.csv(f"{data_path}flood_events.csv", header=True, inferSchema=True)
    risk = spark.read.csv(f"{data_path}risk_scores.csv", header=True, inferSchema=True)
    return rainfall, events, risk


def compute_rolling_rainfall(rainfall_df):
    """7-day and 30-day rolling rainfall totals per state."""
    w7 = Window.partitionBy("state").orderBy("date").rowsBetween(-6, 0)
    w30 = Window.partitionBy("state").orderBy("date").rowsBetween(-29, 0)
    return (
        rainfall_df
        .withColumn("date", F.to_date("date"))
        .withColumn("rolling_7d_mm", F.sum("rainfall_mm").over(w7))
        .withColumn("rolling_30d_mm", F.sum("rainfall_mm").over(w30))
    )


def compute_flood_risk_index(rainfall_df, risk_df):
    """Join rolling rainfall with static risk scores to compute composite flood index."""
    latest = (
        rainfall_df
        .groupBy("state", "lat", "lon", "elevation_m", "flood_zone")
        .agg(
            F.avg("rolling_7d_mm").alias("avg_7d_rainfall"),
            F.avg("rolling_30d_mm").alias("avg_30d_rainfall"),
        )
    )
    joined = latest.join(
        risk_df.select("state", "risk_score", "river_proximity_km",
                       "population_at_risk", "drainage_quality"),
        on="state", how="left"
    )
    drainage_map = {"Poor": 0.8, "Fair": 0.5, "Good": 0.2}
    drainage_udf = F.udf(lambda d: drainage_map.get(d, 0.5), DoubleType())
    return (
        joined
        .withColumn("drainage_factor", drainage_udf(F.col("drainage_quality")))
        .withColumn(
            "composite_flood_index",
            (
                F.col("risk_score") * 0.35
                + (F.col("avg_7d_rainfall") / 100) * 0.30
                + F.col("drainage_factor") * 0.20
                + ((200 - F.col("elevation_m")) / 200).cast(DoubleType()) * 0.15
            ).cast(DoubleType())
        )
        .withColumn(
            "alert_level",
            F.when(F.col("composite_flood_index") >= 0.70, "RED")
             .when(F.col("composite_flood_index") >= 0.45, "ORANGE")
             .otherwise("GREEN")
        )
    )


def train_severity_model(events_df):
    """Train a GBT regressor to predict displaced persons from event features."""
    zone_map = {"coastal": 3.0, "riverine": 2.0, "inland": 1.0, "highland": 0.5}
    zone_udf = F.udf(lambda z: zone_map.get(z, 1.0), DoubleType())
    df = events_df.withColumn("zone_num", zone_udf(F.col("flood_zone")))

    assembler = VectorAssembler(
        inputCols=["flood_risk_score", "affected_area_km2", "zone_num"],
        outputCol="features"
    )
    scaler = StandardScaler(inputCol="features", outputCol="scaled_features")
    gbt = GBTRegressor(featuresCol="scaled_features", labelCol="displaced_persons", maxIter=20)
    pipeline = Pipeline(stages=[assembler, scaler, gbt])

    train, test = df.randomSplit([0.8, 0.2], seed=42)
    model = pipeline.fit(train)
    predictions = model.transform(test)
    return model, predictions


def save_results(flood_index_df, output_path: str = "data/flood_index_output.csv"):
    """Write results — swap path for Azure Blob: wasbs://container@account.blob.core.windows.net/"""
    flood_index_df.toPandas().to_csv(output_path, index=False)
    print(f"Results written to {output_path}")


if __name__ == "__main__":
    spark = get_spark()
    rainfall_df, events_df, risk_df = load_data(spark)
    rainfall_rolling = compute_rolling_rainfall(rainfall_df)
    flood_index = compute_flood_risk_index(rainfall_rolling, risk_df)
    flood_index.show(10)
    model, preds = train_severity_model(events_df)
    save_results(flood_index)
    spark.stop()
