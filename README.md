<<<<<<< HEAD
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
=======
# ProductPilot – Big Data Analytics for Product Prioritization and Project Risk Management

ProductPilot is a Big Data Analytics framework designed to support product feature prioritization and project risk management. It combines large-scale data processing techniques with probabilistic data structures and streaming algorithms to help product and project teams make informed, data-driven decisions.

The framework focuses on identifying high-priority product features, monitoring project progress, detecting potential duplicate feature requests, and tracking recent activity in data streams.

## Project Overview

In product development, teams often receive large volumes of feature requests, customer feedback, and project updates. Managing this information manually can make it difficult to identify important features and recognize potential project delays.

ProductPilot addresses this challenge by combining Big Data Analytics techniques to organize information, prioritize product requirements, and monitor project performance.

## Key Features

- **Product Feature Prioritization:** Evaluates feature requests using factors such as business value, demand, urgency, strategic relevance, and development effort.
- **Project Risk Management:** Helps identify potential project risks by examining task progress, delivery status, and project-related indicators.
- **Large-Scale Data Processing:** Uses Apache Spark to process and analyze structured datasets.
- **Duplicate Request Detection:** Applies Bloom Filters to identify potentially repeated feature requests.
- **Real-Time Stream Analysis:** Uses the DGIM algorithm to estimate the number of recent events in a data stream.
- **Data Visualization:** Presents analytical results through dashboards to support decision-making.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming and data processing |
| Apache Spark / PySpark | Distributed data processing |
| SQL | Data querying and management |
| Bloom Filters | Probabilistic duplicate detection |
| DGIM Algorithm | Approximate counting of recent stream events |
| FastAPI | Backend API development |
| React | User interface |
| Streamlit | Analytical dashboard |

## Algorithms and Methodology

### 1. Apache Spark

Apache Spark is used to process and analyze structured datasets efficiently. It supports data transformation, aggregation, and large-scale analytical operations.

### 2. Bloom Filter

A Bloom Filter is a probabilistic data structure used to check whether an element may already exist in a collection.

In ProductPilot, it is applied to potential duplicate feature request detection. It is memory-efficient but can produce false positives.

### 3. DGIM Algorithm

The DGIM (Datar-Gionis-Indyk-Motwani) algorithm estimates the number of recent occurrences of an event in a binary data stream.

It uses compact buckets to maintain an approximate count over a sliding time window, reducing memory requirements compared with storing the entire stream.

### 4. Feature Prioritization

Product features are evaluated using multiple factors, including:

- Business value
- Customer demand
- Urgency
- Strategic relevance
- Development effort

The resulting prioritization helps teams identify which features should receive attention first.

### 5. Project Risk Analysis

Project risk analysis considers task progress, delivery status, and potential delays to help identify areas that may require attention.

## System Architecture

The overall framework follows this workflow:

```text
       Input Datasets
             |
             v
     Data Processing
       (Python / Spark)
             |
             v
      Analytical Layer
             |
      +------+------+
      |      |      |
      v      v      v
   Feature Bloom  DGIM
   Ranking Filter Algorithm
      |      |      |
      +------+------+
             |
             v
      Project Risk
         Analysis
             |
             v
       Backend APIs
         (FastAPI)
             |
             v
       User Interface
          (React)
             |
             v
      Analytical Dashboard
```

## Project Objectives

1. To develop a data-driven approach for product feature prioritization.
2. To apply Big Data Analytics techniques to structured product and project datasets.
3. To explore memory-efficient duplicate detection using Bloom Filters.
4. To implement approximate stream counting using the DGIM algorithm.
5. To support project monitoring and risk identification through analytical insights.

## Repository Structure

The repository may be organized into the following modules:

```text
ProductPilot-Big-Data-Analytics/
│
├── data/
│   ├── feature_requests.csv
│   ├── project_tasks.csv
│   └── release_history.csv
│
├── backend/
│   └── API implementation
│
├── frontend/
│   └── User interface
│
├── algorithms/
│   ├── bloom_filter.py
│   └── dgim.py
│
├── notebooks/
│   └── Data analysis and experiments
│
├── requirements.txt
├── README.md
└── .gitignore
```

*Note: Adjust this structure to match the actual files and folders in your repository.*

## Installation and Execution

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/ProductPilot.git
```

Navigate to the project directory:

```bash
cd ProductPilot
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Follow the setup instructions for the backend, frontend, and analytical modules provided in their respective directories.

## Research Paper

This project is also documented in a research paper titled:

**ProductPilot: A Big Data Analytics Framework for Product Feature Prioritization and Project Risk Management Using Apache Spark, Bloom Filters and DGIM Stream Counting.**

The research paper describes the framework, its methodology, algorithms, and application of Big Data Analytics to product and project management.

## Future Scope

- Integration with project management platforms.
- Improved predictive project risk analysis.
- Support for larger and continuously updated datasets.
- Advanced feature recommendation techniques.
- Enhanced analytical dashboards and reporting capabilities.

## Author

**Vedant Kulkarni**
>>>>>>> 2965d15257db9b8d4a532f07d1edd2d0c9496ede
