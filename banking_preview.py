# Initial preview of banking_data.csv
# This script only reads and inspects the data. It does not change or save anything.
# Purpose: confirm the shape/structure of the raw file before any cleaning or analysis begins.

import pandas as pd

# Widen pandas display settings so all columns print instead of being truncated with "..."
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

# Load the raw banking CSV exactly as-is (read-only -- we never modify this file)
df = pd.read_csv("banking_data.csv")

# First 5 rows, so we can see what the actual data looks like
print("=== HEAD (first 5 rows) ===")
print(df.head())

# Shape (rows, columns) confirms how much data we're dealing with
print("\n=== SHAPE (rows, columns) ===")
print(df.shape)

# The data type pandas inferred for each column (numbers vs text vs dates, etc.)
print("\n=== DTYPES (column data types) ===")
print(df.dtypes)
