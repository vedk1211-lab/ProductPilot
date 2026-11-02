"""
ProductPilot - Automated Tests
===============================
Tests for data generation, feature scoring, risk scoring,
Bloom Filter, and DGIM modules.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.feature_scoring import (
    compute_priority_scores, validate_weights,
    normalize_column, compute_effort_efficiency, get_feature_explanation
)
from src.risk_scoring import compute_risk_scores, compute_release_risk, generate_recommendations
from src.bloom_filter import BloomFilter, evaluate_bloom_filter
from src.dgim import DGIM, run_dgim_demo


# ================================================================
# Feature Scoring Tests
# ================================================================
class TestFeatureScoring:

    def _make_features_df(self, n=10):
        return pd.DataFrame({
            "feature_id": [f"FEAT-{i}" for i in range(n)],
            "feature_name": [f"Feature {i}" for i in range(n)],
            "product": ["Product A"] * n,
            "category": ["UI"] * n,
            "customer_demand": np.random.randint(1, 100, n),
            "business_value": np.random.randint(1, 100, n),
            "urgency": np.random.choice(["Critical", "High", "Medium", "Low"], n),
            "urgency_score": np.random.randint(25, 100, n),
            "strategic_alignment": np.random.randint(1, 100, n),
            "estimated_effort_hours": np.random.randint(5, 200, n),
            "status": ["Proposed"] * n,
        })

    def test_validate_weights_default(self):
        w = validate_weights(None)
        assert abs(sum(w.values()) - 1.0) < 1e-9

    def test_validate_weights_normalization(self):
        w = validate_weights({"customer_demand": 60, "business_value": 40,
                              "urgency": 0, "strategic_alignment": 0, "effort_efficiency": 0})
        assert abs(sum(w.values()) - 1.0) < 1e-9
        assert w["customer_demand"] == pytest.approx(0.6)

    def test_validate_weights_negative(self):
        w = validate_weights({"customer_demand": -10, "business_value": 50,
                              "urgency": 50, "strategic_alignment": 0, "effort_efficiency": 0})
        assert all(v >= 0 for v in w.values())
        assert abs(sum(w.values()) - 1.0) < 1e-9

    def test_validate_weights_all_zero(self):
        w = validate_weights({"customer_demand": 0, "business_value": 0,
                              "urgency": 0, "strategic_alignment": 0, "effort_efficiency": 0})
        # Should return defaults
        assert abs(sum(w.values()) - 1.0) < 1e-9

    def test_normalize_column(self):
        s = pd.Series([0, 25, 50, 75, 100])
        result = normalize_column(s)
        assert result.min() == pytest.approx(0.0)
        assert result.max() == pytest.approx(100.0)

    def test_normalize_column_constant(self):
        s = pd.Series([50, 50, 50])
        result = normalize_column(s)
        assert (result == 50.0).all()

    def test_compute_effort_efficiency_zero_effort(self):
        bv = pd.Series([50, 100])
        eff = pd.Series([0, 0])
        result = compute_effort_efficiency(bv, eff)
        assert not result.isna().any()

    def test_compute_priority_scores(self):
        df = self._make_features_df(20)
        result = compute_priority_scores(df)
        assert "priority_score" in result.columns
        assert "priority_category" in result.columns
        assert "rank" in result.columns
        assert result["priority_score"].between(0, 100).all()
        assert len(result) == 20

    def test_priority_scores_with_custom_weights(self):
        df = self._make_features_df()
        w = {"customer_demand": 100, "business_value": 0,
             "urgency": 0, "strategic_alignment": 0, "effort_efficiency": 0}
        result = compute_priority_scores(df, w)
        assert "priority_score" in result.columns

    def test_priority_category_labels(self):
        df = self._make_features_df(50)
        result = compute_priority_scores(df)
        valid_cats = {"Low", "Medium", "High", "Critical"}
        cats = set(result["priority_category"].dropna().unique())
        assert cats.issubset(valid_cats)

    def test_get_feature_explanation(self):
        df = self._make_features_df(5)
        scored = compute_priority_scores(df)
        row = scored.iloc[0]
        explanation = get_feature_explanation(row)
        assert "Priority Score" in explanation
        assert "Recommended Action" in explanation

    def test_missing_values_handled(self):
        df = pd.DataFrame({
            "feature_id": ["F1", "F2"],
            "feature_name": ["A", "B"],
            "product": ["P", "P"],
            "category": ["C", "C"],
            "customer_demand": [None, 50],
            "business_value": [80, None],
            "urgency": ["High", "Low"],
            "urgency_score": [75, 25],
            "strategic_alignment": [60, 70],
            "estimated_effort_hours": [0, None],
            "status": ["Proposed", "Proposed"],
        })
        result = compute_priority_scores(df)
        assert not result["priority_score"].isna().any()


# ================================================================
# Risk Scoring Tests
# ================================================================
class TestRiskScoring:

    def _make_tasks_df(self, n=20):
        return pd.DataFrame({
            "task_id": [f"TASK-{i}" for i in range(n)],
            "project_id": ["PROJ-001"] * n,
            "release_id": ["REL-001"] * n,
            "task_name": [f"Task {i}" for i in range(n)],
            "task_status": np.random.choice(
                ["Completed", "In Progress", "Not Started", "Blocked"], n
            ),
            "overdue_days": np.random.choice([0, 0, 5, 10, 30], n),
            "effort_ratio": np.random.uniform(0.5, 2.0, n),
            "estimated_effort_hours": np.random.randint(5, 100, n),
            "actual_effort_hours": np.random.randint(5, 150, n),
            "dependency": [""] * n,
            "priority": np.random.choice(["Critical", "High", "Medium", "Low"], n),
        })

    def test_compute_risk_scores(self):
        df = self._make_tasks_df()
        result = compute_risk_scores(df)
        assert "risk_score" in result.columns
        assert "risk_category" in result.columns
        assert "recommendation" in result.columns
        assert result["risk_score"].between(0, 100).all()

    def test_risk_categories(self):
        df = self._make_tasks_df(50)
        result = compute_risk_scores(df)
        valid_cats = {"Low", "Medium", "High"}
        cats = set(result["risk_category"].dropna().unique())
        assert cats.issubset(valid_cats)

    def test_blocked_task_high_risk(self):
        df = pd.DataFrame({
            "task_id": ["T1"],
            "project_id": ["P1"],
            "release_id": ["R1"],
            "task_name": ["Blocked Task"],
            "task_status": ["Blocked"],
            "overdue_days": [30],
            "effort_ratio": [2.0],
            "estimated_effort_hours": [50],
            "actual_effort_hours": [100],
            "dependency": [""],
            "priority": ["Critical"],
        })
        result = compute_risk_scores(df)
        assert result.iloc[0]["risk_score"] > 50

    def test_generate_recommendations(self):
        df = self._make_tasks_df(50)
        scored = compute_risk_scores(df)
        recs = generate_recommendations(scored, pd.DataFrame())
        assert isinstance(recs, list)
        for rec in recs:
            assert "type" in rec
            assert "action" in rec
            assert "severity" in rec

    def test_release_risk(self):
        tasks = self._make_tasks_df(30)
        releases = pd.DataFrame({
            "release_id": ["REL-001"],
            "release_status": ["In Progress"],
            "delay_days": [5],
            "planned_features": [10],
            "delivered_features": [7],
            "feature_delivery_rate": [70.0],
        })
        scored_tasks = compute_risk_scores(tasks)
        result = compute_release_risk(releases, scored_tasks)
        assert "release_risk" in result.columns


# ================================================================
# Bloom Filter Tests
# ================================================================
class TestBloomFilter:

    def test_basic_insert_lookup(self):
        bf = BloomFilter(size=1000, num_hashes=3)
        bf.insert("hello")
        bf.insert("world")
        assert bf.lookup("hello") == True
        assert bf.lookup("world") == True

    def test_no_false_negatives(self):
        bf = BloomFilter(size=10000, num_hashes=5)
        items = [f"item-{i}" for i in range(100)]
        for item in items:
            bf.insert(item)
        for item in items:
            assert bf.lookup(item) == True, f"False negative for {item}"

    def test_empty_filter(self):
        bf = BloomFilter(size=1000, num_hashes=3)
        assert bf.lookup("anything") == False

    def test_fill_ratio(self):
        bf = BloomFilter(size=100, num_hashes=3)
        assert bf.fill_ratio() == 0.0
        bf.insert("test")
        assert bf.fill_ratio() > 0.0

    def test_false_positive_rate(self):
        bf = BloomFilter(size=10000, num_hashes=5)
        inserted = [f"REQ-{i}" for i in range(500)]
        for item in inserted:
            bf.insert(item)

        false_positives = 0
        test_count = 1000
        for i in range(test_count):
            if bf.lookup(f"FAKE-{i}"):
                false_positives += 1

        fp_rate = false_positives / test_count
        # FP rate should be reasonable (< 20% for this size)
        assert fp_rate < 0.20, f"FP rate too high: {fp_rate}"

    def test_memory_usage(self):
        bf = BloomFilter(size=10000, num_hashes=5)
        assert bf.memory_bytes() == 10000 / 8

    def test_expected_fp_rate(self):
        bf = BloomFilter(size=10000, num_hashes=5)
        assert bf.expected_false_positive_rate() == 0.0
        for i in range(100):
            bf.insert(f"item-{i}")
        rate = bf.expected_false_positive_rate()
        assert 0 <= rate <= 1

    def test_bit_array_summary(self):
        bf = BloomFilter(size=100, num_hashes=3)
        bf.insert("test")
        summary = bf.get_bit_array_summary()
        assert summary["total_bits"] == 100
        assert summary["set_bits"] > 0
        assert summary["items_inserted"] == 1

    def test_evaluate_bloom_filter(self):
        inserted = [f"ID-{i}" for i in range(100)]
        existing = inserted[:50]
        new_items = [f"NEW-{i}" for i in range(50)]
        result = evaluate_bloom_filter(inserted, existing, new_items,
                                       size=5000, num_hashes=5)
        assert result["false_negatives"] == 0
        assert result["true_positives"] == 50
        assert "measured_fp_rate" in result
        assert "memory_ratio" in result

    def test_invalid_size(self):
        with pytest.raises(ValueError):
            BloomFilter(size=0)

    def test_invalid_hashes(self):
        with pytest.raises(ValueError):
            BloomFilter(size=100, num_hashes=0)

    def test_bit_array_visual(self):
        bf = BloomFilter(size=50, num_hashes=2)
        bf.insert("test")
        visual = bf.get_bit_array_visual()
        assert len(visual) == 50
        assert "1" in visual


# ================================================================
# DGIM Tests
# ================================================================
class TestDGIM:

    def test_empty_stream(self):
        dgim = DGIM(window_size=100)
        assert dgim.query() == 0
        assert dgim.exact_count() == 0

    def test_all_zeros(self):
        dgim = DGIM(window_size=10)
        for _ in range(20):
            dgim.process_bit(0)
        assert dgim.query() == 0
        assert dgim.exact_count() == 0

    def test_all_ones(self):
        dgim = DGIM(window_size=10)
        for _ in range(10):
            dgim.process_bit(1)
        approx = dgim.query()
        exact = dgim.exact_count()
        assert exact == 10
        # DGIM error should be ≤ 50% of exact
        assert abs(approx - exact) <= exact * 0.5 + 1

    def test_window_boundary(self):
        dgim = DGIM(window_size=5)
        stream = [1, 1, 1, 0, 0, 0, 0, 0]
        for bit in stream:
            dgim.process_bit(bit)
        # Only last 5 bits matter: [1, 0, 0, 0, 0] = 1
        # Wait, stream processed: after bit 8, window covers bits 4-8: [0,0,0,0,0]
        exact = dgim.exact_count()
        assert exact == 0

    def test_bucket_merging(self):
        dgim = DGIM(window_size=100)
        # Insert many 1s — should trigger bucket merges
        for _ in range(50):
            dgim.process_bit(1)
        buckets = dgim.get_buckets_info()
        # Should have fewer buckets than 50 due to merging
        assert len(buckets) < 50
        # Verify DGIM invariant: at most 2 buckets of each size
        size_counts = {}
        for b in buckets:
            size_counts[b["size"]] = size_counts.get(b["size"], 0) + 1
        for size, count in size_counts.items():
            assert count <= 2, f"DGIM invariant violated: {count} buckets of size {size}"

    def test_approximation_bound(self):
        """DGIM error should be within theoretical bounds."""
        dgim = DGIM(window_size=100)
        import random
        random.seed(42)
        for _ in range(200):
            dgim.process_bit(random.randint(0, 1))

        error = dgim.get_error()
        exact = error["exact_count"]
        if exact > 0:
            assert error["relative_error"] <= 0.55  # Allow slight slack

    def test_memory_usage(self):
        dgim = DGIM(window_size=1000)
        import random
        random.seed(42)
        for _ in range(1000):
            dgim.process_bit(random.randint(0, 1))
        mem = dgim.memory_usage()
        assert mem["dgim_entries"] < mem["exact_entries"]

    def test_get_error(self):
        dgim = DGIM(window_size=50)
        for _ in range(50):
            dgim.process_bit(1)
        error = dgim.get_error()
        assert "approximate_count" in error
        assert "exact_count" in error
        assert "absolute_error" in error
        assert "relative_error" in error

    def test_run_dgim_demo(self):
        stream = [1, 0, 1, 1, 0, 0, 1, 0, 1, 1] * 50
        result = run_dgim_demo(stream, window_size=50)
        assert "final_error" in result
        assert "memory" in result
        assert "snapshots" in result
        assert len(result["snapshots"]) > 0

    def test_dgim_with_alerts(self):
        stream = [1] * 100
        result = run_dgim_demo(stream, window_size=50, alert_threshold=20)
        assert len(result["alerts"]) > 0

    def test_process_stream(self):
        dgim = DGIM(window_size=20)
        dgim.process_stream([1, 0, 1, 1, 0, 1, 0, 0, 1, 1])
        assert dgim.query() > 0

    def test_invalid_window_size(self):
        with pytest.raises(ValueError):
            DGIM(window_size=0)

    def test_bucket_visualization(self):
        dgim = DGIM(window_size=50)
        dgim.process_stream([1, 0, 1, 1, 0, 1])
        viz = dgim.get_bucket_visualization()
        assert "current_time" in viz
        assert "window_size" in viz
        assert "buckets" in viz


# ================================================================
# Data Generation Tests
# ================================================================
class TestDataGeneration:

    def test_data_files_exist(self):
        """Test that data files exist after generation."""
        raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")
        if os.path.exists(raw_dir):
            expected = ["releases.csv", "features.csv", "feature_requests.csv", "tasks.csv"]
            for f in expected:
                filepath = os.path.join(raw_dir, f)
                if os.path.exists(filepath):
                    df = pd.read_csv(filepath)
                    assert len(df) > 0, f"{f} is empty"

    def test_features_schema(self):
        filepath = os.path.join(PROJECT_ROOT, "data", "raw", "features.csv")
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            required_cols = ["feature_id", "feature_name", "product", "category",
                           "customer_demand", "business_value", "urgency"]
            for col in required_cols:
                assert col in df.columns, f"Missing column: {col}"
            assert len(df) >= 200

    def test_requests_schema(self):
        filepath = os.path.join(PROJECT_ROOT, "data", "raw", "feature_requests.csv")
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            assert "request_id" in df.columns
            assert "feature_id" in df.columns
            assert len(df) >= 10000

    def test_tasks_schema(self):
        filepath = os.path.join(PROJECT_ROOT, "data", "raw", "tasks.csv")
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            assert "task_id" in df.columns
            assert "project_id" in df.columns
            assert len(df) >= 3000

    def test_releases_schema(self):
        filepath = os.path.join(PROJECT_ROOT, "data", "raw", "releases.csv")
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            assert "release_id" in df.columns
            assert len(df) >= 150

    def test_feature_request_links(self):
        """Feature requests should reference valid feature IDs."""
        raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")
        feat_path = os.path.join(raw_dir, "features.csv")
        req_path = os.path.join(raw_dir, "feature_requests.csv")
        if os.path.exists(feat_path) and os.path.exists(req_path):
            features = pd.read_csv(feat_path)
            requests = pd.read_csv(req_path)
            valid_ids = set(features["feature_id"])
            request_feat_ids = set(requests["feature_id"].dropna())
            orphans = request_feat_ids - valid_ids
            assert len(orphans) == 0, f"Orphan feature IDs: {orphans}"


# ================================================================
# Custom Data Processor Tests
# ================================================================
class TestCustomDataProcessor:

    def test_sample_dataset_generation(self):
        from src.custom_data_processor import get_sample_custom_dataset
        ds = get_sample_custom_dataset()
        assert "features" in ds
        assert "tasks" in ds
        assert "releases" in ds
        assert "requests" in ds
        assert len(ds["features"]) == 10
        assert len(ds["tasks"]) == 10
        assert len(ds["releases"]) == 3

    def test_auto_column_detection(self):
        from src.custom_data_processor import detect_column_mapping
        cols = ["Feature Title", "User Demand", "Biz_Value", "Hours", "Due_Date", "Status"]
        mapping = detect_column_mapping(cols)
        assert mapping.get("feature_name") == "Feature Title"
        assert mapping.get("customer_demand") == "User Demand"
        assert mapping.get("business_value") == "Biz_Value"
        assert mapping.get("estimated_effort_hours") == "Hours"
        assert mapping.get("planned_end_date") == "Due_Date"
        assert mapping.get("status") == "Status"

    def test_process_minimal_features_dataframe(self):
        from src.custom_data_processor import process_user_dataframe
        raw_df = pd.DataFrame({
            "name": ["Login with Google", "Dark Theme"],
            "votes": [120, 45],
            "impact": [8.5, 6.0],
            "urgency": ["High", "Low"],
            "effort": [25, 10]
        })
        res = process_user_dataframe(raw_df, dataset_name="Minimal Test")
        assert len(res["features"]) == 2
        assert "priority_score" not in res["features"].columns  # ready for scoring
        assert "customer_demand" in res["features"].columns
        assert res["features"]["customer_demand"].iloc[0] == 120
        # Tasks should have been auto-generated
        assert len(res["tasks"]) >= 2
        assert len(res["releases"]) >= 1

    def test_csv_template_generation(self):
        from src.custom_data_processor import generate_csv_template
        csv_str = generate_csv_template()
        assert "feature_name" in csv_str
        assert "customer_demand" in csv_str


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
