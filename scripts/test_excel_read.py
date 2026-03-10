from pathlib import Path
import pandas as pd

excel_path = Path("data/EM_pipeline_100.xlsx")

df = pd.read_excel(excel_path)

print("Rows:", len(df))
print("Columns:", list(df.columns))
print(df[["ID", "Title", "Status"]].head())