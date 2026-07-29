# Prepares the data sources for the Power BI project (powerbi_dashboard/BankingDashboard.pbip).
# Reads the already-cleaned data (clean/banking_data_clean.csv) -- never the raw file --
# and writes two new files Power BI will import:
#   1. clean/banking_data_powerbi.csv -- the client table plus the derived metrics used
#      by the 5 business-question charts (total value, product count, cross-sell ratio),
#      precomputed here so the Power BI model only needs simple SUM/AVERAGE measures
#      instead of complex DAX.
#   2. clean/risk_correlations.csv -- the correlation-with-risk-weighting numbers from
#      banking_charts.py, as a small standalone reference table (DAX has no built-in
#      correlation function, and this stat isn't meant to be sliced per-client anyway).

import pandas as pd

df = pd.read_csv("clean/banking_data_clean.csv", parse_dates=["joined_bank_date"])

# --- Derived metric 1: total_relationship_value ------------------------------
# Same definition used in banking_charts.py: the sum of every dollar figure the
# client represents to the bank.
VALUE_COLS = [
    "bank_deposits", "saving_accounts", "checking_accounts",
    "foreign_currency_account", "superannuation_savings",
    "business_lending", "bank_loans", "credit_card_balance",
]
df["total_relationship_value"] = df[VALUE_COLS].sum(axis=1)

# --- Derived metric 2: value_quintile ------------------------------------------
# Splits clients into 5 equal-sized groups by total_relationship_value, used for
# the Q1 concentration chart.
df["value_quintile"] = pd.qcut(df["total_relationship_value"], 5,
                                labels=["Bottom 20%", "2nd", "3rd", "4th", "Top 20%"])

# --- Derived metric 3: product_count and products_per_100k_income -------------
# Same definition used in banking_charts.py: how many of the 6 core products a
# client holds, and that count relative to their income (Q3 cross-sell chart).
product_cols = ["bank_loans", "bank_deposits", "checking_accounts",
                 "saving_accounts", "foreign_currency_account", "business_lending"]
df["product_count"] = (df[product_cols] > 0).sum(axis=1)
df["products_per_100k_income"] = df["product_count"] / (df["estimated_income"] / 100_000)

out_path = "clean/banking_data_powerbi.csv"
df.to_csv(out_path, index=False)
print(f"Saved: {out_path}  ({len(df)} rows, {len(df.columns)} columns)")

# --- Standalone risk-correlation reference table (from banking_charts.py Q2) --
numeric_predictors = [
    "age", "estimated_income", "superannuation_savings", "amount_of_credit_cards",
    "credit_card_balance", "bank_loans", "bank_deposits", "checking_accounts",
    "saving_accounts", "foreign_currency_account", "business_lending", "properties_owned",
]
correlations = df[numeric_predictors + ["risk_weighting"]].corr()["risk_weighting"].drop("risk_weighting")
correlations = correlations.sort_values(ascending=False).reset_index()
correlations.columns = ["driver", "correlation_with_risk"]

corr_path = "clean/risk_correlations.csv"
correlations.to_csv(corr_path, index=False)
print(f"Saved: {corr_path} ({len(correlations)} rows)")
print(correlations)
