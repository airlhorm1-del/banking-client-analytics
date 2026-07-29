# Extracts the lookup/dimension tables (Banking Relationship, Gender, Investment Advisor)
# from the Power BI file "Banking Dashboard.pbix" (in Downloads) and saves them as CSVs.
#
# Why this is needed: banking_data.csv only stores coded IDs (BRId, GenderId, IAId) with
# no legend. The .pbix report's underlying data model has the real lookup tables that
# translate those codes into readable labels -- this script pulls them out so we can
# join them onto the main data during cleaning/analysis.
#
# This only reads the .pbix file; it does not modify it. Output is written to clean/
# since these are derived reference tables, not raw source data.

import os
from pbixray import PBIXRay

pbix_path = r"C:\Users\user\Downloads\Banking Dashboard.pbix"
model = PBIXRay(pbix_path)

os.makedirs("clean", exist_ok=True)

lookup_tables = {
    "Banking Relationship": "dim_banking_relationship.csv",
    "Gender": "dim_gender.csv",
    "Investment Advisor": "dim_investment_advisor.csv",
}

for table_name, filename in lookup_tables.items():
    df = model.get_table(table_name)
    out_path = os.path.join("clean", filename)
    df.to_csv(out_path, index=False)
    print(f"Saved '{table_name}' ({len(df)} rows) -> {out_path}")
    print(df)
    print()
