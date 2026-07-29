# Cleans banking_data.csv according to the decisions agreed after the quality scan
# (see banking_quality_report.py and banking_investigate_flags.py) and writes the
# result to clean/banking_data_clean.csv. The original CSV is never modified --
# this script only reads the raw file (+ the lookup tables already extracted to
# clean/) and writes a new file.
#
# Decisions applied here (agreed after investigation):
#   1. Duplicate 'Client ID' values (60 rows) are DIFFERENT real clients whose ID
#      happens to collide -- not the same person twice. No rows are dropped for
#      this. Instead we add a surrogate key so every row has a guaranteed-unique ID.
#   2. The 39 "outlier" ages are all exactly 17 -- a valid age for a bank client
#      (e.g. youth/custodial account), not a data error. No rows are dropped.
#   3. Zero balances in loan/deposit/account columns are valid (client just may not
#      hold that product). No action needed.
#   4. 'Properties Owned' = 0 is valid (not everyone owns property). No action needed.
#   5. BRId / GenderId / IAId are coded foreign keys. Their lookup tables were
#      recovered from Banking Dashboard.pbix and saved to clean/dim_*.csv. Here we
#      join them in to replace the bare codes with readable labels.

import os
import pandas as pd

# --- Load the raw data and preview it before any processing (project rule) ---
df = pd.read_csv("banking_data.csv")
print("=== PREVIEW (raw data, before cleaning) ===")
print(df.head())
print("\nShape:", df.shape)
print("\nDtypes:\n", df.dtypes)

before_count = len(df)

# --- Step 1: add a surrogate key ---------------------------------------------
# 'Client ID' is not a reliable unique identifier (60 rows share an ID with a
# different client), so we add our own row-based key that IS guaranteed unique,
# for any downstream work that needs one (e.g. joins, tracking individual records).
df.insert(0, "client_row_id", range(1, len(df) + 1))
print(f"\nStep 1: added surrogate key 'client_row_id' (1 to {len(df)}) -- 'Client ID' is not unique on its own")

# --- Step 2: parse 'Joined Bank' as a real date -------------------------------
# The raw column is text in dd-mm-yyyy format (e.g. '06-05-2019'). Converting it
# to an actual date type allows proper date math/sorting/filtering later instead
# of treating it as a string.
parsed_dates = pd.to_datetime(df["Joined Bank"], format="%d-%m-%Y")
unparsed = parsed_dates.isna().sum()
df["Joined Bank"] = parsed_dates
print(f"Step 2: parsed 'Joined Bank' to a real date column ({unparsed} values failed to parse)")

# --- Step 3: join in the lookup tables for BRId / GenderId / IAId ------------
# These three columns were bare numeric codes with no legend in the raw file.
# The actual labels were recovered from the Power BI data model (Banking
# Dashboard.pbix) and saved as reference tables in clean/. We merge them in here
# so the clean dataset is human-readable instead of relying on undocumented codes.
dim_banking_relationship = pd.read_csv("clean/dim_banking_relationship.csv")
dim_gender = pd.read_csv("clean/dim_gender.csv")
dim_investment_advisor = pd.read_csv("clean/dim_investment_advisor.csv")

rows_before_merge = len(df)
df = df.merge(dim_banking_relationship, on="BRId", how="left")
df = df.merge(dim_gender, on="GenderId", how="left")
df = df.merge(dim_investment_advisor, on="IAId", how="left")
assert len(df) == rows_before_merge, "Row count changed during lookup merge -- investigate before proceeding"

unmatched_br = df["Banking Relationship"].isna().sum()
unmatched_gender = df["Gender"].isna().sum()
unmatched_ia = df["Investment Advisor"].isna().sum()
print(f"Step 3: joined lookup labels for Banking Relationship, Gender, Investment Advisor "
      f"(unmatched: {unmatched_br}, {unmatched_gender}, {unmatched_ia})")

# Now that we have readable labels, drop the raw numeric codes -- keeping both
# would be redundant since the label carries the same information.
df = df.drop(columns=["BRId", "GenderId", "IAId"])

# --- Step 4: rename columns to snake_case ------------------------------------
# Matches the naming convention already used elsewhere in this project
# (see clean/retail_sales_clean.csv) so all clean files are consistent.
rename_map = {
    "Client ID": "client_id",
    "Name": "name",
    "Age": "age",
    "Location ID": "location_id",
    "Joined Bank": "joined_bank_date",
    "Banking Contact": "banking_contact",
    "Nationality": "nationality",
    "Occupation": "occupation",
    "Fee Structure": "fee_structure",
    "Loyalty Classification": "loyalty_classification",
    "Estimated Income": "estimated_income",
    "Superannuation Savings": "superannuation_savings",
    "Amount of Credit Cards": "amount_of_credit_cards",
    "Credit Card Balance": "credit_card_balance",
    "Bank Loans": "bank_loans",
    "Bank Deposits": "bank_deposits",
    "Checking Accounts": "checking_accounts",
    "Saving Accounts": "saving_accounts",
    "Foreign Currency Account": "foreign_currency_account",
    "Business Lending": "business_lending",
    "Properties Owned": "properties_owned",
    "Risk Weighting": "risk_weighting",
    "Banking Relationship": "banking_relationship",
    "Gender": "gender",
    "Investment Advisor": "investment_advisor",
}
df = df.rename(columns=rename_map)
print(f"Step 4: renamed {len(rename_map)} columns to snake_case for consistency with the rest of the project")

after_count = len(df)

# --- Save the cleaned data to clean/, never touching the raw file ----------
os.makedirs("clean", exist_ok=True)
out_path = os.path.join("clean", "banking_data_clean.csv")
df.to_csv(out_path, index=False)

# --- Summary of every change made ------------------------------------------
print("\n=== SUMMARY ===")
print(f"Rows before cleaning: {before_count}")
print(f"Rows after cleaning:  {after_count}  (no rows were dropped -- see decisions at top of script)")
print(f"  - surrogate key added:               client_row_id")
print(f"  - 'joined_bank_date' parsed as date:  {unparsed} unparseable values")
print(f"  - lookup labels joined in:            banking_relationship, gender, investment_advisor")
print(f"  - columns renamed to snake_case:      {len(rename_map)}")
print(f"\nCleaned file written to: {out_path}")

print("\n=== PREVIEW (cleaned data) ===")
print(df.head())
print("\nShape:", df.shape)
print("\nDtypes:\n", df.dtypes)
