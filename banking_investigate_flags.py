# Investigates two specific quality flags raised by banking_quality_report.py:
#   1. 60 duplicate 'Client ID' values (rows aren't fully identical, so worth a closer look)
#   2. 39 rows with 'Age' outside the plausible 18-100 range
# Read-only -- no data is changed or saved here, this is just to inform cleaning decisions.

import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

df = pd.read_csv("banking_data.csv")

# --- 1. Duplicate Client IDs ---------------------------------------------------
print("=" * 70)
print("DUPLICATE CLIENT IDs")
print("=" * 70)
dup_ids = df.loc[df["Client ID"].duplicated(keep=False), "Client ID"].unique()
print(f"Number of distinct Client IDs that appear more than once: {len(dup_ids)}")

# Show a handful of examples side-by-side to see whether they look like the same
# person recorded twice (data entry duplicate) or two different people who happen
# to share an ID (an ID-generation problem).
sample_ids = dup_ids[:5]
for cid in sample_ids:
    print(f"\n--- Client ID: {cid} ---")
    print(df.loc[df["Client ID"] == cid, ["Client ID", "Name", "Age", "Joined Bank", "Nationality", "Occupation"]])

# --- 2. Age outliers -------------------------------------------------------------
print("\n" + "=" * 70)
print("AGE OUTLIERS (outside 18-100)")
print("=" * 70)
outliers = df.loc[(df["Age"] < 18) | (df["Age"] > 100), "Age"]
print(f"Count: {len(outliers)}")
print("\nValue counts of the outlier ages themselves:")
print(outliers.value_counts().sort_index())
print("\nOverall Age value counts at the low end (15-20) for context:")
print(df.loc[df["Age"].between(15, 20), "Age"].value_counts().sort_index())
