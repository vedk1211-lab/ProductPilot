# Data Dictionary — ProductPilot

> All data is **synthetic**, generated using `src/data_generator.py` with a fixed random seed (42) for reproducibility.

---

## Dataset Overview

| Dataset | File | Records | Description |
|---------|------|---------|-------------|
| Feature Requests | `data/raw/feature_requests.csv` | 10,000 | Customer requests for product features |
| Product Features | `data/raw/features.csv` | 200 | Product feature catalog |
| Project Tasks | `data/raw/tasks.csv` | 3,000 | Project work items |
| Release History | `data/raw/releases.csv` | 150 | Software release records |

---

## Feature Requests (`feature_requests.csv`)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `request_id` | String | Unique request identifier | REQ-000001 |
| `feature_id` | String | Referenced feature | FEAT-0042 |
| `customer_id` | String | Customer/account identifier | CUST-0123 |
| `request_date` | Date | Date the request was submitted | 2024-03-15 |
| `demand_votes` | Integer | Number of votes/demand signals | 12 |
| `customer_segment` | String | Customer category | Enterprise, SMB, Startup |
| `urgency` | String | Urgency level | Critical, High, Medium, Low |
| `business_value` | Integer (1-100) | Estimated business value | 78 |
| `strategic_alignment` | Integer (1-100) | Alignment with strategy | 65 |
| `estimated_effort_hours` | Integer | Effort estimate in hours | 40 |
| `status` | String | Request status | Open, Accepted, Rejected |

**Missing values:** ~2% in `demand_votes` and `business_value` (intentional).

---

## Product Features (`features.csv`)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `feature_id` | String | Unique feature identifier | FEAT-0001 |
| `feature_name` | String | Descriptive name | Enhanced Dashboard |
| `product` | String | Product line | Analytics Suite |
| `category` | String | Feature category | User Interface, API |
| `customer_demand` | Integer (1-100) | Aggregated demand score | 85 |
| `business_value` | Integer (1-100) | Business impact score | 70 |
| `urgency` | String | Urgency level | Critical, High, Medium, Low |
| `strategic_alignment` | Integer (1-100) | Strategic fit score | 60 |
| `estimated_effort_hours` | Integer | Development effort estimate | 120 |
| `release_id` | String | Assigned release (if any) | REL-0025 |
| `status` | String | Feature status | Proposed, In Development, Released |

**Missing values:** ~3% in `customer_demand`, `business_value`, and `estimated_effort_hours`.

---

## Project Tasks (`tasks.csv`)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `task_id` | String | Unique task identifier | TASK-00001 |
| `project_id` | String | Parent project | PROJ-005 |
| `release_id` | String | Associated release | REL-0030 |
| `task_name` | String | Task description | Implement FEAT-0042 |
| `start_date` | Date | Task start date | 2024-06-01 |
| `planned_end_date` | Date | Planned completion date | 2024-06-20 |
| `actual_end_date` | Date | Actual completion (if done) | 2024-06-25 |
| `estimated_effort_hours` | Integer | Planned effort | 40 |
| `actual_effort_hours` | Integer | Actual effort spent | 55 |
| `dependency` | String | Dependent task ID | TASK-00023 |
| `task_status` | String | Current status | Not Started, In Progress, Completed, Blocked |
| `priority` | String | Task priority | Critical, High, Medium, Low |

**Notes:** `actual_end_date` is empty for incomplete tasks. ~30% of tasks have dependencies.

---

## Release History (`releases.csv`)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `release_id` | String | Unique release identifier | REL-0001 |
| `planned_release_date` | Date | Originally planned date | 2024-03-01 |
| `actual_release_date` | Date | Actual release date | 2024-03-08 |
| `planned_features` | Integer | Features planned | 8 |
| `delivered_features` | Integer | Features delivered | 6 |
| `planned_effort_hours` | Integer | Total planned effort | 320 |
| `actual_effort_hours` | Integer | Total actual effort | 380 |
| `delay_days` | Integer | Days delayed (0 if on time) | 7 |
| `release_status` | String | Release outcome | Released, Delayed, Cancelled |

**Notes:** `actual_release_date` is empty for cancelled or future releases.

---

## Relationships

```
Feature Requests ──(feature_id)──> Product Features
Product Features ──(release_id)──> Release History
Project Tasks    ──(release_id)──> Release History
Project Tasks    ──(dependency)──> Project Tasks (self-reference)
```

---

## Processed Datasets (Parquet)

After running the PySpark pipeline, enriched datasets are saved in `data/processed/`:

- **features** — Features enriched with demand aggregations (total_requests, total_votes, unique_customers)
- **requests** — Cleaned with parsed dates and filled nulls
- **tasks** — Cleaned with computed `overdue_days` and `effort_ratio`
- **releases** — Enriched with `feature_delivery_rate`, `effort_variance_pct`, and task aggregations

---

## Synthetic Data Assumptions

1. Features are distributed across 8 product lines and 12 categories
2. Customer segments: Enterprise, Mid-Market, SMB, Startup, Government, Education
3. ~35% of releases experience some delay; ~5% are cancelled
4. ~30% of tasks have task-to-task dependencies
5. Effort overruns of up to 50% are common
6. ~2-3% of records have intentionally missing numeric values
7. Random seed 42 ensures identical data on every generation
