# Methodology — ProductPilot

## 1. Feature Prioritization Scoring

### Approach
Features are scored on a **0–100 scale** using a weighted combination of five normalized factors:

| Factor | Default Weight | Description |
|--------|---------------|-------------|
| Customer Demand | 30% | Aggregated demand signals and vote counts |
| Business Value | 25% | Estimated business impact (1–100) |
| Urgency | 20% | Mapped from Critical=100, High=75, Medium=50, Low=25 |
| Strategic Alignment | 15% | Alignment with organizational strategy (1–100) |
| Effort Efficiency | 10% | Business value per unit of effort (higher = better) |

### Normalization
Each factor is **min-max normalized** to [0, 100] before weighting:
```
normalized = (value - min) / (max - min) × 100
```
This ensures all factors are on comparable scales regardless of their original ranges.

### Effort Efficiency
Effort efficiency rewards features that deliver more value for less development effort:
```
efficiency = business_value / (estimated_effort + 1)
```
The `+1` prevents division by zero. The result is then min-max normalized.

### Weight Validation
- Users can adjust weights via sliders
- Negative weights are set to 0
- All weights are normalized to sum to 1.0
- If all weights are 0, defaults are restored

### Priority Categories
| Score Range | Category | Action |
|-------------|----------|--------|
| 75–100 | Critical | Prioritize for next sprint |
| 50–75 | High | Schedule for upcoming release |
| 25–50 | Medium | Evaluate further |
| 0–25 | Low | Defer to future roadmap |

---

## 2. Project Risk Scoring

### Risk Factors
Each task receives a risk score (0–100) from five transparent components:

| Factor | Max Points | Calculation |
|--------|-----------|-------------|
| Overdue Days | 40 | Scaled by max overdue across all tasks |
| Effort Overrun | 25 | (actual_effort / estimated_effort) - 1, capped and scaled |
| Status Penalty | 15 | Blocked=15, Not Started=8, In Progress=3, Completed=0 |
| Dependency Risk | 10 | Based on dependent task status (Blocked dependency=10) |
| Priority Weight | 10 | Critical=10, High=7, Medium=4, Low=1 |

### Risk Categories
| Score Range | Category |
|-------------|----------|
| 67–100 | High |
| 34–66 | Medium |
| 0–33 | Low |

### Release Risk
Releases are scored by aggregating task risks:
- Average task risk score
- Number of high-risk tasks
- Overdue and blocked task counts

---

## 3. PySpark Data Pipeline

### Pipeline Steps
1. **Load** — Read CSV files with explicit schemas
2. **Validate** — Check for duplicates, nulls, invalid types
3. **Clean** — Cast types, fill missing values, parse dates
4. **Transform** — Compute derived fields (overdue_days, effort_ratio)
5. **Aggregate** — Join datasets, compute per-feature and per-release summaries
6. **Save** — Write cleaned data as Parquet (columnar, compressed)

### Spark Configuration
- Master: `local[*]` (all available cores)
- Driver memory: 2 GB
- No external cluster or HDFS dependency

---

## 4. Bloom Filter

### Algorithm
A Bloom Filter is a space-efficient probabilistic data structure for set membership testing.

**Key properties:**
- **No false negatives** — if the filter says "not present," it definitely is not
- **Possible false positives** — if the filter says "might be present," it could be wrong
- Uses multiple hash functions to map items to bit positions

### Implementation
- **Hash functions:** Double-hashing with SHA-256 and MD5 for determinism
- `position_i = (SHA256(item) + i × MD5(item)) mod bit_array_size`
- **Insert:** Set all `k` bit positions to 1
- **Lookup:** Return True only if all `k` positions are 1

### False Positive Rate
Theoretical: `(1 - e^(-kn/m))^k`
- k = number of hash functions
- n = items inserted
- m = bit array size

### Safety Rule
A Bloom Filter NEVER automatically discards items. Positive matches are flagged for exact database verification.

---

## 5. DGIM Algorithm

### Algorithm
DGIM (Datar-Gionis-Indyk-Motwani) counts 1-bits in a sliding window over a binary stream using logarithmic memory.

### Bucket Rules
1. Each 1-bit creates a new bucket of size 1
2. At most 2 buckets of each size are allowed
3. When 3 buckets of the same size exist, merge the two oldest into one bucket of double size
4. Expired buckets (outside window) are removed

### Counting
- Sum all bucket sizes
- The oldest bucket is counted at **half** its size (may be partially outside window)
- Round up the total

### Error Bound
- Worst case: ≤ 50% of true count
- In practice: typically much lower (5–15%)

### Memory
- Stores O(log²N) entries for a window of size N
- Each entry is just (timestamp, size) — two integers

---

## 6. Data Generation

### Approach
- Fixed random seed (42) for reproducibility
- Realistic distributions and relationships between datasets
- Intentional missing values (~2–3% per numeric column)
- Valid foreign key relationships maintained
- Multiple customer segments, products, categories, and statuses
