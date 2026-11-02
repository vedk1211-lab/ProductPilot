"""
ProductPilot - Big Data Processing Pipeline
============================================
Supports Apache Spark (PySpark local[*]) with a seamless standalone
analytics engine (Pandas/PyArrow) fallback if PySpark is not installed.
Validates schemas, data types, missing values, duplicates, transforms data,
computes analytical aggregations, and saves processed outputs in Parquet format.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ProductPilot.Pipeline")

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# PySpark Availability Check
try:
    import pyspark
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F
    from pyspark.sql.types import (
        StructType, StructField, StringType, IntegerType, DateType, DoubleType
    )
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


def check_environment():
    """Check Python, Java, and Spark environment."""
    info = {
        "python_version": sys.version.split()[0],
        "java_home": os.environ.get("JAVA_HOME", "Not set in environment"),
        "pyspark_installed": PYSPARK_AVAILABLE,
    }
    return info


# ================================================================
# Common Validation Result
# ================================================================
class ValidationResult:
    """Stores validation results for a dataset."""
    def __init__(self, name):
        self.name = name
        self.total_rows = 0
        self.valid_rows = 0
        self.null_counts = {}
        self.duplicate_ids = 0
        self.invalid_records = 0
        self.issues = []

    def to_dict(self):
        return {
            "dataset": self.name,
            "total_rows": self.total_rows,
            "valid_rows": self.valid_rows,
            "null_counts": self.null_counts,
            "duplicate_ids": self.duplicate_ids,
            "invalid_records": self.invalid_records,
            "issues": self.issues
        }


# ================================================================
# PySpark Engine Implementation
# ================================================================
if PYSPARK_AVAILABLE:
    def get_spark_session(app_name="ProductPilot"):
        """Create or retrieve a local Spark session."""
        spark = (
            SparkSession.builder
            .appName(app_name)
            .master("local[*]")
            .config("spark.sql.warehouse.dir", os.path.join(BASE_DIR, "spark-warehouse"))
            .config("spark.driver.memory", "2g")
            .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")
        return spark

    RELEASES_SCHEMA = StructType([
        StructField("release_id", StringType(), False),
        StructField("planned_release_date", StringType(), True),
        StructField("actual_release_date", StringType(), True),
        StructField("planned_features", StringType(), True),
        StructField("delivered_features", StringType(), True),
        StructField("planned_effort_hours", StringType(), True),
        StructField("actual_effort_hours", StringType(), True),
        StructField("delay_days", StringType(), True),
        StructField("release_status", StringType(), True),
    ])

    FEATURES_SCHEMA = StructType([
        StructField("feature_id", StringType(), False),
        StructField("feature_name", StringType(), True),
        StructField("product", StringType(), True),
        StructField("category", StringType(), True),
        StructField("customer_demand", StringType(), True),
        StructField("business_value", StringType(), True),
        StructField("urgency", StringType(), True),
        StructField("strategic_alignment", StringType(), True),
        StructField("estimated_effort_hours", StringType(), True),
        StructField("release_id", StringType(), True),
        StructField("status", StringType(), True),
    ])

    REQUESTS_SCHEMA = StructType([
        StructField("request_id", StringType(), False),
        StructField("feature_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("request_date", StringType(), True),
        StructField("demand_votes", StringType(), True),
        StructField("customer_segment", StringType(), True),
        StructField("urgency", StringType(), True),
        StructField("business_value", StringType(), True),
        StructField("strategic_alignment", StringType(), True),
        StructField("estimated_effort_hours", StringType(), True),
        StructField("status", StringType(), True),
    ])

    TASKS_SCHEMA = StructType([
        StructField("task_id", StringType(), False),
        StructField("project_id", StringType(), True),
        StructField("release_id", StringType(), True),
        StructField("task_name", StringType(), True),
        StructField("start_date", StringType(), True),
        StructField("planned_end_date", StringType(), True),
        StructField("actual_end_date", StringType(), True),
        StructField("estimated_effort_hours", StringType(), True),
        StructField("actual_effort_hours", StringType(), True),
        StructField("dependency", StringType(), True),
        StructField("task_status", StringType(), True),
        StructField("priority", StringType(), True),
    ])

    def load_csv_spark(spark, filename, schema):
        filepath = os.path.join(RAW_DIR, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Data file not found: {filepath}")
        return spark.read.option("header", "true").option("inferSchema", "false").schema(schema).csv(filepath)

    def validate_dataset_spark(df, name, id_col):
        val = ValidationResult(name)
        total = df.count()
        val.total_rows = total
        for col_name in df.columns:
            null_count = df.filter(F.col(col_name).isNull() | (F.trim(F.col(col_name)) == "")).count()
            val.null_counts[col_name] = null_count
        id_counts = df.groupBy(id_col).count().filter(F.col("count") > 1)
        val.duplicate_ids = id_counts.count()
        if val.duplicate_ids > 0:
            val.issues.append(f"Found {val.duplicate_ids} duplicate {id_col} values")
        val.valid_rows = total - val.duplicate_ids
        return val

    def clean_features_spark(df):
        return (
            df
            .withColumn("customer_demand", F.col("customer_demand").cast(IntegerType()))
            .withColumn("business_value", F.col("business_value").cast(IntegerType()))
            .withColumn("strategic_alignment", F.col("strategic_alignment").cast(IntegerType()))
            .withColumn("estimated_effort_hours", F.col("estimated_effort_hours").cast(IntegerType()))
            .fillna({"customer_demand": 50, "business_value": 50, "estimated_effort_hours": 40})
            .withColumn("urgency_score", F.when(F.col("urgency") == "Critical", 100)
                         .when(F.col("urgency") == "High", 75)
                         .when(F.col("urgency") == "Medium", 50)
                         .when(F.col("urgency") == "Low", 25)
                         .otherwise(50))
        )

    def clean_requests_spark(df):
        return (
            df
            .withColumn("demand_votes", F.col("demand_votes").cast(IntegerType()))
            .withColumn("business_value", F.col("business_value").cast(IntegerType()))
            .withColumn("strategic_alignment", F.col("strategic_alignment").cast(IntegerType()))
            .withColumn("estimated_effort_hours", F.col("estimated_effort_hours").cast(IntegerType()))
            .withColumn("request_date", F.to_date(F.col("request_date"), "yyyy-MM-dd"))
            .fillna({"demand_votes": 1, "business_value": 50})
        )

    def clean_tasks_spark(df):
        return (
            df
            .withColumn("estimated_effort_hours", F.col("estimated_effort_hours").cast(IntegerType()))
            .withColumn("actual_effort_hours", F.col("actual_effort_hours").cast(IntegerType()))
            .withColumn("start_date", F.to_date(F.col("start_date"), "yyyy-MM-dd"))
            .withColumn("planned_end_date", F.to_date(F.col("planned_end_date"), "yyyy-MM-dd"))
            .withColumn("actual_end_date",
                         F.when(F.trim(F.col("actual_end_date")) != "",
                                F.to_date(F.col("actual_end_date"), "yyyy-MM-dd"))
                         .otherwise(F.lit(None).cast(DateType())))
            .fillna({"estimated_effort_hours": 20})
            .withColumn("reference_date", F.lit("2026-10-22").cast(DateType()))
            .withColumn("overdue_days",
                         F.when(
                             (F.col("task_status").isin("Not Started", "In Progress", "Blocked")) &
                             (F.col("planned_end_date") < F.col("reference_date")),
                             F.datediff(F.col("reference_date"), F.col("planned_end_date"))
                         ).otherwise(
                             F.when(
                                 (F.col("task_status") == "Completed") & F.col("actual_end_date").isNotNull(),
                                 F.greatest(F.lit(0), F.datediff(F.col("actual_end_date"), F.col("planned_end_date")))
                             ).otherwise(0)
                         ))
            .withColumn("effort_ratio",
                         F.when(
                             (F.col("estimated_effort_hours").isNotNull()) &
                             (F.col("estimated_effort_hours") > 0) &
                             (F.col("actual_effort_hours").isNotNull()),
                             F.col("actual_effort_hours") / F.col("estimated_effort_hours")
                         ).otherwise(F.lit(None).cast(DoubleType())))
            .drop("reference_date")
        )

    def clean_releases_spark(df):
        return (
            df
            .withColumn("planned_features", F.col("planned_features").cast(IntegerType()))
            .withColumn("delivered_features", F.col("delivered_features").cast(IntegerType()))
            .withColumn("planned_effort_hours", F.col("planned_effort_hours").cast(IntegerType()))
            .withColumn("actual_effort_hours", F.col("actual_effort_hours").cast(IntegerType()))
            .withColumn("delay_days", F.col("delay_days").cast(IntegerType()))
            .withColumn("planned_release_date", F.to_date(F.col("planned_release_date"), "yyyy-MM-dd"))
            .withColumn("actual_release_date",
                         F.when(F.trim(F.col("actual_release_date")) != "",
                                F.to_date(F.col("actual_release_date"), "yyyy-MM-dd"))
                         .otherwise(F.lit(None).cast(DateType())))
            .fillna({"delay_days": 0, "delivered_features": 0, "actual_effort_hours": 0})
            .withColumn("feature_delivery_rate",
                         F.when(F.col("planned_features") > 0,
                                F.round(F.col("delivered_features") / F.col("planned_features") * 100, 1))
                         .otherwise(0.0))
            .withColumn("effort_variance_pct",
                         F.when(F.col("planned_effort_hours") > 0,
                                F.round((F.col("actual_effort_hours") - F.col("planned_effort_hours"))
                                        / F.col("planned_effort_hours") * 100, 1))
                         .otherwise(0.0))
        )

    def compute_aggregations_spark(spark, features_df, requests_df, tasks_df, releases_df):
        demand_agg = (
            requests_df
            .groupBy("feature_id")
            .agg(
                F.count("request_id").alias("total_requests"),
                F.sum("demand_votes").alias("total_votes"),
                F.countDistinct("customer_id").alias("unique_customers"),
                F.countDistinct("customer_segment").alias("segment_diversity"),
                F.avg("business_value").alias("avg_request_bv"),
            )
        )
        features_enriched = (
            features_df
            .join(demand_agg, "feature_id", "left")
            .fillna({"total_requests": 0, "total_votes": 0, "unique_customers": 0, "segment_diversity": 0})
        )
        task_release_agg = (
            tasks_df
            .groupBy("release_id")
            .agg(
                F.count("task_id").alias("total_tasks"),
                F.sum(F.when(F.col("task_status") == "Completed", 1).otherwise(0)).alias("completed_tasks"),
                F.sum(F.when(F.col("task_status") == "In Progress", 1).otherwise(0)).alias("in_progress_tasks"),
                F.sum(F.when(F.col("task_status") == "Blocked", 1).otherwise(0)).alias("blocked_tasks"),
                F.sum(F.when(F.col("overdue_days") > 0, 1).otherwise(0)).alias("overdue_tasks"),
                F.avg("overdue_days").alias("avg_overdue_days"),
                F.max("overdue_days").alias("max_overdue_days"),
            )
        )
        releases_enriched = (
            releases_df
            .join(task_release_agg, "release_id", "left")
            .fillna({
                "total_tasks": 0, "completed_tasks": 0, "in_progress_tasks": 0,
                "blocked_tasks": 0, "overdue_tasks": 0, "avg_overdue_days": 0.0, "max_overdue_days": 0
            })
        )
        return features_enriched, releases_enriched

    def save_parquet_spark(df, name):
        path = os.path.join(PROCESSED_DIR, name)
        df.write.mode("overwrite").parquet(path)
        count = df.count()
        logger.info(f"Saved {name}: {count:,} records -> {path}")
        return count


# ================================================================
# Standalone Analytics Engine (Pandas/PyArrow)
# ================================================================
def run_standalone_pipeline():
    """High-performance Pandas/PyArrow implementation mirroring PySpark logic."""
    import pandas as pd
    import numpy as np

    start_time = time.time()
    logger.info("=" * 60)
    logger.info("ProductPilot - Analytics Pipeline (Engine: Pandas/PyArrow)")
    logger.info("=" * 60)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    results = {
        "engine": "Standalone Analytics Engine (Pandas/PyArrow)",
        "spark_available": PYSPARK_AVAILABLE,
        "validation": {},
        "counts": {}
    }

    # 1. Load CSVs
    releases_raw = pd.read_csv(os.path.join(RAW_DIR, "releases.csv"), dtype=str)
    features_raw = pd.read_csv(os.path.join(RAW_DIR, "features.csv"), dtype=str)
    requests_raw = pd.read_csv(os.path.join(RAW_DIR, "feature_requests.csv"), dtype=str)
    tasks_raw = pd.read_csv(os.path.join(RAW_DIR, "tasks.csv"), dtype=str)

    results["counts"]["raw_releases"] = len(releases_raw)
    results["counts"]["raw_features"] = len(features_raw)
    results["counts"]["raw_requests"] = len(requests_raw)
    results["counts"]["raw_tasks"] = len(tasks_raw)

    # 2. Validation
    for name, df, id_col in [
        ("releases", releases_raw, "release_id"),
        ("features", features_raw, "feature_id"),
        ("requests", requests_raw, "request_id"),
        ("tasks", tasks_raw, "task_id")
    ]:
        val = ValidationResult(name)
        val.total_rows = len(df)
        val.null_counts = {c: int(df[c].isnull().sum() + (df[c].str.strip() == "").sum()) for c in df.columns}
        val.duplicate_ids = int(df[id_col].duplicated().sum())
        val.valid_rows = len(df) - val.duplicate_ids
        results["validation"][name] = val.to_dict()

    # 3. Clean Features
    features_clean = features_raw.copy()
    for col in ["customer_demand", "business_value", "strategic_alignment", "estimated_effort_hours"]:
        features_clean[col] = pd.to_numeric(features_clean[col], errors="coerce")
    features_clean["customer_demand"] = features_clean["customer_demand"].fillna(50).astype(int)
    features_clean["business_value"] = features_clean["business_value"].fillna(50).astype(int)
    features_clean["strategic_alignment"] = features_clean["strategic_alignment"].fillna(50).astype(int)
    features_clean["estimated_effort_hours"] = features_clean["estimated_effort_hours"].fillna(40).astype(int)

    urgency_map = {"Critical": 100, "High": 75, "Medium": 50, "Low": 25}
    features_clean["urgency_score"] = features_clean["urgency"].map(urgency_map).fillna(50).astype(int)

    # 4. Clean Requests
    requests_clean = requests_raw.copy()
    for col in ["demand_votes", "business_value", "strategic_alignment", "estimated_effort_hours"]:
        requests_clean[col] = pd.to_numeric(requests_clean[col], errors="coerce")
    requests_clean["demand_votes"] = requests_clean["demand_votes"].fillna(1).astype(int)
    requests_clean["business_value"] = requests_clean["business_value"].fillna(50).astype(int)
    requests_clean["strategic_alignment"] = requests_clean["strategic_alignment"].fillna(50).astype(int)
    requests_clean["estimated_effort_hours"] = requests_clean["estimated_effort_hours"].fillna(20).astype(int)
    requests_clean["request_date"] = pd.to_datetime(requests_clean["request_date"], errors="coerce")

    # 5. Clean Tasks
    tasks_clean = tasks_raw.copy()
    tasks_clean["estimated_effort_hours"] = pd.to_numeric(tasks_clean["estimated_effort_hours"], errors="coerce").fillna(20).astype(int)
    tasks_clean["actual_effort_hours"] = pd.to_numeric(tasks_clean["actual_effort_hours"], errors="coerce")
    tasks_clean["start_date"] = pd.to_datetime(tasks_clean["start_date"], errors="coerce")
    tasks_clean["planned_end_date"] = pd.to_datetime(tasks_clean["planned_end_date"], errors="coerce")
    tasks_clean["actual_end_date"] = pd.to_datetime(tasks_clean["actual_end_date"], errors="coerce")

    ref_date = pd.to_datetime("2026-10-22")
    overdue_days = []
    for _, row in tasks_clean.iterrows():
        status = row["task_status"]
        planned = row["planned_end_date"]
        actual = row["actual_end_date"]
        if status in ["Not Started", "In Progress", "Blocked"] and pd.notnull(planned) and planned < ref_date:
            overdue_days.append(max(0, (ref_date - planned).days))
        elif status == "Completed" and pd.notnull(actual) and pd.notnull(planned):
            overdue_days.append(max(0, (actual - planned).days))
        else:
            overdue_days.append(0)
    tasks_clean["overdue_days"] = overdue_days

    tasks_clean["effort_ratio"] = np.where(
        (tasks_clean["estimated_effort_hours"] > 0) & tasks_clean["actual_effort_hours"].notnull(),
        tasks_clean["actual_effort_hours"] / tasks_clean["estimated_effort_hours"],
        np.nan
    )

    # 6. Clean Releases
    releases_clean = releases_raw.copy()
    for col in ["planned_features", "delivered_features", "planned_effort_hours", "actual_effort_hours", "delay_days"]:
        releases_clean[col] = pd.to_numeric(releases_clean[col], errors="coerce").fillna(0).astype(int)
    releases_clean["planned_release_date"] = pd.to_datetime(releases_clean["planned_release_date"], errors="coerce")
    releases_clean["actual_release_date"] = pd.to_datetime(releases_clean["actual_release_date"], errors="coerce")

    releases_clean["feature_delivery_rate"] = np.where(
        releases_clean["planned_features"] > 0,
        np.round(releases_clean["delivered_features"] / releases_clean["planned_features"] * 100, 1),
        0.0
    )
    releases_clean["effort_variance_pct"] = np.where(
        releases_clean["planned_effort_hours"] > 0,
        np.round((releases_clean["actual_effort_hours"] - releases_clean["planned_effort_hours"])
                 / releases_clean["planned_effort_hours"] * 100, 1),
        0.0
    )

    # 7. Aggregations
    demand_agg = requests_clean.groupby("feature_id").agg(
        total_requests=("request_id", "count"),
        total_votes=("demand_votes", "sum"),
        unique_customers=("customer_id", "nunique"),
        segment_diversity=("customer_segment", "nunique"),
        avg_request_bv=("business_value", "mean")
    ).reset_index()

    features_enriched = features_clean.merge(demand_agg, on="feature_id", how="left")
    features_enriched[["total_requests", "total_votes", "unique_customers", "segment_diversity"]] = (
        features_enriched[["total_requests", "total_votes", "unique_customers", "segment_diversity"]].fillna(0).astype(int)
    )

    task_release_agg = tasks_clean.groupby("release_id").agg(
        total_tasks=("task_id", "count"),
        completed_tasks=("task_status", lambda s: (s == "Completed").sum()),
        in_progress_tasks=("task_status", lambda s: (s == "In Progress").sum()),
        blocked_tasks=("task_status", lambda s: (s == "Blocked").sum()),
        overdue_tasks=("overdue_days", lambda o: (o > 0).sum()),
        avg_overdue_days=("overdue_days", "mean"),
        max_overdue_days=("overdue_days", "max")
    ).reset_index()

    releases_enriched = releases_clean.merge(task_release_agg, on="release_id", how="left")
    releases_enriched[["total_tasks", "completed_tasks", "in_progress_tasks", "blocked_tasks", "overdue_tasks", "max_overdue_days"]] = (
        releases_enriched[["total_tasks", "completed_tasks", "in_progress_tasks", "blocked_tasks", "overdue_tasks", "max_overdue_days"]].fillna(0).astype(int)
    )
    releases_enriched["avg_overdue_days"] = releases_enriched["avg_overdue_days"].fillna(0.0).round(1)

    # 8. Save Parquet
    for name, df in [
        ("features", features_enriched),
        ("requests", requests_clean),
        ("tasks", tasks_clean),
        ("releases", releases_enriched)
    ]:
        out_dir = os.path.join(PROCESSED_DIR, name)
        os.makedirs(out_dir, exist_ok=True)
        out_file = os.path.join(out_dir, "part-0.parquet")
        df.to_parquet(out_file, engine="pyarrow", index=False)
        results["counts"][f"processed_{name}"] = len(df)
        logger.info(f"Saved {name}: {len(df):,} records -> {out_dir}")

    elapsed = time.time() - start_time
    results["execution_time_seconds"] = round(elapsed, 2)
    results["completed_at"] = datetime.now().isoformat()

    # Save pipeline metadata
    meta_path = os.path.join(PROCESSED_DIR, "pipeline_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Pipeline metadata written to {meta_path}")
    logger.info(f"Pipeline finished in {elapsed:.2f}s")
    logger.info("=" * 60)

    return results


# ================================================================
# Unified Entry Point
# ================================================================
def run_pipeline(spark=None, engine="auto"):
    """
    Run data processing pipeline.
    engine: 'auto', 'spark', or 'fallback'
    """
    if engine == "spark" or (engine == "auto" and PYSPARK_AVAILABLE):
        if not PYSPARK_AVAILABLE:
            raise ImportError("PySpark is requested but not installed. Install with 'pip install pyspark'.")

        start_time = time.time()
        own_spark = spark is None
        if own_spark:
            spark = get_spark_session()

        logger.info("=" * 60)
        logger.info("ProductPilot - PySpark Data Pipeline")
        logger.info("=" * 60)
        logger.info(f"Spark version: {spark.version}")
        logger.info(f"Spark master: {spark.sparkContext.master}")

        os.makedirs(PROCESSED_DIR, exist_ok=True)
        results = {
            "engine": f"Apache Spark {spark.version} (local[*])",
            "spark_available": True,
            "spark_version": spark.version,
            "spark_master": spark.sparkContext.master,
            "validation": {},
            "counts": {}
        }

        # Load
        releases_raw = load_csv_spark(spark, "releases.csv", RELEASES_SCHEMA)
        features_raw = load_csv_spark(spark, "features.csv", FEATURES_SCHEMA)
        requests_raw = load_csv_spark(spark, "feature_requests.csv", REQUESTS_SCHEMA)
        tasks_raw = load_csv_spark(spark, "tasks.csv", TASKS_SCHEMA)

        results["counts"]["raw_releases"] = releases_raw.count()
        results["counts"]["raw_features"] = features_raw.count()
        results["counts"]["raw_requests"] = requests_raw.count()
        results["counts"]["raw_tasks"] = tasks_raw.count()

        # Validate
        results["validation"]["releases"] = validate_dataset_spark(releases_raw, "releases", "release_id").to_dict()
        results["validation"]["features"] = validate_dataset_spark(features_raw, "features", "feature_id").to_dict()
        results["validation"]["requests"] = validate_dataset_spark(requests_raw, "requests", "request_id").to_dict()
        results["validation"]["tasks"] = validate_dataset_spark(tasks_raw, "tasks", "task_id").to_dict()

        # Clean
        releases_clean = clean_releases_spark(releases_raw)
        features_clean = clean_features_spark(features_raw)
        requests_clean = clean_requests_spark(requests_raw)
        tasks_clean = clean_tasks_spark(tasks_raw)

        # Aggregations
        features_enriched, releases_enriched = compute_aggregations_spark(
            spark, features_clean, requests_clean, tasks_clean, releases_clean
        )

        # Save Parquet
        results["counts"]["processed_features"] = save_parquet_spark(features_enriched, "features")
        results["counts"]["processed_requests"] = save_parquet_spark(requests_clean, "requests")
        results["counts"]["processed_tasks"] = save_parquet_spark(tasks_clean, "tasks")
        results["counts"]["processed_releases"] = save_parquet_spark(releases_enriched, "releases")

        elapsed = time.time() - start_time
        results["execution_time_seconds"] = round(elapsed, 2)
        results["completed_at"] = datetime.now().isoformat()

        meta_path = os.path.join(PROCESSED_DIR, "pipeline_metadata.json")
        with open(meta_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        if own_spark:
            spark.stop()

        return results

    else:
        logger.info("Running standalone analytics engine.")
        return run_standalone_pipeline()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ProductPilot Data Pipeline")
    parser.add_argument("--engine", choices=["auto", "spark", "fallback"], default="auto")
    args = parser.parse_args()
    run_pipeline(engine=args.engine)
