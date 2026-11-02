import json
import pandas as pd
import numpy as np

features_df = pd.read_parquet('data/processed/features')
tasks_df = pd.read_parquet('data/processed/tasks')
releases_df = pd.read_parquet('data/processed/releases')

print(f"Features: {len(features_df)}, Tasks: {len(tasks_df)}, Releases: {len(releases_df)}")
