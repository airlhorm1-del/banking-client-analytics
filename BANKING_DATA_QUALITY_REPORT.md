# Banking Client Data: Data Quality Report

**Dataset:** `banking_data.csv` → cleaned to `clean/banking_data_clean.csv`
**Grain:** 1 row = 1 bank client
**Rows:** 3,000 (unchanged by cleaning, no rows were dropped)
**Raw columns:** 25 → **Cleaned columns:** 26

All figures in this report are produced by scripts checked into this repository and can be independently re-run:
`banking_preview.py`, `banking_quality_report.py`, `banking_investigate_flags.py`, `banking_format_check.py`, `banking_cleaning.py`, `banking_extract_lookups.py`, `banking_summary_overview.py`

---

## 1. Completeness

| Check | Result |
|---|---|
| Missing values, any column | 0 (100% complete across all 25 raw columns) |

Source: `banking_quality_report.py`

---

## 2. Uniqueness

| Check | Result |
|---|---|
| Fully duplicated rows (all columns identical) | 0 |
| Rows sharing a `Client ID` with another row | 60, across 59 distinct IDs |

**Investigation (`banking_investigate_flags.py`):** every duplicated `Client ID` was checked. In each case the paired rows have different names, ages, join dates, and occupations. These are **distinct real clients whose ID happens to collide**, not the same person recorded twice.

**Resolution:** no rows were dropped. `Client ID` cannot be relied on as a unique key, so a surrogate key `client_row_id` (1–3,000, guaranteed unique) was added in `banking_cleaning.py`.

---

## 3. Validity

| Check | Result |
|---|---|
| Negative values, any numeric column | 0 |
| `age` outside 18–100 | 39 rows, all exactly age 17 |
| `joined_bank_date` unparseable | 0 |
| `joined_bank_date` in the future | 0 |
| `joined_bank_date` range | 1995-01-03 to 2021-12-31 |
| Zero balances (`bank_loans`, `bank_deposits`, `checking_accounts`, `saving_accounts`, `business_lending`) | 27 / 34 / 34 / 34 / 14 respectively |
| `properties_owned` = 0 | 705 rows |

**Investigation:** the 39 age-17 rows were checked individually: all are exactly 17, not implausible values like negative ages or triple digits. A 17-year-old can legitimately hold a bank account (e.g. youth/custodial account), so this was judged a too-strict assumed threshold, not a data error. Zero balances and zero properties owned are both plausible real states (a client simply may not hold that product / own property), not errors.

**Resolution:** no rows were dropped or modified for any of the above.

**Post-cleaning format audit (`banking_format_check.py`):**

| Column group | Result |
|---|---|
| `client_id` matching pattern `^IND\d+$` | 100% (0 mismatches) |
| Money columns (9) with more than 2 decimal places | 0 |
| Integer columns (6) with non-integer values | 0 |
| Text columns (9) with leading/trailing whitespace | 0 |

---

## 4. Consistency

Three columns (`BRId`, `GenderId`, `IAId`) were coded foreign keys with **no legend anywhere in the source file**.

**Investigation:** the accompanying `Banking Dashboard.pbix` (a Power BI template file provided alongside the CSV) was found to contain the original lookup tables in its data model. These were extracted (`banking_extract_lookups.py`) and joined onto the client data:

| Coded column | Resolved to | Values |
|---|---|---|
| `BRId` | `banking_relationship` | Retail, Institutional, Private Bank, Commercial |
| `GenderId` | `gender` | Male, Female |
| `IAId` | `investment_advisor` | 22 named advisors |

All three joins matched 100% of rows (0 unmatched). The raw numeric codes were dropped from the clean output in favor of the readable labels.

---

## 5. Accuracy

Not independently verifiable: no external source-of-truth system was available to check the data against. Values are used as provided.

---

## 6. Cleaning Actions Applied (`banking_cleaning.py`)

1. Added surrogate key `client_row_id` (see §2)
2. Parsed `Joined Bank` from ambiguous text (`dd-mm-yyyy`) to a true date type, renamed `joined_bank_date`, stored in unambiguous ISO format (`yyyy-mm-dd`)
3. Joined the 3 recovered lookup tables in place of the raw coded IDs (see §4)
4. Renamed all columns to `snake_case`, matching the convention used elsewhere in this repo

**Rows before cleaning: 3,000. Rows after cleaning: 3,000** (no rows dropped at any step)

---

## 7. Known Limitations

- `client_id` is not a reliable unique identifier in the source system. Always use `client_row_id` for anything requiring uniqueness.
- The dataset includes clients as young as 17; filter explicitly (`age >= 18`) if the intended analysis population is adults only.
- The precise meaning of `risk_weighting` (a 1–5 scale) is not documented anywhere in the source data or the accompanying dashboard, so values are used as provided, without an official definition.
- No transaction-level or time-series data exists, only a single join date per client. Trend/time-series analysis is not supported by this dataset as-is.
