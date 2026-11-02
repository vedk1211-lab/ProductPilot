# Poster Content — ProductPilot

## Title
**ProductPilot: Big Data Analytics for Product Prioritization and Project Risk Management Using Apache Spark**

---

## Problem Statement
Product managers face critical challenges:
- Hundreds of feature requests compete for limited development capacity
- No systematic method to prioritize features objectively
- Project delivery risks are identified too late
- Manual tracking fails at scale

**How can data analytics help product teams make better prioritization and risk management decisions?**

---

## Objectives
1. Build a **configurable feature prioritization system** using weighted scoring
2. Implement **transparent project risk analysis** with actionable recommendations
3. Demonstrate **Big Data processing** with Apache Spark (PySpark)
4. Implement **Bloom Filter** for efficient duplicate detection
5. Implement **DGIM algorithm** for approximate streaming analytics
6. Create an **interactive analytics dashboard** for decision support

---

## Methodology

### Feature Prioritization (Weighted Scoring)
- 5 factors: Customer Demand (30%), Business Value (25%), Urgency (20%), Strategic Alignment (15%), Effort Efficiency (10%)
- Min-max normalization to [0, 100]
- Configurable weights with real-time recalculation

### Risk Scoring (Factor-Based)
- 5 risk factors: Overdue days, effort overrun, status, dependencies, priority
- Transparent risk categories: Low / Medium / High
- Release-level risk aggregation

### Bloom Filter (Probabilistic Duplicate Detection)
- Space-efficient membership testing
- Deterministic double-hashing (SHA-256 + MD5)
- No false negatives; bounded false positive rate

### DGIM (Streaming Event Counting)
- Approximate 1-bit counting in sliding window
- O(log² N) memory vs O(N) for exact counting
- ≤50% worst-case approximation error

---

## Architecture

```
Data Generation → PySpark Pipeline → Parquet Storage → Streamlit Dashboard
     (CSV)          (ETL + Spark)      (Columnar)         (Interactive UI)
```

**Tech Stack:** Python, PySpark, Streamlit, Plotly, Parquet, pytest

---

## Key Results

| Metric | Value |
|--------|-------|
| Feature Requests Processed | 10,000+ |
| Features Analyzed | 200 |
| Tasks Tracked | 3,000 |
| Releases Monitored | 150 |
| Bloom Filter Memory Savings | ~40× vs exact set |
| DGIM Typical Error | 5–15% |
| Automated Tests | 45 |

---

## Algorithms Demonstrated

### Bloom Filter
- Configurable bit array and hash functions
- Measured vs expected false positive rates
- Memory comparison with exact set storage
- Interactive lookup demonstration

### DGIM
- Configurable window size and stream patterns
- Real-time accuracy comparison (approximate vs exact)
- Bucket visualization and merging rules
- Alert threshold monitoring

---

## Dashboard Screenshots
*(7 interactive pages: Overview, Prioritization, Risks, Bloom Filter, DGIM, Recommendations, Evaluation)*

---

## Conclusion
ProductPilot demonstrates how Big Data analytics techniques can support product management decisions:
- **Weighted scoring** provides systematic, configurable feature prioritization
- **Risk analysis** enables early identification of delivery problems
- **Bloom Filters** offer memory-efficient duplicate screening
- **DGIM** enables scalable streaming event monitoring
- **Apache Spark** processes data at scale using a familiar Python interface

All results are computed from data — no hardcoded values. The platform is designed as a decision-support tool that informs rather than replaces human judgment.

---

## Future Work
- Machine learning models for task delay prediction
- Real-time data ingestion and streaming
- Integration with project management tools (Jira, Asana)
- Multi-team collaboration features
- A/B testing for scoring weight optimization
