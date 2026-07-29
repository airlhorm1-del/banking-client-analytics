# Data quality report for banking_data.csv
# This script only reads and inspects the data. It does not change or save anything.
# Findings here are what will drive the cleaning decisions in the next step.

import pandas as pd

# Widen pandas display settings so all columns print instead of being truncated with "..."
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

# Load the raw CSV file into a DataFrame (a table-like structure in pandas)
df = pd.read_csv("banking_data.csv")

# --- Preview the data so we know what we're working with before doing anything else ---
print("=" * 70)
print("PREVIEW")
print("=" * 70)
print("\nFirst 5 rows:")
print(df.head())
print("\nShape (rows, columns):", df.shape)
print("\nColumn data types:")
print(df.dtypes)

# --- Row count ---
print("\n" + "=" * 70)
print("ROW COUNT")
print("=" * 70)
print(f"Total rows: {len(df)}")

# --- Missing values per column ---
# isna() flags each cell as True/False depending on whether it's missing (NaN)
# sum() adds up the True values (True counts as 1) for each column
print("\n" + "=" * 70)
print("MISSING VALUES PER COLUMN")
print("=" * 70)
missing_counts = df.isna().sum()
missing_pct = (missing_counts / len(df) * 100).round(2)
missing_summary = pd.DataFrame({"missing_count": missing_counts, "missing_pct": missing_pct})
print(missing_summary)

# --- Duplicate rows ---
# duplicated() flags rows that are exact copies of an earlier row
print("\n" + "=" * 70)
print("DUPLICATE ROWS")
print("=" * 70)
dup_count = df.duplicated().sum()
print(f"Fully duplicated rows (all columns identical): {dup_count}")

# 'Client ID' should be a unique identifier for each customer -- check separately,
# since two rows could share a Client ID without being fully identical rows
# (e.g. the same customer entered twice with slightly different details).
dup_client_ids = df["Client ID"].duplicated().sum()
print(f"Duplicate values in 'Client ID' column: {dup_client_ids}")

# --- Look for values that seem invalid ---
print("\n" + "=" * 70)
print("POTENTIALLY INVALID VALUES")
print("=" * 70)

# Numeric columns: check for negative numbers and zeros where they may not make sense,
# plus basic descriptive stats to help spot outliers (e.g. absurdly large/small values).
numeric_cols = df.select_dtypes(include="number").columns
for col in numeric_cols:
    negatives = (df[col] < 0).sum()
    zeros = (df[col] == 0).sum()
    print(f"\nColumn: {col}")
    print(df[col].describe())
    print(f"Negative values: {negatives}")
    print(f"Zero values: {zeros}")

# Age deserves a specific sanity check -- flag anything outside a plausible human range.
implausible_age = ((df["Age"] < 18) | (df["Age"] > 100)).sum()
print(f"\nAge values outside a plausible 18-100 range: {implausible_age}")

# --- Date-like columns ---
# 'Joined Bank' is stored as text (e.g. '06-05-2019'). Convert it to a real date and see
# how many values fail to parse, plus check for impossible dates (e.g. in the future).
print("\n" + "=" * 70)
print("DATE COLUMN CHECK: 'Joined Bank'")
print("=" * 70)
joined = pd.to_datetime(df["Joined Bank"], format="%d-%m-%Y", errors="coerce")
bad_dates = joined.isna().sum() - df["Joined Bank"].isna().sum()  # newly-NaT after conversion = unparseable
print(f"Values that don't parse as a valid date (format dd-mm-yyyy): {bad_dates}")
if joined.notna().any():
    print(f"Date range: {joined.min().date()} to {joined.max().date()}")
    future_dates = (joined > pd.Timestamp.now()).sum()
    print(f"Dates in the future: {future_dates}")

# --- Text/categorical columns ---
# Show unique value counts to spot inconsistent labels (e.g. "male" vs "Male", extra whitespace).
print("\n" + "=" * 70)
print("TEXT / CATEGORY COLUMNS")
print("=" * 70)
text_cols = df.select_dtypes(include="object").columns
text_cols = [c for c in text_cols if c not in ["Joined Bank", "Client ID", "Name"]]
for col in text_cols:
    unique_vals = df[col].nunique(dropna=True)
    print(f"\nColumn: {col} ({unique_vals} unique values)")
    if unique_vals <= 25:
        print(df[col].value_counts(dropna=False))
    else:
        has_whitespace_issue = df[col].dropna().astype(str).apply(lambda x: x != x.strip()).sum()
        print(f"  Values with leading/trailing whitespace: {has_whitespace_issue}")
        print(f"  Sample values: {df[col].dropna().unique()[:10]}")

# --- Coded ID columns (BRId, GenderId, IAId) ---
# These look like lookup/reference codes rather than raw values. No legend is provided
# in the file, so we just report their distinct values here -- meaning will need to be
# confirmed with the user or a reference table before they're used in analysis.
print("\n" + "=" * 70)
print("CODED ID COLUMNS (no legend provided in file)")
print("=" * 70)
for col in ["BRId", "GenderId", "IAId"]:
    print(f"\nColumn: {col}")
    print(df[col].value_counts().sort_index())
