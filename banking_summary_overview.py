# Quick descriptive overview of clean/banking_data_clean.csv -- pulls the key
# numbers used to summarize "what this table talks about" before we move into
# chart-building for the 3 business questions. Read-only, no data is changed.

import pandas as pd

df = pd.read_csv("clean/banking_data_clean.csv", parse_dates=["joined_bank_date"])

print("Rows (clients):", len(df))
print("Join date range:", df["joined_bank_date"].min().date(), "to", df["joined_bank_date"].max().date())
print("Age range:", df["age"].min(), "-", df["age"].max(), " | mean:", round(df["age"].mean(), 1))

print("\nGender split:")
print(df["gender"].value_counts())

print("\nBanking relationship split:")
print(df["banking_relationship"].value_counts())

print("\nNationality split:")
print(df["nationality"].value_counts())

print("\nLoyalty classification split:")
print(df["loyalty_classification"].value_counts())

print("\nEstimated income: mean =", round(df["estimated_income"].mean(), 2),
      "| median =", round(df["estimated_income"].median(), 2),
      "| min =", df["estimated_income"].min(), "| max =", df["estimated_income"].max())

print("\nAverage balances by product:")
for col in ["bank_deposits", "saving_accounts", "checking_accounts", "bank_loans",
            "business_lending", "credit_card_balance", "foreign_currency_account",
            "superannuation_savings"]:
    print(f"  {col}: mean = {df[col].mean():,.2f}")

print("\nRisk weighting distribution:")
print(df["risk_weighting"].value_counts().sort_index())

print("\nNumber of distinct investment advisors:", df["investment_advisor"].nunique())
print("Number of distinct occupations:", df["occupation"].nunique())
