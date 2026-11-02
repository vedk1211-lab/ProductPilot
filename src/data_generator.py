"""
ProductPilot - Synthetic Data Generation Script
================================================
Generates realistic, linked synthetic datasets for product management analytics.
All data is clearly synthetic and should not be mistaken for real company data.

Uses a fixed random seed (42) for full reproducibility.
"""

import os
import random
import csv
from datetime import datetime, timedelta
import argparse

# Fixed seed for reproducibility
SEED = 42
random.seed(SEED)

# --- Configuration ---
NUM_FEATURE_REQUESTS = 10000
NUM_FEATURES = 200
NUM_TASKS = 3000
NUM_RELEASES = 150

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

# --- Lookup Data ---
PRODUCTS = [
    "ProductPilot Core", "Analytics Suite", "Collaboration Hub",
    "Mobile Companion", "Integration Platform", "Security Shield",
    "Reporting Engine", "Workflow Automation"
]

CATEGORIES = [
    "User Interface", "API", "Performance", "Security",
    "Reporting", "Integration", "Data Management", "Notifications",
    "Authentication", "Search", "Export", "Dashboard"
]

CUSTOMER_SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Startup", "Government", "Education"]

URGENCY_LEVELS = ["Critical", "High", "Medium", "Low"]

STATUSES_FEATURE = ["Proposed", "Under Review", "Approved", "In Development", "Testing", "Released", "Deferred"]

STATUSES_TASK = ["Not Started", "In Progress", "Completed", "Blocked", "Cancelled"]

STATUSES_RELEASE = ["Planning", "In Progress", "Released", "Delayed", "Cancelled"]

FEATURE_NAME_PREFIXES = [
    "Enhanced", "Advanced", "Automated", "Real-time", "Custom",
    "Integrated", "Smart", "Streamlined", "Unified", "Dynamic"
]

FEATURE_NAME_SUFFIXES = [
    "Dashboard", "Analytics", "Reporting", "Notifications", "Search",
    "Export", "Import", "Sync", "Filtering", "Visualization",
    "Scheduling", "Alerts", "Audit Log", "Access Control", "API Gateway",
    "Data Pipeline", "Workflow", "Templates", "Bulk Operations", "User Management"
]

TASK_ACTIONS = [
    "Design", "Implement", "Test", "Review", "Document",
    "Deploy", "Migrate", "Refactor", "Optimize", "Configure",
    "Integrate", "Validate", "Monitor", "Debug", "Update"
]


def generate_feature_name(idx):
    """Generate a realistic feature name."""
    prefix = FEATURE_NAME_PREFIXES[idx % len(FEATURE_NAME_PREFIXES)]
    suffix = FEATURE_NAME_SUFFIXES[idx % len(FEATURE_NAME_SUFFIXES)]
    return f"{prefix} {suffix}"


def generate_releases(n):
    """Generate release history records."""
    releases = []
    base_date = datetime(2023, 1, 15)

    for i in range(n):
        release_id = f"REL-{i+1:04d}"
        # Releases are roughly every 2-4 weeks
        planned_date = base_date + timedelta(days=i * random.randint(7, 21))

        # Some releases are delayed
        delay_days = 0
        if random.random() < 0.35:
            delay_days = random.randint(1, 30)
        elif random.random() < 0.10:
            delay_days = random.randint(30, 60)

        actual_date = planned_date + timedelta(days=delay_days)

        planned_features = random.randint(3, 15)
        # Some features may not make it
        feature_drop = random.randint(0, min(3, planned_features - 1))
        delivered_features = planned_features - feature_drop

        planned_effort = random.randint(40, 400)
        effort_variance = random.uniform(-0.15, 0.40)
        actual_effort = max(10, int(planned_effort * (1 + effort_variance)))

        # Determine status
        if random.random() < 0.05:
            status = "Cancelled"
            actual_date = None
            delivered_features = 0
            actual_effort = int(planned_effort * random.uniform(0.1, 0.3))
            delay_days = 0
        elif planned_date > datetime(2026, 9, 1):
            status = random.choice(["Planning", "In Progress"])
            if status == "Planning":
                actual_date = None
                actual_effort = 0
                delivered_features = 0
                delay_days = 0
        else:
            status = "Released" if delay_days < 14 else "Delayed"

        releases.append({
            "release_id": release_id,
            "planned_release_date": planned_date.strftime("%Y-%m-%d"),
            "actual_release_date": actual_date.strftime("%Y-%m-%d") if actual_date else "",
            "planned_features": planned_features,
            "delivered_features": delivered_features,
            "planned_effort_hours": planned_effort,
            "actual_effort_hours": actual_effort,
            "delay_days": delay_days,
            "release_status": status
        })

    return releases


def generate_features(n, releases):
    """Generate product feature records linked to releases."""
    features = []
    release_ids = [r["release_id"] for r in releases]

    for i in range(n):
        feature_id = f"FEAT-{i+1:04d}"
        feature_name = generate_feature_name(i)
        product = PRODUCTS[i % len(PRODUCTS)]
        category = random.choice(CATEGORIES)

        customer_demand = random.randint(1, 100)
        business_value = random.randint(1, 100)
        urgency = random.choice(URGENCY_LEVELS)
        strategic_alignment = random.randint(1, 100)
        estimated_effort = random.randint(4, 200)

        # Assign to a release (some features unassigned)
        if random.random() < 0.85:
            release_id = random.choice(release_ids)
        else:
            release_id = ""

        status = random.choice(STATUSES_FEATURE)

        # Add some missing values (about 3% chance per numeric field)
        if random.random() < 0.03:
            customer_demand = ""
        if random.random() < 0.03:
            business_value = ""
        if random.random() < 0.02:
            estimated_effort = ""

        features.append({
            "feature_id": feature_id,
            "feature_name": feature_name,
            "product": product,
            "category": category,
            "customer_demand": customer_demand,
            "business_value": business_value,
            "urgency": urgency,
            "strategic_alignment": strategic_alignment,
            "estimated_effort_hours": estimated_effort,
            "release_id": release_id,
            "status": status
        })

    return features


def generate_feature_requests(n, features):
    """Generate feature request records linked to features."""
    requests = []
    feature_ids = [f["feature_id"] for f in features]

    for i in range(n):
        request_id = f"REQ-{i+1:06d}"
        feature_id = random.choice(feature_ids)
        customer_id = f"CUST-{random.randint(1, 500):04d}"

        # Spread requests over 2+ years
        request_date = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 1000))
        demand_votes = random.randint(1, 50)
        customer_segment = random.choice(CUSTOMER_SEGMENTS)
        urgency = random.choice(URGENCY_LEVELS)
        business_value = random.randint(1, 100)
        strategic_alignment = random.randint(1, 100)
        estimated_effort = random.randint(2, 100)

        status = random.choice(["Open", "Under Review", "Accepted", "Rejected", "Merged", "Completed"])

        # Missing values
        if random.random() < 0.02:
            demand_votes = ""
        if random.random() < 0.02:
            business_value = ""

        requests.append({
            "request_id": request_id,
            "feature_id": feature_id,
            "customer_id": customer_id,
            "request_date": request_date.strftime("%Y-%m-%d"),
            "demand_votes": demand_votes,
            "customer_segment": customer_segment,
            "urgency": urgency,
            "business_value": business_value,
            "strategic_alignment": strategic_alignment,
            "estimated_effort_hours": estimated_effort,
            "status": status
        })

    return requests


def generate_tasks(n, releases, features):
    """Generate project task records linked to releases and projects."""
    tasks = []
    release_ids = [r["release_id"] for r in releases]
    feature_ids = [f["feature_id"] for f in features]

    # Create project groups
    project_ids = [f"PROJ-{j+1:03d}" for j in range(30)]

    for i in range(n):
        task_id = f"TASK-{i+1:05d}"
        project_id = random.choice(project_ids)
        release_id = random.choice(release_ids)

        action = random.choice(TASK_ACTIONS)
        feature_ref = random.choice(feature_ids)
        task_name = f"{action} {feature_ref}"

        start_date = datetime(2023, 3, 1) + timedelta(days=random.randint(0, 900))
        planned_duration = random.randint(1, 45)
        planned_end = start_date + timedelta(days=planned_duration)

        estimated_effort = random.randint(4, 120)

        # Determine completion
        status = random.choice(STATUSES_TASK)
        actual_end = None
        actual_effort = None

        if status == "Completed":
            completion_variance = random.randint(-5, 20)
            actual_end = planned_end + timedelta(days=completion_variance)
            effort_variance = random.uniform(-0.2, 0.5)
            actual_effort = max(1, int(estimated_effort * (1 + effort_variance)))
        elif status == "In Progress":
            actual_effort = max(1, int(estimated_effort * random.uniform(0.2, 0.8)))
        elif status == "Blocked":
            actual_effort = max(1, int(estimated_effort * random.uniform(0.1, 0.4)))

        # Dependencies (some tasks depend on others)
        dependency = ""
        if i > 10 and random.random() < 0.30:
            dep_idx = random.randint(max(0, i - 50), i - 1)
            dependency = f"TASK-{dep_idx+1:05d}"

        priority = random.choice(["Critical", "High", "Medium", "Low"])

        # Missing values
        if random.random() < 0.02:
            estimated_effort = ""

        tasks.append({
            "task_id": task_id,
            "project_id": project_id,
            "release_id": release_id,
            "task_name": task_name,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "planned_end_date": planned_end.strftime("%Y-%m-%d"),
            "actual_end_date": actual_end.strftime("%Y-%m-%d") if actual_end else "",
            "estimated_effort_hours": estimated_effort,
            "actual_effort_hours": actual_effort if actual_effort is not None else "",
            "dependency": dependency,
            "task_status": status,
            "priority": priority
        })

    return tasks


def write_csv(filepath, data, fieldnames):
    """Write a list of dicts to a CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"  -> Wrote {len(data):,} records to {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic datasets for ProductPilot")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="Output directory for CSV files")
    parser.add_argument("--requests", type=int, default=NUM_FEATURE_REQUESTS, help="Number of feature requests")
    parser.add_argument("--features", type=int, default=NUM_FEATURES, help="Number of features")
    parser.add_argument("--tasks", type=int, default=NUM_TASKS, help="Number of project tasks")
    parser.add_argument("--releases", type=int, default=NUM_RELEASES, help="Number of releases")
    args = parser.parse_args()

    output_dir = args.output_dir
    print("=" * 60)
    print("ProductPilot - Synthetic Data Generation")
    print("=" * 60)
    print(f"NOTE: All data is SYNTHETIC, generated with seed={SEED}")
    print(f"Output directory: {output_dir}")
    print()

    # Generate in dependency order
    print("[1/4] Generating releases...")
    releases = generate_releases(args.releases)
    write_csv(
        os.path.join(output_dir, "releases.csv"),
        releases,
        ["release_id", "planned_release_date", "actual_release_date",
         "planned_features", "delivered_features", "planned_effort_hours",
         "actual_effort_hours", "delay_days", "release_status"]
    )

    print("[2/4] Generating product features...")
    features = generate_features(args.features, releases)
    write_csv(
        os.path.join(output_dir, "features.csv"),
        features,
        ["feature_id", "feature_name", "product", "category",
         "customer_demand", "business_value", "urgency", "strategic_alignment",
         "estimated_effort_hours", "release_id", "status"]
    )

    print("[3/4] Generating feature requests...")
    feature_requests = generate_feature_requests(args.requests, features)
    write_csv(
        os.path.join(output_dir, "feature_requests.csv"),
        feature_requests,
        ["request_id", "feature_id", "customer_id", "request_date",
         "demand_votes", "customer_segment", "urgency", "business_value",
         "strategic_alignment", "estimated_effort_hours", "status"]
    )

    print("[4/4] Generating project tasks...")
    tasks = generate_tasks(args.tasks, releases, features)
    write_csv(
        os.path.join(output_dir, "tasks.csv"),
        tasks,
        ["task_id", "project_id", "release_id", "task_name",
         "start_date", "planned_end_date", "actual_end_date",
         "estimated_effort_hours", "actual_effort_hours", "dependency",
         "task_status", "priority"]
    )

    print()
    print("Data generation complete!")
    print(f"  Releases:         {len(releases):>6,}")
    print(f"  Features:         {len(features):>6,}")
    print(f"  Feature Requests: {len(feature_requests):>6,}")
    print(f"  Tasks:            {len(tasks):>6,}")
    print()
    return releases, features, feature_requests, tasks


if __name__ == "__main__":
    main()
