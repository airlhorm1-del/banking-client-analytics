# Builds a date dimension table covering the range of 'joined_bank_date' in the
# cleaned banking data, mirroring the structure already used for the retail
# project (clean/dim_date.csv). Saved separately as clean/dim_date_banking.csv
# so it doesn't collide with the retail project's date table.
#
# This enables optional tenure/cohort analysis in Power BI (e.g. "avg client
# value by acquisition year") -- not required by the 5 core business questions,
# but useful if that angle gets explored later.

import pandas as pd

df = pd.read_csv("clean/banking_data_clean.csv", parse_dates=["joined_bank_date"])

start = df["joined_bank_date"].min()
end = df["joined_bank_date"].max()
print(f"Building date dimension from {start.date()} to {end.date()}")

dim_date = pd.DataFrame({"date": pd.date_range(start, end, freq="D")})
dim_date["year"] = dim_date["date"].dt.year
dim_date["quarter"] = "Q" + dim_date["date"].dt.quarter.astype(str)
dim_date["month_number"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.strftime("%B")
dim_date["date"] = dim_date["date"].dt.strftime("%Y-%m-%d")

out_path = "clean/dim_date_banking.csv"
dim_date.to_csv(out_path, index=False)
print(f"Saved: {out_path} ({len(dim_date)} rows)")
print(dim_date.head())
