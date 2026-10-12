"""Combine both sheets (2009-2010 and 2010-2011) of the UCI Excel file into one CSV.
Usage: python src/convert_excel.py data/online_retail_II.xlsx
"""
import sys
from pathlib import Path
import pandas as pd

src = Path(sys.argv[1] if len(sys.argv) > 1 else "data/online_retail_II.xlsx")
sheets = pd.read_excel(src, sheet_name=None)  # dict of all sheets
df = pd.concat(sheets.values(), ignore_index=True)
out = src.with_suffix(".csv")
df.to_csv(out, index=False)
print(f"{len(df):,} rows written to {out}")
