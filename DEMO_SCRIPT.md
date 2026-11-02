# Demo Script — ProductPilot

## 5-Minute Live Demonstration Guide

### Setup (Before Demo)
```bash
# Ensure data is generated and pipeline has run
python src/data_generator.py
python src/spark_pipeline.py
streamlit run src/app.py
```

---

### Minute 1: Executive Overview (60 seconds)

1. Open the dashboard at `http://localhost:8501`
2. **Show the sidebar** — "ProductPilot is a Big Data analytics platform for product and project management"
3. **Point to KPI cards** — "We're analyzing 10,000+ feature requests, 200 features, 3,000 tasks, and 150 releases — all processed by Apache Spark"
4. **Show the charts** — "Features by product and task status distribution give an at-a-glance view"
5. **Show management alerts** — "The system automatically identifies overdue and blocked tasks"
6. **Show request trend** — "Monthly request volume shows demand patterns over time"

---

### Minute 2: Feature Prioritization (60 seconds)

1. Navigate to **⭐ Feature Prioritization**
2. **Show weight sliders** — "Managers can configure how much each factor matters"
3. **Adjust a weight** (e.g., set Customer Demand to 80, others to 5) — "Watch scores recalculate in real-time"
4. **Show ranked table** — "Features are ranked with transparent scores and recommended actions"
5. **Click a feature** — "The detail view explains exactly why a feature got its score"
6. **Use a filter** (e.g., Product = "Analytics Suite") — "Filters narrow focus to specific products or categories"

---

### Minute 3: Project Risk Management (60 seconds)

1. Navigate to **⚠️ Project Delivery Risks**
2. **Show KPIs** — "We track total, completed, overdue, and high-risk tasks"
3. **Show risk distribution chart** — "Tasks are scored using 5 transparent risk factors"
4. **Show release status table** — "Each release shows feature delivery rate and risk level"
5. **Filter by risk level** (select "High") — "Managers can focus on the most critical items"
6. **Point to recommendations** — "Every recommendation links to an observable metric"

---

### Minute 4: Bloom Filter & DGIM (60 seconds)

**Bloom Filter (30 seconds):**
1. Navigate to **🔬 Bloom Filter Lab**
2. **Explain briefly** — "Bloom Filter is a probabilistic data structure for fast membership testing"
3. **Click Run** — "We insert 5,000 request IDs and measure false positives"
4. **Show results** — "Zero false negatives, measurable false positive rate, 40× memory savings"
5. **Type a request ID** — "Interactive lookup: this ID might exist, verify in the database"

**DGIM (30 seconds):**
1. Navigate to **📈 DGIM Streaming**
2. **Explain** — "DGIM counts events in a sliding window using logarithmic memory"
3. **Click Run** — "Approximate vs exact count — typically within 5–15% error"
4. **Show bucket chart** — "These buckets represent the DGIM data structure"

---

### Minute 5: Pipeline & Wrap-Up (60 seconds)

1. Navigate to **🔧 Pipeline & Evaluation**
2. **Show record counts** — "All data was processed by PySpark in local mode"
3. **Show data quality** — "Completeness metrics for each dataset"
4. **Show algorithm evaluations** — "Bloom Filter and DGIM metrics computed from actual runs"
5. **Show limitations** — "We're transparent about what this system can and cannot do"

**Closing statement:**
> "ProductPilot demonstrates how Big Data techniques — Spark, Bloom Filters, and DGIM — can support product management decisions. All results are computed from data, not hardcoded. The system is a decision-support tool that informs rather than replaces human judgment."

---

### Backup Questions to Prepare For

1. **Why Bloom Filter?** — Fast duplicate screening without loading the entire database into memory
2. **Why DGIM?** — Monitors event streams with constant memory instead of storing every event
3. **Why PySpark?** — Scalable processing; the same pipeline could run on a cluster for larger data
4. **Are the scores accurate?** — They're systematic and configurable, but they're recommendations, not ground truth
5. **What would you add next?** — ML prediction for task delays, real-time streaming, tool integration
