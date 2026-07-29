# Builds the 5 charts for the agreed business questions, from the CLEANED data
# (clean/banking_data_clean.csv). Read-only on the source data -- only writes
# new PNGs to charts/. Chart-type and color choices follow the project's
# dataviz standard (see comments on each chart for the reasoning).

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

df = pd.read_csv("clean/banking_data_clean.csv", parse_dates=["joined_bank_date"])
print("=== PREVIEW ===")
print(df.head())
print("\nShape:", df.shape)

os.makedirs("charts", exist_ok=True)

# --- Shared styling (matches charts already in this project) -----------------
GRID_COLOR = "#e1e0d9"
MUTED = "#898781"
plt.rcParams["font.family"] = "sans-serif"


def style_axes(ax):
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)


# 'Total relationship value' is a derived metric = the sum of every dollar
# figure the client represents to the bank (deposits, savings, checking,
# foreign currency, superannuation, business lending, loans, credit card
# balance). Used as a proxy for "how much this client is worth to the bank"
# in questions 1 and 5.
VALUE_COLS = [
    "bank_deposits", "saving_accounts", "checking_accounts",
    "foreign_currency_account", "superannuation_savings",
    "business_lending", "bank_loans", "credit_card_balance",
]
df["total_relationship_value"] = df[VALUE_COLS].sum(axis=1)


# =============================================================================
# Q1: Client value concentration
# "What share of total value comes from our top clients?"
# Chart: single-axis bar chart of each wealth quintile's share of total value,
# using an ORDINAL blue ramp (light -> dark = low -> high quintile). Chosen
# over a classic dual-axis Pareto chart (bars + cumulative line on a second
# y-scale) because this project avoids dual-axis charts -- a single %-share
# bar per quintile answers the same question on one scale and is easier to
# read at a glance.
# =============================================================================
df["value_quintile"] = pd.qcut(df["total_relationship_value"], 5,
                                labels=["Bottom 20%", "2nd", "3rd", "4th", "Top 20%"])
quintile_share = (
    df.groupby("value_quintile", observed=True)["total_relationship_value"].sum()
    / df["total_relationship_value"].sum() * 100
)
print("\n=== Q1: SHARE OF TOTAL VALUE BY WEALTH QUINTILE ===")
print(quintile_share.round(1))

ordinal_blues = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]  # steps 250/350/450/550/650
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(quintile_share.index.astype(str), quintile_share.values, color=ordinal_blues, width=0.6)
ax.set_title("Client Value Is Highly Concentrated in the Top Quintile", fontsize=13, fontweight="bold")
ax.set_xlabel("Clients Grouped by Total Relationship Value (Low to High)")
ax.set_ylabel("Share of Total Relationship Value (%)")
ax.yaxis.set_major_formatter(mticker.PercentFormatter())
style_axes(ax)
for bar, val in zip(bars, quintile_share.values):
    ax.annotate(f"{val:.0f}%", (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                textcoords="offset points", xytext=(0, 4), ha="center", fontsize=10, color="#0b0b0b")
plt.tight_layout()
plt.savefig("charts/q1_wealth_concentration.png", dpi=150)
plt.close(fig)
print("Saved: charts/q1_wealth_concentration.png")


# =============================================================================
# Q2: Risk drivers
# "Which client characteristics are most strongly associated with risk_weighting?"
# Chart: horizontal DIVERGING bar chart of correlation coefficients (each
# numeric column vs risk_weighting), sorted by strength. Diverging blue/red is
# the correct color job here because correlation has a sign (positive vs
# negative) -- a single hue would hide that polarity.
# =============================================================================
numeric_predictors = [
    "age", "estimated_income", "superannuation_savings", "amount_of_credit_cards",
    "credit_card_balance", "bank_loans", "bank_deposits", "checking_accounts",
    "saving_accounts", "foreign_currency_account", "business_lending", "properties_owned",
]
correlations = df[numeric_predictors + ["risk_weighting"]].corr()["risk_weighting"].drop("risk_weighting")
correlations = correlations.sort_values(key=abs)
print("\n=== Q2: CORRELATION OF EACH NUMERIC COLUMN WITH risk_weighting ===")
print(correlations.round(3))

colors = ["#2a78d6" if v >= 0 else "#e34948" for v in correlations.values]  # blue=positive, red=negative
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(correlations.index, correlations.values, color=colors, height=0.6)
ax.axvline(0, color=MUTED, linewidth=1)
ax.set_title("What's Associated with Higher Risk Weighting?", fontsize=13, fontweight="bold")
ax.set_xlabel("Correlation with Risk Weighting (negative ← → positive)")
style_axes(ax)
ax.grid(axis="x", color=GRID_COLOR, linewidth=0.8)
ax.grid(axis="y", visible=False)
plt.tight_layout()
plt.savefig("charts/q2_risk_drivers.png", dpi=150)
plt.close(fig)
print("Saved: charts/q2_risk_drivers.png")


# =============================================================================
# Q3: Product cross-sell gaps
# "Which segments hold the fewest products relative to their income?"
# Chart: single-axis bar chart of "products held per $100K of income" by
# loyalty tier -- this ratio collapses two measures (product count, income)
# into ONE meaningful magnitude, avoiding a dual-axis chart. The lowest bar
# (biggest gap) is highlighted in orange to flag the opportunity segment.
# =============================================================================
product_cols = ["bank_loans", "bank_deposits", "checking_accounts",
                 "saving_accounts", "foreign_currency_account", "business_lending"]
df["product_count"] = (df[product_cols] > 0).sum(axis=1)
df["products_per_100k_income"] = df["product_count"] / (df["estimated_income"] / 100_000)

tier_order = ["Jade", "Silver", "Gold", "Platinum"]
cross_sell = df.groupby("loyalty_classification", observed=True)["products_per_100k_income"].mean().reindex(tier_order)
print("\n=== Q3: AVG PRODUCTS HELD PER $100K INCOME, BY LOYALTY TIER ===")
print(cross_sell.round(2))

lowest_tier = cross_sell.idxmin()
bar_colors = ["#eb6834" if tier == lowest_tier else "#2a78d6" for tier in cross_sell.index]
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(cross_sell.index, cross_sell.values, color=bar_colors, width=0.5)
ax.set_title("Product Cross-Sell Gap by Loyalty Tier", fontsize=13, fontweight="bold")
ax.set_xlabel("Loyalty Classification")
ax.set_ylabel("Avg. Products Held per $100K of Income")
style_axes(ax)
ax.annotate(f"Lowest: {lowest_tier}\n(biggest cross-sell opportunity)",
            xy=(list(cross_sell.index).index(lowest_tier), cross_sell[lowest_tier]),
            xytext=(0, 20), textcoords="offset points", ha="center", fontsize=9, color="#52514e")
plt.tight_layout()
plt.savefig("charts/q3_cross_sell_gap.png", dpi=150)
plt.close(fig)
print("Saved: charts/q3_cross_sell_gap.png")


# =============================================================================
# Q4: Relationship-type economics
# "Do relationship types differ in value, and does fee structure line up?"
# Chart: grouped bar chart, banking_relationship on the x-axis, grouped by
# fee_structure. fee_structure (Low/Mid/High) is ORDINAL, not just categorical
# identity, so it uses the same single-hue ordinal ramp as Q1/Q5 (light->dark
# = Low->High) instead of 3 unrelated categorical hues.
# =============================================================================
fee_order = ["Low", "Mid", "High"]
rel_order = ["Retail", "Commercial", "Institutional", "Private Bank"]
grouped = (
    df.groupby(["banking_relationship", "fee_structure"], observed=True)["total_relationship_value"]
    .mean().unstack("fee_structure").reindex(index=rel_order, columns=fee_order)
)
print("\n=== Q4: AVG TOTAL RELATIONSHIP VALUE BY RELATIONSHIP TYPE x FEE STRUCTURE ===")
print(grouped.round(0))

fee_colors = {"Low": "#86b6ef", "Mid": "#2a78d6", "High": "#184f95"}  # ordinal ramp, steps 250/450/600
x = range(len(rel_order))
width = 0.25
fig, ax = plt.subplots(figsize=(9, 5.5))
for i, fee in enumerate(fee_order):
    offset = (i - 1) * width
    ax.bar([xi + offset for xi in x], grouped[fee].values, width=width,
           label=fee, color=fee_colors[fee])
ax.set_xticks(list(x))
ax.set_xticklabels(rel_order)
ax.set_title("Relationship Value by Banking Relationship Type & Fee Tier", fontsize=13, fontweight="bold")
ax.set_xlabel("Banking Relationship Type")
ax.set_ylabel("Avg. Total Relationship Value ($)")
style_axes(ax)
ax.legend(title="Fee Structure", frameon=False)
plt.tight_layout()
plt.savefig("charts/q4_relationship_fee_value.png", dpi=150)
plt.close(fig)
print("Saved: charts/q4_relationship_fee_value.png")


# =============================================================================
# Q5: Advisor book-of-business comparison
# "How much does client value vary across advisors?"
# Chart: horizontal ranked bar chart (22 advisors -- horizontal so all name
# labels stay readable), sorted descending, flat single hue since this is a
# magnitude ranking, not a categorical-identity comparison. Dashed reference
# line marks the overall average so over/under performers are obvious at a
# glance.
# =============================================================================
advisor_value = df.groupby("investment_advisor")["total_relationship_value"].mean().sort_values(ascending=False)
overall_avg = df["total_relationship_value"].mean()
print("\n=== Q5: AVG TOTAL RELATIONSHIP VALUE BY INVESTMENT ADVISOR ===")
print(advisor_value.round(0))
print("Overall average across all clients:", round(overall_avg, 0))

fig, ax = plt.subplots(figsize=(8, 9))
ax.barh(advisor_value.index[::-1], advisor_value.values[::-1], color="#2a78d6", height=0.6)
ax.axvline(overall_avg, color=MUTED, linewidth=1.2, linestyle="--")
ax.annotate(f"Overall avg: ${overall_avg:,.0f}", xy=(overall_avg, 0), xytext=(5, -25),
            textcoords="offset points", fontsize=9, color=MUTED)
ax.set_title("Average Client Value by Investment Advisor", fontsize=13, fontweight="bold")
ax.set_xlabel("Avg. Total Relationship Value ($)")
style_axes(ax)
ax.grid(axis="y", visible=False)
plt.tight_layout()
plt.savefig("charts/q5_advisor_performance.png", dpi=150)
plt.close(fig)
print("Saved: charts/q5_advisor_performance.png")
