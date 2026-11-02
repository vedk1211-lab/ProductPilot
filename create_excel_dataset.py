"""
Create Excel Workbook for ProductPilot
=====================================
Builds a beautifully styled multi-sheet Excel file (.xlsx) containing:
1. Overview & Data Dictionary
2. Releases (150 records)
3. Features (200 records)
4. Tasks (3,000 records)
5. Feature Requests (10,000 records)
6. Unified Dataset (400 records)
"""

import os
import shutil
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GEN_DIR = os.path.join(PROJECT_ROOT, "data", "generated")
EXCEL_PATH_PROJECT = os.path.join(PROJECT_ROOT, "ProductPilot_Dataset.xlsx")
DESKTOP_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "ProductPilot_Dataset.xlsx"))

print("Reading CSV files...")
releases_df = pd.read_csv(os.path.join(GEN_DIR, "releases.csv"))
features_df = pd.read_csv(os.path.join(GEN_DIR, "features.csv"))
tasks_df = pd.read_csv(os.path.join(GEN_DIR, "tasks.csv"))
requests_df = pd.read_csv(os.path.join(GEN_DIR, "feature_requests.csv"))
unified_df = pd.read_csv(os.path.join(PROJECT_ROOT, "productpilot_dataset.csv"))

print("Building Excel workbook...")
with pd.ExcelWriter(EXCEL_PATH_PROJECT, engine='openpyxl') as writer:
    # 1. Summary sheet
    summary_data = {
        "Sheet Name": [
            "Releases",
            "Features",
            "Tasks",
            "Feature_Requests",
            "Unified_Dataset"
        ],
        "Record Count": [
            len(releases_df),
            len(features_df),
            len(tasks_df),
            len(requests_df),
            len(unified_df)
        ],
        "Description": [
            "Software release cycles, dates, delay days, planned vs delivered features",
            "Product catalog features with demand, value, urgency, and effort metrics",
            "Engineering tasks with dependencies, estimated vs actual hours, and status",
            "Customer demand signals, votes, urgency, and customer segments",
            "Pre-joined dataset matching ProductPilot Workspace schema for quick upload & WSJF scoring"
        ]
    }
    pd.DataFrame(summary_data).to_excel(writer, sheet_name="Overview", index=False)
    
    # 2. Main data sheets
    releases_df.to_excel(writer, sheet_name="Releases", index=False)
    features_df.to_excel(writer, sheet_name="Features", index=False)
    tasks_df.to_excel(writer, sheet_name="Tasks", index=False)
    requests_df.to_excel(writer, sheet_name="Feature_Requests", index=False)
    unified_df.to_excel(writer, sheet_name="Unified_Dataset", index=False)

print("Applying professional styles...")
wb = openpyxl.load_workbook(EXCEL_PATH_PROJECT)

# Styling palette
header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid") # Deep navy
header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
thin_border = Border(
    left=Side(style='thin', color='E2E8F0'),
    right=Side(style='thin', color='E2E8F0'),
    top=Side(style='thin', color='E2E8F0'),
    bottom=Side(style='thin', color='E2E8F0')
)
zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

for sheetname in wb.sheetnames:
    ws = wb[sheetname]
    ws.views.sheetView[0].showGridLines = True
    ws.freeze_panes = "A2"
    
    # Style header row
    for col_idx in range(1, ws.max_column + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)
        cell.border = thin_border
        
    # Auto-fit column widths & style data rows
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
            # Row borders & zebra
            if cell.row > 1:
                cell.border = thin_border
                if cell.row % 2 == 0:
                    cell.fill = zebra_fill
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

wb.save(EXCEL_PATH_PROJECT)
print(f"Saved to: {EXCEL_PATH_PROJECT}")

# Copy directly to user's Desktop for one-click access
try:
    shutil.copy2(EXCEL_PATH_PROJECT, DESKTOP_PATH)
    print(f"Copied directly to Desktop: {DESKTOP_PATH}")
except Exception as e:
    print(f"Could not copy to Desktop: {e}")
