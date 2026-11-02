"""
ProductPilot - Project Delivery Risk Scoring
=============================================
Calculates transparent risk scores for project tasks based on
overdue days, effort ratios, status, dependencies, and deadlines.
"""

import pandas as pd
import numpy as np


def compute_risk_scores(tasks_df, releases_df=None):
    """
    Compute risk scores for each task.

    Risk factors:
    - Overdue days (0-40 points)
    - Effort overrun ratio (0-25 points)
    - Status penalty (0-15 points)
    - Dependency risk (0-10 points)
    - Priority weight (0-10 points)

    Returns tasks_df augmented with risk_score, risk_category, and recommendation.
    """
    df = tasks_df.copy()

    # --- Overdue score (max 40 points) ---
    overdue = pd.to_numeric(df.get("overdue_days", 0), errors="coerce").fillna(0).clip(lower=0)
    df["overdue_risk"] = (overdue / overdue.max() * 40).clip(0, 40) if overdue.max() > 0 else 0

    # --- Effort overrun (max 25 points) ---
    effort_ratio = pd.to_numeric(df.get("effort_ratio", 1.0), errors="coerce").fillna(1.0)
    # Ratio > 1 means overrun
    overrun = (effort_ratio - 1.0).clip(lower=0)
    max_overrun = overrun.max()
    df["effort_risk"] = (overrun / max_overrun * 25).clip(0, 25) if max_overrun > 0 else 0

    # --- Status penalty (max 15 points) ---
    status_map = {
        "Blocked": 15,
        "Not Started": 8,
        "In Progress": 3,
        "Completed": 0,
        "Cancelled": 0,
    }
    df["status_risk"] = df["task_status"].map(status_map).fillna(5)

    # --- Dependency risk (max 10 points) ---
    has_dep = df["dependency"].notna() & (df["dependency"].astype(str).str.strip() != "")
    df["dependency_risk"] = 0.0
    if has_dep.any():
        # Check if dependency is overdue or blocked
        dep_status = {}
        for _, row in df.iterrows():
            dep_status[row["task_id"]] = row["task_status"]

        def dep_risk(row):
            if not has_dep[row.name]:
                return 0
            dep_id = str(row["dependency"]).strip()
            dep_st = dep_status.get(dep_id, "")
            if dep_st == "Blocked":
                return 10
            elif dep_st in ("Not Started", "In Progress"):
                if row["task_status"] in ("Not Started", "In Progress", "Blocked"):
                    return 6
            return 2

        df["dependency_risk"] = df.apply(dep_risk, axis=1)

    # --- Priority weight (max 10 points) ---
    priority_map = {"Critical": 10, "High": 7, "Medium": 4, "Low": 1}
    df["priority_risk"] = df["priority"].map(priority_map).fillna(4)

    # --- Total risk score ---
    df["risk_score"] = (
        df["overdue_risk"]
        + df["effort_risk"]
        + df["status_risk"]
        + df["dependency_risk"]
        + df["priority_risk"]
    ).round(1)

    # Normalize to 0-100
    max_score = df["risk_score"].max()
    if max_score > 0:
        df["risk_score"] = (df["risk_score"] / max_score * 100).round(1)

    # Risk categories
    df["risk_category"] = pd.cut(
        df["risk_score"],
        bins=[-1, 33, 66, 100],
        labels=["Low", "Medium", "High"]
    )

    # Recommendations
    def recommend(row):
        recs = []
        if row.get("overdue_risk", 0) > 20:
            recs.append("Task is significantly overdue — escalate immediately")
        if row.get("effort_risk", 0) > 15:
            recs.append("Effort overrun detected — review remaining scope")
        if row.get("status_risk", 0) >= 15:
            recs.append("Task is blocked — resolve blockers urgently")
        if row.get("dependency_risk", 0) >= 8:
            recs.append("Dependent task is blocked/delayed — review dependency chain")
        if row.get("priority_risk", 0) >= 8:
            recs.append("Critical priority task at risk — consider reallocation")
        if not recs:
            recs.append("On track — continue monitoring")
        return "; ".join(recs)

    df["recommendation"] = df.apply(recommend, axis=1)

    return df.sort_values("risk_score", ascending=False)


def compute_release_risk(releases_df, tasks_df):
    """Compute risk summary per release."""
    if tasks_df.empty or releases_df.empty:
        return releases_df

    rel_df = releases_df.copy()
    task_risk = tasks_df.copy()

    # Per-release task risk summary
    risk_agg = (
        task_risk.groupby("release_id")
        .agg(
            total_tasks=("task_id", "count"),
            high_risk_tasks=("risk_category", lambda x: (x == "High").sum()),
            avg_risk=("risk_score", "mean"),
            max_risk=("risk_score", "max"),
            overdue_count=("overdue_days", lambda x: (x > 0).sum()),
            blocked_count=("task_status", lambda x: (x == "Blocked").sum()),
        )
        .reset_index()
    )

    rel_df = rel_df.merge(risk_agg, on="release_id", how="left", suffixes=("", "_task"))
    rel_df["high_risk_tasks"] = rel_df["high_risk_tasks"].fillna(0).astype(int)
    rel_df["avg_risk"] = rel_df["avg_risk"].fillna(0).round(1)
    rel_df["overdue_count"] = rel_df["overdue_count"].fillna(0).astype(int)

    # Release risk category
    rel_df["release_risk"] = "Low"
    rel_df.loc[rel_df["avg_risk"] > 33, "release_risk"] = "Medium"
    rel_df.loc[rel_df["avg_risk"] > 60, "release_risk"] = "High"
    rel_df.loc[rel_df["high_risk_tasks"] > 3, "release_risk"] = "High"

    return rel_df


def generate_recommendations(tasks_df, releases_df):
    """Generate management-level recommendations from risk data."""
    recs = []

    if tasks_df.empty:
        return recs

    # Overdue tasks
    overdue = tasks_df[tasks_df.get("overdue_days", pd.Series(dtype=float)) > 0]
    if len(overdue) > 0:
        recs.append({
            "type": "Overdue Tasks",
            "severity": "High" if len(overdue) > 50 else "Medium",
            "count": len(overdue),
            "message": f"{len(overdue)} tasks are past their planned completion date. "
                       f"Average overdue: {overdue['overdue_days'].mean():.0f} days.",
            "action": "Review overdue tasks, identify blockers, and reassign or rescope."
        })

    # Blocked tasks
    blocked = tasks_df[tasks_df["task_status"] == "Blocked"]
    if len(blocked) > 0:
        recs.append({
            "type": "Blocked Tasks",
            "severity": "High" if len(blocked) > 20 else "Medium",
            "count": len(blocked),
            "message": f"{len(blocked)} tasks are currently blocked.",
            "action": "Investigate root causes of blocks. Prioritize unblocking critical-path items."
        })

    # High risk tasks
    if "risk_category" in tasks_df.columns:
        high_risk = tasks_df[tasks_df["risk_category"] == "High"]
        if len(high_risk) > 0:
            recs.append({
                "type": "High-Risk Tasks",
                "severity": "High",
                "count": len(high_risk),
                "message": f"{len(high_risk)} tasks are classified as high risk based on "
                           f"overdue status, effort overruns, and dependencies.",
                "action": "Escalate high-risk tasks to project leads. Consider scope reduction."
            })

    # Effort overruns
    if "effort_ratio" in tasks_df.columns:
        overrun = tasks_df[tasks_df["effort_ratio"] > 1.3]
        if len(overrun) > 0:
            recs.append({
                "type": "Effort Overruns",
                "severity": "Medium",
                "count": len(overrun),
                "message": f"{len(overrun)} tasks have actual effort exceeding estimates by >30%.",
                "action": "Review estimation practices. Update remaining task estimates."
            })

    # Release risks
    if releases_df is not None and not releases_df.empty and "release_risk" in releases_df.columns:
        high_risk_releases = releases_df[releases_df["release_risk"] == "High"]
        if len(high_risk_releases) > 0:
            recs.append({
                "type": "At-Risk Releases",
                "severity": "High",
                "count": len(high_risk_releases),
                "message": f"{len(high_risk_releases)} releases are at high risk of delay.",
                "action": "Reassess release scope. Move non-critical features to next release."
            })

    return recs
