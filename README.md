# ProductPilot

**Big Data Analytics for Product Prioritization and Project Risk Management Using Apache Spark**

> ⚠️ All data in this project is **synthetic**, generated for demonstration purposes.
> Scores and recommendations are analytical tools — they should inform, not replace, human judgment.

---

## Overview

ProductPilot is a decision-support platform that helps product managers:

- **Prioritize product features** using configurable weighted scoring
- **Assess project delivery risks** with transparent risk analysis
- **Screen for duplicates** using a working Bloom Filter implementation
- **Monitor event streams** using the DGIM streaming algorithm
- **Generate actionable recommendations** from computed analytics

Built with **Apache Spark (PySpark)** for data processing, with two dashboard interfaces:
- **Bolt.new React Frontend** (Vite + React 18 + Tailwind CSS) on `http://localhost:5173`
- **FastAPI Backend Bridge** on `http://localhost:8000`
- **Streamlit Dashboard** on `http://localhost:8001`

---

## Architecture

```
ProductPilot/
├── bolt-frontend/            # Bolt.new React 18 + Vite frontend
│   ├── src/pages/            # Dashboard, Features, Risk, Bloom, DGIM, Pipeline, Workspace
│   └── src/data/             # apiClient.ts, analysis.ts, types.ts
├── src/
│   ├── api.py                # FastAPI backend bridge (port 8000)
│   ├── app.py                # Streamlit dashboard (port 8001)
│   ├── data_generator.py     # Synthetic data generation
│   ├── spark_pipeline.py     # PySpark ETL pipeline
│   ├── feature_scoring.py    # Feature prioritization scoring
│   ├── risk_scoring.py       # Project risk scoring
│   ├── bloom_filter.py       # Bloom Filter implementation
│   └── dgim.py               # DGIM streaming algorithm
├── tests/
│   └── test_modules.py       # Automated tests (pytest)
├── data/
│   ├── raw/                  # Generated CSV datasets
│   └── processed/            # Spark-processed Parquet files
├── requirements.txt
├── README.md
├── DATA_DICTIONARY.md
├── METHODOLOGY.md
├── ARCHITECTURE.md
├── EVALUATION.md
├── POSTER_CONTENT.md
└── DEMO_SCRIPT.md
```

---

## Prerequisites

- **Python 3.9+** (tested with 3.11)
- **Java 8 or 11+** (required by Spark)
- **pip** (Python package manager)

---

## Quick Start

### 1. Install Dependencies

```bash
cd ProductPilot
pip install -r requirements.txt
```

### 2. Generate Synthetic Data

```bash
python src/data_generator.py
```

This creates 4 CSV files in `data/raw/` with 10,000+ feature requests, 200 features, 3,000 tasks, and 150 releases.

### 3. Run PySpark Pipeline

```bash
python src/spark_pipeline.py
```

Processes raw CSVs → validates → cleans → aggregates → saves as Parquet in `data/processed/`.

### 4. Run Tests

```bash
pytest tests/ -v
```

### 5. Launch Dashboard

```bash
streamlit run src/app.py
```

Open `http://localhost:8501` in your browser.

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| 📊 Executive Overview | KPIs, trends, management alerts |
| ⭐ Feature Prioritization | Weighted scoring, filters, rankings |
| ⚠️ Project Delivery Risks | Risk scores, overdue analysis, release status |
| 🔬 Bloom Filter Lab | Interactive Bloom Filter demonstration & membership query |
| 📈 DGIM Streaming | Sliding window event counting simulation & custom task streams |
| 💡 Recommendations | Data-driven management recommendations |
| 🔧 Pipeline & Evaluation | Processing details and algorithm evaluation |
| 📥 User Data Workspace | Upload custom CSV/Excel, quick-add form, and live spreadsheet editor |

---

## 📥 Custom User Data Input

ProductPilot enables users to input their own custom data and automatically executes all analytical features on their dataset:

1. **📁 CSV & Excel File Upload**: Upload any `.csv`, `.xlsx`, or `.xls` file. Smart semantic column detection automatically maps common header names (`feature_name`, `customer_demand`, `business_value`, `urgency`, `dev_effort`, `task_status`, `planned_date`, etc.).
2. **✍️ Interactive Form Input**: Quickly create and add individual features and tasks on the fly using intuitive sliders and inputs.
3. **📊 Live Spreadsheet Editor**: Edit cells, paste data from Excel/Google Sheets, add or delete rows directly in an interactive grid (`st.data_editor`).
4. **🚀 1-Click Sample Dataset**: Instantly load a curated 10-feature SaaS dataset or download standard CSV / Excel templates.
5. **🔄 Seamless Global Recomputation**: All analytics (WSJF prioritization scores, delivery risk scoring, Bloom Filter indexing, DGIM stream monitoring, and executive KPIs) live-update across all pages for the active dataset.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Programming | Python 3.11 |
| Big Data | Apache Spark 3.5 (PySpark) |
| Dashboard | Streamlit |
| Charts | Plotly |
| Data Storage | CSV (raw), Parquet (processed) |
| Testing | pytest |

---

## Troubleshooting

### Java not found
Spark requires Java. Install JDK 11+ and ensure `java` is on your PATH:
```bash
java -version
```

### PySpark fails to start
- Ensure `JAVA_HOME` is set correctly
- On Windows: `set JAVA_HOME=C:\Program Files\Java\jdk-11`

### Streamlit port in use
```bash
streamlit run src/app.py --server.port 8502
```

### Data not found
Run `python src/data_generator.py` followed by `python src/spark_pipeline.py` before launching the dashboard.

---

## License

This project is for educational and demonstration purposes only.

---

## Author

College Big Data Analytics Project — ProductPilot
