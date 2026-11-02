"""
ProductPilot - Custom Data Processor
=====================================
Processes user-supplied data (CSV, Excel, or interactive input) and converts
it into standardized DataFrames ready for all ProductPilot analytical features:
- Feature Prioritization (WSJF & weighted scoring)
- Project Delivery Risk (task risk, release risk, overdue analysis)
- Bloom Filter Duplicate Screening (feature & request ID indexing)
- DGIM Sliding Window Streaming (event stream generation)
- Management Recommendations & Executive KPIs
"""

import os
import io
import re
import datetime
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, List

# Column Aliases for intelligent auto-detection
COLUMN_ALIASES: Dict[str, List[str]] = {
    "feature_name": [
        "feature_name", "feature", "name", "title", "summary",
        "feature_title", "feat_name", "item_name", "featurename"
    ],
    "feature_id": [
        "feature_id", "id", "feat_id", "key", "issue_key",
        "featureid", "feature_key", "code"
    ],
    "customer_demand": [
        "customer_demand", "demand", "votes", "requests", "request_count",
        "user_demand", "customer_votes", "score_demand", "popularity", "customerdemand"
    ],
    "business_value": [
        "business_value", "value", "bv", "roi", "business_impact",
        "impact", "biz_value", "businessvalue", "business_score"
    ],
    "urgency": [
        "urgency", "time_criticality", "urgency_level", "priority",
        "criticality", "urg", "time_urgency"
    ],
    "strategic_alignment": [
        "strategic_alignment", "alignment", "strategy", "strategic_value",
        "strategic_score", "strategic", "strategicalignment"
    ],
    "estimated_effort_hours": [
        "estimated_effort_hours", "dev_effort", "effort", "effort_hours",
        "hours", "story_points", "estimate", "size", "deveffort", "dev_hours"
    ],
    "product": [
        "product", "product_name", "app", "application", "module",
        "system", "product_line", "productname"
    ],
    "category": [
        "category", "type", "feature_type", "tag", "component", "domain"
    ],
    "status": [
        "status", "feature_status", "stage", "state", "phase"
    ],
    "task_id": [
        "task_id", "task", "tid", "subtask_id", "action_id", "taskid"
    ],
    "task_name": [
        "task_name", "task_title", "task_description", "description",
        "activity", "taskname"
    ],
    "project_id": [
        "project_id", "project", "proj_id", "team", "projectid", "proj"
    ],
    "task_status": [
        "task_status", "task_state", "workflow_status", "status_task", "taskstatus"
    ],
    "planned_end_date": [
        "planned_end_date", "planned_date", "due_date", "target_date",
        "deadline", "planneddate", "end_date", "target_completion"
    ],
    "actual_end_date": [
        "actual_end_date", "actual_date", "completed_date", "finish_date",
        "actualdate", "completion_date"
    ],
    "overdue_days": [
        "overdue_days", "overdue", "delay_days", "days_overdue", "overduedays"
    ],
    "dependency": [
        "dependency", "depends_on", "blocked_by", "prerequisite", "depends"
    ],
    "priority": [
        "priority", "task_priority", "severity", "taskpriority"
    ],
    "release_id": [
        "release_id", "release", "version", "target_release", "rel_id",
        "sprint", "milestone", "releaseid"
    ],
    "request_id": [
        "request_id", "request", "req_id", "ticket_id", "feedback_id", "requestid"
    ],
}


def normalize_col_name(col: str) -> str:
    """Normalize a column name string for matching."""
    return re.sub(r"[^a-z0-9]", "", str(col).lower().strip())


def detect_column_mapping(df_columns: List[str]) -> Dict[str, str]:
    """
    Detect semantic column mapping automatically from DataFrame column names.
    Returns: {canonical_field: actual_column_name}
    """
    mapping: Dict[str, str] = {}
    normalized_cols = {normalize_col_name(c): c for c in df_columns}

    for canonical, aliases in COLUMN_ALIASES.items():
        matched_col = None
        for alias in aliases:
            norm_alias = normalize_col_name(alias)
            if norm_alias in normalized_cols:
                matched_col = normalized_cols[norm_alias]
                break
        if matched_col:
            mapping[canonical] = matched_col

    return mapping


def parse_urgency_to_numeric(val: Any) -> float:
    """Convert urgency strings or numbers to a standard 0-10 score."""
    if pd.isna(val) or val is None or str(val).strip() == "":
        return 5.0
    val_str = str(val).strip().lower()
    if val_str in ("critical", "urgent", "p0", "blocker"):
        return 9.0
    elif val_str in ("high", "p1", "major"):
        return 7.0
    elif val_str in ("medium", "p2", "normal", "moderate"):
        return 5.0
    elif val_str in ("low", "p3", "minor", "trivial"):
        return 2.0
    try:
        num = float(val)
        return float(np.clip(num, 0, 10))
    except (ValueError, TypeError):
        return 5.0


def parse_urgency_to_label(numeric_urgency: float) -> str:
    """Convert numeric urgency to standard label."""
    if numeric_urgency >= 8.0:
        return "Critical"
    elif numeric_urgency >= 6.0:
        return "High"
    elif numeric_urgency >= 3.5:
        return "Medium"
    else:
        return "Low"


def process_user_dataframe(
    df: pd.DataFrame,
    custom_mapping: Optional[Dict[str, str]] = None,
    dataset_name: str = "Custom Dataset"
) -> Dict[str, Any]:
    """
    Transform any user tabular data into the four standard DataFrames:
    - features: features_df
    - tasks: tasks_df
    - releases: releases_df
    - requests: requests_df
    """
    if df.empty:
        raise ValueError("Uploaded dataset is empty.")

    # 1. Column mapping
    detected = detect_column_mapping(df.columns.tolist())
    if custom_mapping:
        for k, v in custom_mapping.items():
            if v and v in df.columns:
                detected[k] = v

    # Helper getter
    def get_val(row: pd.Series, canonical: str, default: Any = None) -> Any:
        col = detected.get(canonical)
        if col and col in row and pd.notna(row[col]):
            return row[col]
        return default

    today = datetime.date.today()

    # -------------------------------------------------------------
    # 2. Extract / Build Features DataFrame
    # -------------------------------------------------------------
    features_records = []
    has_feature_info = any(k in detected for k in [
        "feature_name", "feature_id", "customer_demand", "business_value"
    ])

    # If rows have distinct feature identifiers or names, group or extract them
    feat_col = detected.get("feature_id") or detected.get("feature_name")

    if feat_col:
        grouped_features = df.groupby(feat_col, sort=False)
    else:
        grouped_features = [(f"FEAT-{i+1:04d}", group) for i, (_, group) in enumerate(df.iterrows())]

    feat_counter = 1
    for f_key, group in grouped_features:
        first_row = group.iloc[0] if isinstance(group, pd.DataFrame) else group

        f_id = str(get_val(first_row, "feature_id", f"FEAT-{feat_counter:04d}")).strip()
        f_name = str(get_val(first_row, "feature_name", f_key if f_key else f"Feature {feat_counter}")).strip()

        # Demand
        raw_demand = get_val(first_row, "customer_demand", None)
        if raw_demand is None:
            # Maybe aggregated count of requests in this group
            demand_val = len(group) if isinstance(group, pd.DataFrame) else 25
        else:
            try:
                demand_val = float(raw_demand)
            except (ValueError, TypeError):
                demand_val = 25.0

        # Business Value (scale to 1-10 or 0-100)
        raw_bv = get_val(first_row, "business_value", 6.0)
        try:
            bv_val = float(raw_bv)
            if bv_val > 10.0:
                # User used 0-100 scale, normalize to 1-10
                bv_val = round(bv_val / 10.0, 1)
        except (ValueError, TypeError):
            bv_val = 6.0

        # Urgency
        raw_urg = get_val(first_row, "urgency", "Medium")
        urg_score = parse_urgency_to_numeric(raw_urg)
        urg_label = parse_urgency_to_label(urg_score)

        # Strategic Alignment
        raw_strat = get_val(first_row, "strategic_alignment", 5.0)
        try:
            strat_val = float(raw_strat)
            if strat_val > 10.0:
                strat_val = round(strat_val / 10.0, 1)
        except (ValueError, TypeError):
            strat_val = 5.0

        # Dev Effort Hours
        raw_effort = get_val(first_row, "estimated_effort_hours", 40.0)
        try:
            effort_val = float(raw_effort)
            if effort_val < 1.0:
                effort_val = 8.0
        except (ValueError, TypeError):
            effort_val = 40.0

        # Product / Category / Status / Release
        prod_val = str(get_val(first_row, "product", "Custom Product")).strip()
        cat_val = str(get_val(first_row, "category", "Core Functionality")).strip()
        stat_val = str(get_val(first_row, "status", "Proposed")).strip()
        rel_val = str(get_val(first_row, "release_id", "REL-001")).strip()

        features_records.append({
            "feature_id": f_id,
            "feature_name": f_name,
            "product": prod_val if prod_val else "Custom Product",
            "category": cat_val if cat_val else "Core Functionality",
            "status": stat_val if stat_val else "Proposed",
            "customer_demand": int(max(1, round(demand_val))),
            "business_value": round(bv_val, 1),
            "urgency": urg_label,
            "urgency_score": round(urg_score, 1),
            "strategic_alignment": round(strat_val, 1),
            "estimated_effort_hours": round(effort_val, 1),
            "release_id": rel_val if rel_val else "REL-001",
        })
        feat_counter += 1

    features_df = pd.DataFrame(features_records)

    # -------------------------------------------------------------
    # 3. Extract / Build Tasks DataFrame
    # -------------------------------------------------------------
    tasks_records = []
    has_task_col = detected.get("task_id") is not None or detected.get("task_status") is not None

    if has_task_col:
        # Group or iterate df rows
        for idx, row in df.iterrows():
            t_id = str(get_val(row, "task_id", f"TASK-{idx+1:05d}")).strip()
            f_id = str(get_val(row, "feature_id", features_df.iloc[min(idx, len(features_df)-1)]["feature_id"])).strip()
            f_name = str(get_val(row, "feature_name", features_df.iloc[min(idx, len(features_df)-1)]["feature_name"])).strip()
            t_name = str(get_val(row, "task_name", f"Implement {f_name}")).strip()
            p_id = str(get_val(row, "project_id", "PROJ-Core")).strip()
            t_status = str(get_val(row, "task_status", "In Progress")).strip()
            if t_status.lower() in ("done", "closed", "finish", "complete"):
                t_status = "Completed"
            elif t_status.lower() in ("block", "blocked", "waiting"):
                t_status = "Blocked"
            elif t_status.lower() in ("progress", "wip", "active"):
                t_status = "In Progress"
            elif t_status.lower() in ("todo", "open", "new", "backlog"):
                t_status = "Not Started"

            # Dates
            p_date_raw = get_val(row, "planned_end_date", None)
            a_date_raw = get_val(row, "actual_end_date", None)

            p_date_str = str(p_date_raw)[:10] if pd.notna(p_date_raw) else (today - datetime.timedelta(days=10)).isoformat()
            a_date_str = str(a_date_raw)[:10] if pd.notna(a_date_raw) else None

            # Overdue calculation
            raw_overdue = get_val(row, "overdue_days", None)
            if raw_overdue is not None and pd.notna(raw_overdue):
                try:
                    overdue_days = max(0, int(float(raw_overdue)))
                except (ValueError, TypeError):
                    overdue_days = 0
            else:
                overdue_days = 0
                if p_date_str and t_status != "Completed":
                    try:
                        p_dt = datetime.datetime.strptime(p_date_str[:10], "%Y-%m-%d").date()
                        delta = (today - p_dt).days
                        if delta > 0:
                            overdue_days = delta
                    except Exception:
                        pass

            # Effort & Dependency & Priority
            raw_effort = get_val(row, "estimated_effort_hours", 20.0)
            try:
                est_effort = max(1.0, float(raw_effort))
            except (ValueError, TypeError):
                est_effort = 20.0

            dep_val = get_val(row, "dependency", None)
            dep_str = str(dep_val).strip() if pd.notna(dep_val) and str(dep_val).strip() not in ("None", "", "nan") else None

            prio_val = str(get_val(row, "priority", "Medium")).strip()
            rel_id = str(get_val(row, "release_id", "REL-001")).strip()

            tasks_records.append({
                "task_id": t_id,
                "feature_id": f_id,
                "task_name": t_name,
                "project_id": p_id if p_id else "PROJ-Core",
                "task_status": t_status if t_status else "In Progress",
                "planned_end_date": p_date_str,
                "actual_end_date": a_date_str,
                "overdue_days": overdue_days,
                "estimated_effort_hours": est_effort,
                "actual_effort_hours": est_effort * (1.2 if overdue_days > 0 else 0.9),
                "effort_ratio": round(1.2 if overdue_days > 0 else 0.9, 2),
                "dependency": dep_str,
                "priority": prio_val if prio_val else "Medium",
                "release_id": rel_id if rel_id else "REL-001",
            })
    else:
        # Auto-generate realistic engineering tasks corresponding to the features
        task_id_counter = 1
        for _, feat in features_df.iterrows():
            f_id = feat["feature_id"]
            f_name = feat["feature_name"]
            rel_id = feat["release_id"]
            total_effort = feat["estimated_effort_hours"]

            # Subtask 1: Backend / Implementation
            t1_status = "Completed" if feat["status"] == "Completed" else "In Progress"
            t1_overdue = 12 if feat["urgency"] == "Critical" else 0
            p1_date = (today - datetime.timedelta(days=t1_overdue + 5)).isoformat()
            tasks_records.append({
                "task_id": f"TASK-{task_id_counter:05d}",
                "feature_id": f_id,
                "task_name": f"Core Engineering: {f_name}",
                "project_id": "PROJ-Platform",
                "task_status": t1_status,
                "planned_end_date": p1_date,
                "actual_end_date": (today - datetime.timedelta(days=2)).isoformat() if t1_status == "Completed" else None,
                "overdue_days": t1_overdue,
                "estimated_effort_hours": round(total_effort * 0.6, 1),
                "actual_effort_hours": round(total_effort * 0.7, 1),
                "effort_ratio": 1.15 if t1_overdue > 0 else 0.95,
                "dependency": None,
                "priority": feat["urgency"],
                "release_id": rel_id,
            })
            task_id_counter += 1

            # Subtask 2: QA / Testing
            t2_status = "Blocked" if feat["urgency"] == "Critical" and t1_overdue > 0 else ("Completed" if feat["status"] == "Completed" else "Not Started")
            tasks_records.append({
                "task_id": f"TASK-{task_id_counter:05d}",
                "feature_id": f_id,
                "task_name": f"Integration & Testing: {f_name}",
                "project_id": "PROJ-QA",
                "task_status": t2_status,
                "planned_end_date": (today + datetime.timedelta(days=14)).isoformat(),
                "actual_end_date": None,
                "overdue_days": 0,
                "estimated_effort_hours": round(total_effort * 0.4, 1),
                "actual_effort_hours": 0.0,
                "effort_ratio": 1.0,
                "dependency": f"TASK-{task_id_counter-1:05d}",
                "priority": feat["urgency"],
                "release_id": rel_id,
            })
            task_id_counter += 1

    tasks_df = pd.DataFrame(tasks_records)

    # -------------------------------------------------------------
    # 4. Extract / Build Releases DataFrame
    # -------------------------------------------------------------
    releases_records = []
    unique_rels = tasks_df["release_id"].dropna().unique().tolist()
    if not unique_rels:
        unique_rels = ["REL-001"]

    for rel_id in unique_rels:
        rel_tasks = tasks_df[tasks_df["release_id"] == rel_id]
        total_t = len(rel_tasks)
        comp_t = len(rel_tasks[rel_tasks["task_status"] == "Completed"])
        over_t = len(rel_tasks[rel_tasks["overdue_days"] > 0])
        deliv_rate = round((comp_t / total_t * 100), 1) if total_t > 0 else 0.0

        if deliv_rate >= 80.0 and over_t == 0:
            rel_status = "Released"
            delay_days = 0
        elif over_t > 0:
            rel_status = "Delayed"
            delay_days = int(rel_tasks["overdue_days"].max())
        else:
            rel_status = "On Track"
            delay_days = 0

        releases_records.append({
            "release_id": rel_id,
            "release_name": f"Release {rel_id}",
            "release_status": rel_status,
            "planned_date": (today + datetime.timedelta(days=30)).isoformat(),
            "target_date": (today + datetime.timedelta(days=30)).isoformat(),
            "actual_date": today.isoformat() if rel_status == "Released" else None,
            "total_tasks": total_t,
            "completed_tasks": comp_t,
            "overdue_tasks": over_t,
            "feature_delivery_rate": deliv_rate,
            "delay_days": delay_days,
        })
    releases_df = pd.DataFrame(releases_records)

    # -------------------------------------------------------------
    # 5. Extract / Build Requests DataFrame (for Bloom Filter & Trends)
    # -------------------------------------------------------------
    requests_records = []
    has_req_col = detected.get("request_id") is not None
    if has_req_col and "request_id" in df.columns:
        for idx, row in df.iterrows():
            r_id = str(row[detected["request_id"]]).strip()
            f_id = str(get_val(row, "feature_id", features_df.iloc[0]["feature_id"])).strip()
            requests_records.append({
                "request_id": r_id,
                "feature_id": f_id,
                "request_date": str(get_val(row, "planned_end_date", today.isoformat()))[:10],
                "customer_segment": "Enterprise",
                "urgency": "Medium"
            })
    else:
        # Generate representative requests based on customer_demand
        req_counter = 1
        for _, feat in features_df.iterrows():
            f_id = feat["feature_id"]
            num_reqs = min(20, max(2, int(feat["customer_demand"] // 5)))
            for j in range(num_reqs):
                day_offset = (req_counter * 3) % 90
                req_date = (today - datetime.timedelta(days=day_offset)).isoformat()
                requests_records.append({
                    "request_id": f"REQ-{feat['feature_id']}-{j+1:03d}",
                    "feature_id": f_id,
                    "request_date": req_date,
                    "customer_segment": "Enterprise" if j % 2 == 0 else "SMB",
                    "urgency": feat["urgency"]
                })
                req_counter += 1

    requests_df = pd.DataFrame(requests_records)

    # Return structured package
    return {
        "features": features_df,
        "tasks": tasks_df,
        "releases": releases_df,
        "requests": requests_df,
        "name": dataset_name,
        "mapping": detected,
        "record_counts": {
            "features": len(features_df),
            "tasks": len(tasks_df),
            "releases": len(releases_df),
            "requests": len(requests_df),
        }
    }


def process_excel_file(file_obj_or_path: Any, filename: str = "dataset.xlsx") -> Dict[str, Any]:
    """
    Process an uploaded Excel file (.xlsx or .xls), supporting multi-sheet workbooks.
    """
    excel_file = pd.ExcelFile(file_obj_or_path)
    sheet_names = [s.strip().lower() for s in excel_file.sheet_names]

    # Check for dedicated sheets
    has_features = any("feat" in s for s in sheet_names)
    has_tasks = any("task" in s for s in sheet_names)

    if has_features and has_tasks:
        feat_sheet = next(s for s in excel_file.sheet_names if "feat" in s.lower())
        task_sheet = next(s for s in excel_file.sheet_names if "task" in s.lower())
        f_df = pd.read_excel(excel_file, sheet_name=feat_sheet)
        t_df = pd.read_excel(excel_file, sheet_name=task_sheet)

        # Merge or combine into unified frame
        # If there's a join key like feature_id
        if "feature_id" in f_df.columns and "feature_id" in t_df.columns:
            merged = pd.merge(t_df, f_df, on="feature_id", how="left", suffixes=("_task", ""))
            return process_user_dataframe(merged, dataset_name=filename)
        else:
            # Concat columns or process features directly
            return process_user_dataframe(f_df, dataset_name=filename)

    # Check for 'Unified_Dataset' sheet or take the first substantive sheet
    substantive_sheet = excel_file.sheet_names[0]
    for s in excel_file.sheet_names:
        if s.lower() in ("unified_dataset", "data", "features", "dataset"):
            substantive_sheet = s
            break
        elif s.lower() == "overview" and len(excel_file.sheet_names) > 1:
            continue
        substantive_sheet = s

    df = pd.read_excel(excel_file, sheet_name=substantive_sheet)
    return process_user_dataframe(df, dataset_name=filename)


def get_sample_custom_dataset() -> Dict[str, Any]:
    """
    Return a curated, rich sample custom dataset that users can load with 1-click.
    """
    sample_data = {
        "feature_id": [
            "CUSTOM-001", "CUSTOM-002", "CUSTOM-003", "CUSTOM-004", "CUSTOM-005",
            "CUSTOM-006", "CUSTOM-007", "CUSTOM-008", "CUSTOM-009", "CUSTOM-010"
        ],
        "feature_name": [
            "AI-Powered Smart Search", "One-Click Stripe Billing", "Role-Based Access Control (RBAC)",
            "Automated PDF Invoicing", "Real-time Slack Webhooks", "Mobile Responsive Redesign",
            "Multi-Tenant Database Sync", "Audit Log Export to CSV", "SSO via Okta & Google",
            "Performance Optimization & Caching"
        ],
        "product": [
            "Customer Portal", "Billing Suite", "Security Core",
            "Billing Suite", "Integrations Hub", "Mobile App",
            "Security Core", "Compliance Suite", "Security Core",
            "Core Engine"
        ],
        "customer_demand": [95, 88, 76, 62, 54, 70, 48, 35, 82, 90],
        "business_value": [9.5, 9.0, 8.0, 6.5, 5.0, 7.5, 8.5, 4.0, 8.8, 9.2],
        "urgency": [
            "Critical", "High", "High", "Medium", "Low",
            "Medium", "High", "Low", "Critical", "High"
        ],
        "strategic_alignment": [9.0, 8.5, 8.0, 6.0, 5.5, 7.0, 9.0, 5.0, 8.5, 9.5],
        "estimated_effort_hours": [60, 40, 50, 30, 20, 45, 80, 15, 35, 55],
        "task_id": [
            "TSK-101", "TSK-102", "TSK-103", "TSK-104", "TSK-105",
            "TSK-106", "TSK-107", "TSK-108", "TSK-109", "TSK-110"
        ],
        "project_id": [
            "PROJ-Search", "PROJ-Fintech", "PROJ-Sec", "PROJ-Fintech", "PROJ-Integ",
            "PROJ-UX", "PROJ-Cloud", "PROJ-Sec", "PROJ-Sec", "PROJ-Perf"
        ],
        "task_status": [
            "In Progress", "In Progress", "Blocked", "Completed", "Not Started",
            "In Progress", "Blocked", "Completed", "Not Started", "In Progress"
        ],
        "planned_date": [
            "2026-10-15", "2026-10-20", "2026-10-01", "2026-09-30", "2026-11-15",
            "2026-10-28", "2026-09-20", "2026-09-15", "2026-11-01", "2026-10-22"
        ],
        "release_id": [
            "REL-v2.1", "REL-v2.1", "REL-v2.1", "REL-v2.0", "REL-v2.2",
            "REL-v2.1", "REL-v2.0", "REL-v2.0", "REL-v2.2", "REL-v2.1"
        ]
    }
    df = pd.DataFrame(sample_data)
    return process_user_dataframe(df, dataset_name="Curated SaaS Sample Dataset")


def generate_csv_template() -> str:
    """Generate sample CSV template content."""
    df = pd.DataFrame({
        "feature_name": ["User Authentication", "Export to Excel", "Dark Mode UI"],
        "customer_demand": [85, 60, 45],
        "business_value": [9.0, 7.5, 5.0],
        "urgency": ["Critical", "High", "Low"],
        "strategic_alignment": [9.0, 7.0, 6.0],
        "dev_effort": [40, 20, 15],
        "product": ["Core Web App", "Analytics Suite", "Core Web App"],
        "task_name": ["OAuth2 Integration", "Excel Writer API", "Tailwind Dark Theme"],
        "task_status": ["In Progress", "Completed", "Not Started"],
        "planned_date": ["2026-11-01", "2026-10-10", "2026-11-20"],
        "release_id": ["REL-1.0", "REL-1.0", "REL-1.1"],
    })
    return df.to_csv(index=False)
