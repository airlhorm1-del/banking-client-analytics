# Exports clean/banking_data_clean.csv to a formatted Excel workbook purely for
# easy visual inspection (sorting/filtering in Excel) -- no data is changed here,
# this just re-presents the already-cleaned data in a more readable format.

import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

df = pd.read_csv("clean/banking_data_clean.csv", parse_dates=["joined_bank_date"])

out_path = "clean/banking_data_clean_view.xlsx"
with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Banking Data", index=False)
    ws = writer.sheets["Banking Data"]

    # --- Style the header row: bold white text on a dark fill ---
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    # --- Freeze the header row so it stays visible while scrolling ---
    ws.freeze_panes = "A2"

    # --- Turn on Excel's built-in filter dropdowns for every column ---
    ws.auto_filter.ref = ws.dimensions

    # --- Auto-size each column to roughly fit its longest value ---
    for i, col in enumerate(df.columns, start=1):
        max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
        ws.column_dimensions[get_column_letter(i)].width = min(max_len, 40)

    # --- Apply currency formatting to the monetary columns ---
    money_cols = [
        "estimated_income", "superannuation_savings", "credit_card_balance",
        "bank_loans", "bank_deposits", "checking_accounts", "saving_accounts",
        "foreign_currency_account", "business_lending",
    ]
    for col in money_cols:
        col_idx = df.columns.get_loc(col) + 1
        letter = get_column_letter(col_idx)
        for row in range(2, ws.max_row + 1):
            ws[f"{letter}{row}"].number_format = "#,##0.00"

    # --- Apply a plain date format to the join-date column ---
    date_idx = df.columns.get_loc("joined_bank_date") + 1
    date_letter = get_column_letter(date_idx)
    for row in range(2, ws.max_row + 1):
        ws[f"{date_letter}{row}"].number_format = "yyyy-mm-dd"

print(f"Saved formatted view to: {out_path}")
print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
