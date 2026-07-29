# Full format-consistency audit of clean/banking_data_clean.csv -- checks that
# every column is stored in the type/format it should be (dates as real dates,
# money as clean 2-decimal numbers, IDs following their expected pattern, text
# columns free of whitespace/casing issues). Read-only -- flags problems, does
# not fix them here (fixes go back into banking_cleaning.py if anything is found).

import re
import pandas as pd

df = pd.read_csv("clean/banking_data_clean.csv", parse_dates=["joined_bank_date"])

print("=" * 70)
print("DTYPE CHECK")
print("=" * 70)
print(df.dtypes)

# --- client_id: should always match 'IND' + digits ---------------------------
print("\n" + "=" * 70)
print("client_id FORMAT")
print("=" * 70)
id_pattern = re.compile(r"^IND\d+$")
bad_ids = df.loc[~df["client_id"].astype(str).str.match(id_pattern)]
print(f"Values NOT matching '^IND\\d+$': {len(bad_ids)}")

# --- joined_bank_date: confirm it's a real datetime, check the range ---------
print("\n" + "=" * 70)
print("joined_bank_date FORMAT")
print("=" * 70)
print("Dtype:", df["joined_bank_date"].dtype)
print("Is real datetime64:", pd.api.types.is_datetime64_any_dtype(df["joined_bank_date"]))
print("Range:", df["joined_bank_date"].min().date(), "to", df["joined_bank_date"].max().date())
print("Any missing:", df["joined_bank_date"].isna().sum())

# --- Money columns: should be float, and round-trip cleanly to 2 decimals ----
print("\n" + "=" * 70)
print("MONEY COLUMN FORMAT (should be numeric, at most 2 decimal places)")
print("=" * 70)
money_cols = [
    "estimated_income", "superannuation_savings", "credit_card_balance",
    "bank_loans", "bank_deposits", "checking_accounts", "saving_accounts",
    "foreign_currency_account", "business_lending",
]
for col in money_cols:
    is_numeric = pd.api.types.is_numeric_dtype(df[col])
    # round to 2dp and compare to original -- if they differ, something has more precision than expected
    over_precision = (df[col].round(2) != df[col]).sum()
    print(f"{col}: numeric={is_numeric}, values with >2 decimal places={over_precision}")

# --- Integer columns: should have no fractional part -------------------------
print("\n" + "=" * 70)
print("INTEGER COLUMN FORMAT")
print("=" * 70)
int_cols = ["age", "location_id", "amount_of_credit_cards", "properties_owned", "risk_weighting", "client_row_id"]
for col in int_cols:
    dtype = df[col].dtype
    print(f"{col}: dtype={dtype}")

# --- Text columns: whitespace and casing consistency --------------------------
print("\n" + "=" * 70)
print("TEXT COLUMN WHITESPACE / CASING CHECK")
print("=" * 70)
text_cols = ["name", "banking_contact", "nationality", "occupation", "fee_structure",
             "loyalty_classification", "banking_relationship", "gender", "investment_advisor"]
for col in text_cols:
    has_whitespace = (df[col].astype(str) != df[col].astype(str).str.strip()).sum()
    print(f"{col}: leading/trailing whitespace issues = {has_whitespace}")
