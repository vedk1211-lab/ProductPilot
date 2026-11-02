"""
Dataset Generator for ProductPilot
===================================
Generates:
1. productpilot_dataset.csv: A comprehensive, unified CSV file matching the schema
   expected by ProductPilot's Data Workspace (features, tasks, WSJF scoring inputs, and release links).
2. data/generated/: Individual CSV files for features.csv, tasks.csv, releases.csv, and feature_requests.csv
   matching DATA_DICTIONARY.md specifications.
"""

import os
import random
import csv
from datetime import datetime, timedelta

SEED = 2026
random.seed(SEED)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "generated")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lookup Tables
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

PROJECT_IDS = ["PROJ-Atlas", "PROJ-Comply", "PROJ-Connect", "PROJ-Horizon", "PROJ-Nova"]
CUSTOMER_SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Startup", "Government"]
URGENCY_LEVELS = ["Critical", "High", "Medium", "Low"]
STATUSES_FEATURE = ["Proposed", "Under Review", "Approved", "In Development", "Testing", "Released", "Deferred"]
STATUSES_TASK = ["Not Started", "In Progress", "Completed", "Blocked", "Cancelled"]
STATUSES_RELEASE = ["Planning", "In Progress", "Released", "Delayed", "Cancelled"]

FEATURE_NAME_PREFIXES = [
    "Enhanced", "Advanced", "Automated", "Real-time", "Custom",
    "Integrated", "Smart", "Streamlined", "Unified", "Dynamic",
    "Predictive", "Intelligent", "Scalable", "Federated", "Interactive"
]

FEATURE_NAME_SUFFIXES = [
    "Dashboard", "Analytics", "Reporting", "Notifications", "Search",
    "Export", "Import", "Sync", "Filtering", "Visualization",
    "Scheduling", "Alerts", "Audit Log", "Access Control", "API Gateway",
    "Data Pipeline", "Workflow", "Templates", "Bulk Operations", "User Management"
]

TASK_ACTIONS = [
    "Design UI mockups for", "Implement API endpoints for", "Unit test and validate",
    "Code review implementation of", "Write documentation for", "Deploy to staging for",
    "Database schema migration for", "Refactor core logic for", "Performance optimize",
    "Configure authorization for", "Integrate webhooks for", "Run security audit on"
]

# Generate Releases (150 records)
releases = []
base_date = datetime(2024, 1, 15)
for i in range(150):
    rel_id = f"REL-{i+1:04d}"
    planned_dt = base_date + timedelta(days=i * random.randint(7, 21))
    
    delay = 0
    if random.random() < 0.35:
        delay = random.randint(1, 28)
    elif random.random() < 0.10:
        delay = random.randint(29, 60)
        
    actual_dt = planned_dt + timedelta(days=delay)
    planned_feats = random.randint(3, 16)
    delivered_feats = max(0, planned_feats - random.randint(0, min(3, planned_feats - 1)))
    planned_hrs = random.randint(50, 450)
    actual_hrs = max(10, int(planned_hrs * (1 + random.uniform(-0.15, 0.40))))
    
    if random.random() < 0.05:
        status = "Cancelled"
        actual_str = ""
        delivered_feats = 0
        delay = 0
    elif planned_dt > datetime(2026, 8, 1):
        status = random.choice(["Planning", "In Progress"])
        actual_str = ""
        delay = 0
    else:
        status = "Released" if delay < 14 else "Delayed"
        actual_str = actual_dt.strftime("%Y-%m-%d")
        
    releases.append({
        "release_id": rel_id,
        "planned_release_date": planned_dt.strftime("%Y-%m-%d"),
        "actual_release_date": actual_str,
        "planned_features": planned_feats,
        "delivered_features": delivered_feats,
        "planned_effort_hours": planned_hrs,
        "actual_effort_hours": actual_hrs,
        "delay_days": delay,
        "release_status": status
    })

# Generate Features (200 records)
features = []
for i in range(200):
    feat_id = f"FEAT-{i+1:04d}"
    p_idx = random.randint(0, len(FEATURE_NAME_PREFIXES) - 1)
    s_idx = random.randint(0, len(FEATURE_NAME_SUFFIXES) - 1)
    feat_name = f"{FEATURE_NAME_PREFIXES[p_idx]} {FEATURE_NAME_SUFFIXES[s_idx]}"
    
    assigned_rel = random.choice(releases)["release_id"] if random.random() < 0.85 else ""
    demand = random.randint(1, 100)
    b_val = random.randint(10, 100)
    urg = random.choices(["Critical", "High", "Medium", "Low"], weights=[0.15, 0.35, 0.35, 0.15])[0]
    strat = random.randint(10, 100)
    effort = random.randint(8, 200)
    
    features.append({
        "feature_id": feat_id,
        "feature_name": feat_name,
        "product": random.choice(PRODUCTS),
        "category": random.choice(CATEGORIES),
        "customer_demand": demand,
        "business_value": b_val,
        "urgency": urg,
        "strategic_alignment": strat,
        "estimated_effort_hours": effort,
        "release_id": assigned_rel,
        "status": random.choice(STATUSES_FEATURE)
    })

# Generate Tasks (3,000 records)
tasks = []
for i in range(3000):
    task_id = f"TASK-{i+1:05d}"
    feat = random.choice(features)
    action = random.choice(TASK_ACTIONS)
    task_name = f"{action} {feat['feature_name']}"
    proj_id = random.choice(PROJECT_IDS)
    rel_id = feat["release_id"] or random.choice(releases)["release_id"]
    
    start_dt = base_date + timedelta(days=random.randint(0, 900))
    est_effort = random.randint(4, 120)
    variance = random.uniform(-0.2, 0.6)
    act_effort = max(1, int(est_effort * (1 + variance)))
    
    planned_end = start_dt + timedelta(days=max(1, est_effort // 8))
    actual_end = planned_end + timedelta(days=random.randint(-3, 18)) if random.random() < 0.65 else None
    
    status = random.choices(
        ["Completed", "In Progress", "Not Started", "Blocked", "Cancelled"],
        weights=[0.45, 0.30, 0.15, 0.07, 0.03]
    )[0]
    
    priority = random.choices(["Critical", "High", "Medium", "Low"], weights=[0.15, 0.35, 0.35, 0.15])[0]
    dep = f"TASK-{random.randint(1, i):05d}" if i > 5 and random.random() < 0.25 else ""
    
    tasks.append({
        "task_id": task_id,
        "project_id": proj_id,
        "release_id": rel_id,
        "feature_id": feat["feature_id"],
        "task_name": task_name,
        "start_date": start_dt.strftime("%Y-%m-%d"),
        "planned_end_date": planned_end.strftime("%Y-%m-%d"),
        "actual_end_date": actual_end.strftime("%Y-%m-%d") if (actual_end and status == "Completed") else "",
        "estimated_effort_hours": est_effort,
        "actual_effort_hours": act_effort if status != "Not Started" else 0,
        "dependency": dep,
        "task_status": status,
        "priority": priority
    })

# Generate Feature Requests (10,000 records)
feature_requests = []
for i in range(10000):
    req_id = f"REQ-{i+1:06d}"
    feat = random.choice(features)
    cust_id = f"CUST-{random.randint(1, 800):04d}"
    req_dt = base_date + timedelta(days=random.randint(0, 950))
    votes = random.randint(1, 150)
    segment = random.choice(CUSTOMER_SEGMENTS)
    urg = random.choices(["Critical", "High", "Medium", "Low"], weights=[0.10, 0.30, 0.40, 0.20])[0]
    b_val = random.randint(1, 100)
    strat = random.randint(1, 100)
    est_eff = random.randint(8, 160)
    status = random.choices(["Open", "Accepted", "Under Review", "Deferred", "Rejected"], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
    
    feature_requests.append({
        "request_id": req_id,
        "feature_id": feat["feature_id"],
        "customer_id": cust_id,
        "request_date": req_dt.strftime("%Y-%m-%d"),
        "demand_votes": votes,
        "customer_segment": segment,
        "urgency": urg,
        "business_value": b_val,
        "strategic_alignment": strat,
        "estimated_effort_hours": est_eff,
        "status": status
    })

# Write the individual specification CSV files
def write_csv_file(path, data, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)

write_csv_file(os.path.join(OUTPUT_DIR, "releases.csv"), releases, [
    "release_id", "planned_release_date", "actual_release_date",
    "planned_features", "delivered_features", "planned_effort_hours",
    "actual_effort_hours", "delay_days", "release_status"
])

write_csv_file(os.path.join(OUTPUT_DIR, "features.csv"), features, [
    "feature_id", "feature_name", "product", "category",
    "customer_demand", "business_value", "urgency", "strategic_alignment",
    "estimated_effort_hours", "release_id", "status"
])

write_csv_file(os.path.join(OUTPUT_DIR, "tasks.csv"), tasks, [
    "task_id", "project_id", "release_id", "feature_id", "task_name",
    "start_date", "planned_end_date", "actual_end_date",
    "estimated_effort_hours", "actual_effort_hours", "dependency",
    "task_status", "priority"
])

write_csv_file(os.path.join(OUTPUT_DIR, "feature_requests.csv"), feature_requests, [
    "request_id", "feature_id", "customer_id", "request_date",
    "demand_votes", "customer_segment", "urgency", "business_value",
    "strategic_alignment", "estimated_effort_hours", "status"
])

# Write the Unified ProductPilot Dataset CSV for direct workspace upload & Excel inspection
# Schema matches SAMPLE_CSV_HEADERS:
# [feature_id, feature_name, customer_demand, business_value, urgency, strategic_alignment, dev_effort, task_id, project_id, task_status, planned_date, actual_date, release_id]

unified_rows = []
task_by_feature = {}
for t in tasks:
    fid = t["feature_id"]
    if fid not in task_by_feature:
        task_by_feature[fid] = []
    task_by_feature[fid].append(t)

for f in features:
    associated_tasks = task_by_feature.get(f["feature_id"], [])
    if not associated_tasks:
        associated_tasks = [{
            "task_id": f"TASK-{random.randint(1000, 9999)}",
            "project_id": random.choice(PROJECT_IDS),
            "task_status": "In Progress" if f["status"] == "In Development" else ("Completed" if f["status"] == "Released" else "Not Started"),
            "planned_end_date": "2025-12-15",
            "actual_end_date": ""
        }]
        
    for t in associated_tasks[:2]: # 1-2 tasks per feature
        urgency_num = 9 if f["urgency"] == "Critical" else (7 if f["urgency"] == "High" else (5 if f["urgency"] == "Medium" else 3))
        dev_effort_num = max(1, round(f["estimated_effort_hours"] / 16.0))
        bv_scaled = round(f["business_value"] / 10.0, 1)
        strat_scaled = max(1, round(f["strategic_alignment"] / 20.0))
        
        unified_rows.append({
            "feature_id": f["feature_id"],
            "feature_name": f["feature_name"],
            "customer_demand": f["customer_demand"],
            "business_value": bv_scaled,
            "urgency": urgency_num,
            "strategic_alignment": strat_scaled,
            "dev_effort": dev_effort_num,
            "task_id": t["task_id"],
            "project_id": t["project_id"],
            "task_status": t["task_status"],
            "planned_date": t["planned_end_date"],
            "actual_date": t.get("actual_end_date", ""),
            "release_id": f["release_id"] or t.get("release_id", "R-2025.4")
        })

unified_headers = [
    "feature_id", "feature_name", "customer_demand", "business_value",
    "urgency", "strategic_alignment", "dev_effort", "task_id",
    "project_id", "task_status", "planned_date", "actual_date", "release_id"
]

unified_csv_path = os.path.join(PROJECT_ROOT, "productpilot_dataset.csv")
write_csv_file(unified_csv_path, unified_rows, unified_headers)

print(f"Generated unified dataset at: {unified_csv_path} with {len(unified_rows)} rows.")
print(f"Generated 4 specification datasets in: {OUTPUT_DIR}")
