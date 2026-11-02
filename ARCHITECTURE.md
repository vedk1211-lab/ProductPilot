# Architecture — ProductPilot

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Overview  │ │ Features │ │  Risks   │ │  Bloom   │  ...  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │             │            │             │              │
│  ┌────┴─────────────┴────────────┴─────────────┴──────────┐ │
│  │              Pandas DataFrames (UI Layer)               │ │
│  └────────────────────────┬───────────────────────────────┘ │
└───────────────────────────┼─────────────────────────────────┘
                            │
                     ┌──────┴──────┐
                     │   Parquet   │
                     │   Files     │
                     └──────┬──────┘
                            │
              ┌─────────────┴─────────────┐
              │    PySpark Pipeline        │
              │  Load → Validate → Clean  │
              │  → Transform → Aggregate  │
              │  → Save Parquet            │
              └─────────────┬─────────────┘
                            │
                     ┌──────┴──────┐
                     │  Raw CSV    │
                     │  Files      │
                     └──────┬──────┘
                            │
              ┌─────────────┴─────────────┐
              │    Data Generator          │
              │  (Synthetic, seed=42)      │
              └───────────────────────────┘
```

## Component Overview

| Component | File | Responsibility |
|-----------|------|----------------|
| Data Generator | `src/data_generator.py` | Generate synthetic CSV datasets |
| Spark Pipeline | `src/spark_pipeline.py` | ETL: validate, clean, aggregate, save Parquet |
| Feature Scoring | `src/feature_scoring.py` | Weighted priority scoring (0–100) |
| Risk Scoring | `src/risk_scoring.py` | Task/release risk calculation |
| Bloom Filter | `src/bloom_filter.py` | Probabilistic duplicate detection |
| DGIM | `src/dgim.py` | Sliding window event counting |
| Dashboard | `src/app.py` | Streamlit UI with 7 pages |
| Tests | `tests/test_modules.py` | Automated validation |

## Data Flow

1. **Generation:** `data_generator.py` creates 4 linked CSV files in `data/raw/`
2. **Processing:** `spark_pipeline.py` loads CSVs via PySpark, validates schemas, cleans data, computes aggregations, and writes Parquet to `data/processed/`
3. **Analysis:** `app.py` loads Parquet into pandas DataFrames for display and applies scoring/risk modules on the fly
4. **Algorithms:** Bloom Filter and DGIM run as in-memory Python computations triggered by user interaction

## Technology Decisions

- **PySpark local[*]:** No cluster needed; all processing on a single machine
- **Parquet output:** Columnar format with compression for efficient storage and reads
- **Streamlit:** Rapid prototyping of interactive dashboards without frontend code
- **Plotly:** Interactive, publication-quality charts
- **Deterministic hashing:** SHA-256 + MD5 for reproducible Bloom Filter results
