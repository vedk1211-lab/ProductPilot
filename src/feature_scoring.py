"""
ProductPilot - Feature Prioritization Scoring
==============================================
Calculates configurable priority scores (0-100) for product features.
Normalizes inputs and combines weighted factors.
"""

import pandas as pd
import numpy as np


DEFAULT_WEIGHTS = {
    "customer_demand": 0.30,
    "business_value": 0.25,
    "urgency": 0.20,
    "strategic_alignment": 0.15,
    "effort_efficiency": 0.10,
}


def validate_weights(weights):
    """Validate and normalize weights to sum to 1.0."""
    if not weights:
        return DEFAULT_WEIGHTS.copy()

    cleaned = {}
    for key in DEFAULT_WEIGHTS:
        val = weights.get(key, 0)
        if val < 0:
            val = 0
        cleaned[key] = val

    total = sum(cleaned.values())
    if total == 0:
        return DEFAULT_WEIGHTS.copy()

    return {k: v / total for k, v in cleaned.items()}


def normalize_column(series, min_val=None, max_val=None):
    """Min-max normalize a pandas Series to [0, 100]."""
    s = pd.to_numeric(series, errors="coerce").fillna(0)
    if min_val is None:
        min_val = s.min()
    if max_val is None:
        max_val = s.max()
    if max_val == min_val:
        return pd.Series(50.0, index=s.index)
    return ((s - min_val) / (max_val - min_val) * 100).clip(0, 100)


def compute_effort_efficiency(business_value, effort):
    """
    Compute effort efficiency: higher value for lower effort = better score.
    Returns a 0-100 normalized score.
    """
    bv = pd.to_numeric(business_value, errors="coerce").fillna(50)
    eff = pd.to_numeric(effort, errors="coerce").fillna(0)
    # Avoid division by zero: add 1 to effort
    raw = bv / (eff + 1)
    # Normalize to 0-100
    min_r, max_r = raw.min(), raw.max()
    if max_r == min_r:
        return pd.Series(50.0, index=bv.index)
    return ((raw - min_r) / (max_r - min_r) * 100).clip(0, 100)


def compute_priority_scores(features_df, weights=None):
    """
    Compute priority scores for each feature.

    Parameters
    ----------
    features_df : pd.DataFrame
        Must have columns: customer_demand, business_value, urgency_score,
        strategic_alignment, estimated_effort_hours
    weights : dict, optional
        Weights for each scoring factor. Normalized to sum to 1.0.

    Returns
    -------
    pd.DataFrame
        Input df augmented with score columns and priority category.
    """
    w = validate_weights(weights)
    df = features_df.copy()

    # Normalize each factor to 0-100
    df["demand_score"] = normalize_column(df["customer_demand"])
    df["bv_score"] = normalize_column(df["business_value"])
    df["urgency_norm"] = normalize_column(df.get("urgency_score", pd.Series(50, index=df.index)))
    df["alignment_score"] = normalize_column(df["strategic_alignment"])
    df["efficiency_score"] = compute_effort_efficiency(
        df["business_value"], df["estimated_effort_hours"]
    )

    # Weighted sum
    df["priority_score"] = (
        df["demand_score"] * w["customer_demand"]
        + df["bv_score"] * w["business_value"]
        + df["urgency_norm"] * w["urgency"]
        + df["alignment_score"] * w["strategic_alignment"]
        + df["efficiency_score"] * w["effort_efficiency"]
    ).round(2)

    # Priority categories
    df["priority_category"] = pd.cut(
        df["priority_score"],
        bins=[0, 25, 50, 75, 100],
        labels=["Low", "Medium", "High", "Critical"],
        include_lowest=True
    )

    # Recommended action
    df["recommended_action"] = df["priority_category"].map({
        "Critical": "Prioritize for next sprint — high demand & business value",
        "High": "Schedule for upcoming release — strong business case",
        "Medium": "Evaluate further — needs stakeholder input",
        "Low": "Defer or deprioritize — consider for future roadmap",
    })

    # Rank
    df["rank"] = df["priority_score"].rank(ascending=False, method="min").astype(int)

    return df.sort_values("priority_score", ascending=False)


def get_feature_explanation(row, weights=None):
    """Generate a human-readable explanation of a feature's priority score."""
    w = validate_weights(weights)
    lines = [
        f"**{row.get('feature_name', 'Feature')}** — Priority Score: **{row.get('priority_score', 'N/A')}** / 100",
        f"Category: **{row.get('priority_category', 'N/A')}** | Rank: #{row.get('rank', 'N/A')}",
        "",
        "**Score Breakdown:**",
        f"  • Customer Demand:     {row.get('demand_score', 0):.1f}/100 × {w['customer_demand']:.0%} = {row.get('demand_score', 0) * w['customer_demand']:.1f}",
        f"  • Business Value:      {row.get('bv_score', 0):.1f}/100 × {w['business_value']:.0%} = {row.get('bv_score', 0) * w['business_value']:.1f}",
        f"  • Urgency:             {row.get('urgency_norm', 0):.1f}/100 × {w['urgency']:.0%} = {row.get('urgency_norm', 0) * w['urgency']:.1f}",
        f"  • Strategic Alignment: {row.get('alignment_score', 0):.1f}/100 × {w['strategic_alignment']:.0%} = {row.get('alignment_score', 0) * w['strategic_alignment']:.1f}",
        f"  • Effort Efficiency:   {row.get('efficiency_score', 0):.1f}/100 × {w['effort_efficiency']:.0%} = {row.get('efficiency_score', 0) * w['effort_efficiency']:.1f}",
        "",
        f"**Recommended Action:** {row.get('recommended_action', 'N/A')}",
        "",
        "*Note: These scores are recommendations derived from the configured weights and "
        "normalized input data. They should inform, not replace, product management judgment.*"
    ]
    return "\n".join(lines)
