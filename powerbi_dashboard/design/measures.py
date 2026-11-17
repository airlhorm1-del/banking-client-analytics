"""Generates the Overview redesign measures (HTML cards, gauge, pill colour) into banking_clients.tmdl,
plus the small 'Gauge Metric' table for the Risk / Products switch.

Re-runnable: it replaces only the measures listed in MEASURES (matched by name) and never touches others.
Usage: python measures.py <SemanticModel/definition folder>
"""
import re
import sys
import uuid
from pathlib import Path

DEF = Path(sys.argv[1])
TABLE = DEF / "tables" / "banking_clients.tmdl"
NS = uuid.UUID("6f1c2b0e-0d5a-4b7e-9f1e-5a0c3d2b1a99")
tag = lambda name: str(uuid.uuid5(NS, name))

FONT = "font-family:Plus Jakarta Sans,Segoe UI,sans-serif;"
INK, INK2, GREY, GREEN = "#17140F", "#2F2B26", "#6B665D", "#3F6B4B"
GOLD, GOLD_BAR, LIGHT_BAR, PALE = "#C9A45C", "#C4A66A", "#E5D6AF", "#E8D6AE"


def amt(v):
    """DAX text for 8.23bn / 963.28M / 171K style amounts."""
    return (f'IF({v} >= 1000000000, FORMAT({v} / 1000000000, "0.00") & "bn", '
            f'IF({v} >= 1000000, FORMAT({v} / 1000000, "0.00") & "M", '
            f'IF({v} >= 1000, FORMAT({v} / 1000, "0") & "K", FORMAT({v}, "0"))))')


def s(text):
    """DAX string literal."""
    return '"' + text.replace('"', '""') + '"'


def box(left, top, style, width=None):
    w = f"width:{width}px;" if width else ""
    return f"<div style='position:absolute;left:{left}px;top:{top}px;{w}{style}'>"


SEGMENT = ('VAR _segment = IF ( ISFILTERED ( banking_clients[banking_relationship] ), '
           'IF ( HASONEVALUE ( banking_clients[banking_relationship] ), '
           'VALUES ( banking_clients[banking_relationship] ) & " clients", "Selected clients" ), "All clients" )')

MEASURES = {}

# ---------------------------------------------------------------- header subtitle
MEASURES["Overview Subtitle HTML"] = f"""
-- Page subtitle, e.g. 3,000 clients · 4 relationship types (follows the client-type slicer)
VAR _n = [Total Clients]
VAR _types = DISTINCTCOUNT ( banking_clients[banking_relationship] )
RETURN
    {s(f"<div style='{FONT}font-size:12.5px;line-height:16px;color:#5E5A52;white-space:nowrap;'>")}
        & FORMAT ( _n, "#,0" ) & " clients · " & _types
        & IF ( _types = 1, " relationship type", " relationship types" ) & "</div>"
"""

# ---------------------------------------------------------------- KPI cards (322 x 111 each)
KPI_WRAP = f"<div style='position:relative;width:322px;height:111px;overflow:hidden;{FONT}color:{INK};'>"
KPI_LABEL = lambda text: box(19, 24, f"font-size:12.5px;line-height:16px;font-weight:500;color:{INK2};white-space:nowrap;") + text + "</div>"
KPI_VALUE = box(70, 57, "font-size:27px;line-height:34px;font-weight:700;letter-spacing:-0.3px;white-space:nowrap;")
KPI_NOTE = box(176, 60, f"font-size:11.5px;line-height:15px;font-weight:600;color:{GREEN};white-space:nowrap;")
TITLE = "font-size:16.5px;line-height:22px;font-weight:800;"
CAPTION = lambda left, top: box(left, top, f"font-size:9px;line-height:13px;color:{GREY};white-space:nowrap;")

MEASURES["KPI Value HTML"] = f"""
-- KPI card: total relationship value, share of the whole book, clients by year joined (6 bins)
VAR _v = [Total Relationship Value]
VAR _book = DIVIDE ( _v, CALCULATE ( [Total Relationship Value], ALL ( banking_clients ) ) )
VAR _bins =
    DATATABLE ( "Start", INTEGER, "End", INTEGER, "Order", INTEGER,
        {{ {{ 1995, 1999, 1 }}, {{ 2000, 2004, 2 }}, {{ 2005, 2009, 3 }}, {{ 2010, 2014, 4 }}, {{ 2015, 2019, 5 }}, {{ 2020, 2021, 6 }} }} )
VAR _counts =
    ADDCOLUMNS ( _bins, "@n",
        VAR _s = [Start]
        VAR _e = [End]
        RETURN CALCULATE ( [Total Clients],
            FILTER ( ALL ( banking_clients[joined_bank_date] ),
                YEAR ( banking_clients[joined_bank_date] ) >= _s && YEAR ( banking_clients[joined_bank_date] ) <= _e ) ) )
VAR _max = MAXX ( _counts, [@n] )
VAR _bars =
    CONCATENATEX ( _counts,
        VAR _h = ROUND ( DIVIDE ( [@n], _max ) * 42, 1 )
        RETURN "<rect x='" & FORMAT ( ( [Order] - 1 ) * 14, "0.0" ) & "' y='" & FORMAT ( 42 - _h, "0.0" )
            & "' width='10.5' height='" & FORMAT ( _h, "0.0" ) & "' rx='2' fill='"
            & IF ( [@n] = _max, "{GOLD_BAR}", "{LIGHT_BAR}" ) & "'/>",
        "", [Order], ASC )
RETURN
    {s(KPI_WRAP + KPI_LABEL("Total relationship value") + KPI_VALUE)} & {amt("_v")} & "</div>"
        & {s(KPI_NOTE)} & FORMAT ( COALESCE ( _book, 0 ), "0%" ) & " of<br>book</div>"
        & "<svg style='position:absolute;left:232px;top:23px;' width='81' height='42' viewBox='0 0 81 42'>" & _bars & "</svg>"
        & {s(CAPTION(232, 68) + "Clients by year<br>joined, 1995–2021</div></div>")}
"""

MEASURES["KPI Clients HTML"] = f"""
-- KPI card: client count, share in the Jade tier, clients per loyalty tier
VAR _n = [Total Clients]
VAR _jade = DIVIDE ( CALCULATE ( [Total Clients], banking_clients[loyalty_classification] = "Jade" ), _n )
VAR _tiers =
    DATATABLE ( "Tier", STRING, "Order", INTEGER, {{ {{ "Jade", 1 }}, {{ "Silver", 2 }}, {{ "Gold", 3 }}, {{ "Platinum", 4 }} }} )
VAR _counts =
    ADDCOLUMNS ( _tiers, "@n", VAR _t = [Tier] RETURN CALCULATE ( [Total Clients], banking_clients[loyalty_classification] = _t ) )
VAR _max = MAXX ( _counts, [@n] )
VAR _bars =
    CONCATENATEX ( _counts,
        VAR _h = ROUND ( DIVIDE ( [@n], _max ) * 42, 1 )
        RETURN "<rect x='" & FORMAT ( ( [Order] - 1 ) * 18, "0" ) & "' y='" & FORMAT ( 42 - _h, "0.0" )
            & "' width='12' height='" & FORMAT ( _h, "0.0" ) & "' rx='2' fill='"
            & IF ( [@n] = _max, "{GOLD_BAR}", "{LIGHT_BAR}" ) & "'/>",
        "", [Order], ASC )
RETURN
    {s(KPI_WRAP + KPI_LABEL("Clients") + KPI_VALUE)} & FORMAT ( _n, "#,0" ) & "</div>"
        & {s(KPI_NOTE)} & FORMAT ( COALESCE ( _jade, 0 ), "0%" ) & "<br>Jade</div>"
        & "<svg style='position:absolute;left:226px;top:24px;' width='66' height='42' viewBox='0 0 66 42'>" & _bars & "</svg>"
        & {s(CAPTION(214, 68) + "Jade · Silver · Gold ·<br>Plat.</div></div>")}
"""

MEASURES["KPI Risk HTML"] = f"""
-- KPI card: average risk weighting out of 5, clients at each risk level 1 to 5
VAR _avg = [Avg Risk Weighting]
VAR _levels = SELECTCOLUMNS ( GENERATESERIES ( 1, 5, 1 ), "Level", [Value] )
VAR _counts = ADDCOLUMNS ( _levels, "@n", VAR _l = [Level] RETURN CALCULATE ( [Total Clients], banking_clients[risk_weighting] = _l ) )
VAR _max = MAXX ( _counts, [@n] )
VAR _dots =
    CONCATENATEX ( _counts,
        "<circle cx='" & FORMAT ( 4 + ( [Level] - 1 ) * 23, "0" ) & "' cy='"
            & FORMAT ( 47.8 - DIVIDE ( [@n], _max ) * 36.8, "0.0" ) & "' r='3.4' fill='{GOLD_BAR}'/>",
        "", [Level], ASC )
RETURN
    {s(KPI_WRAP + KPI_LABEL("Average risk weighting") + KPI_VALUE)} & FORMAT ( _avg, "0.00" ) & "</div>"
        & {s(box(147, 67, f"font-size:11px;line-height:15px;font-weight:500;color:{GREY};white-space:nowrap;") + "of 5</div>")}
        & "<svg style='position:absolute;left:198px;top:26px;' width='100' height='52' viewBox='0 0 100 52'>" & _dots & "</svg>"
        & {s(CAPTION(200, 82) + "Clients at risk level 1 → 5</div></div>")}
"""

# ---------------------------------------------------------------- Client profile panel (322 x 266)
def mini(left, width, top_value, label_html):
    return (box(left, 102, "font-size:16px;line-height:20px;font-weight:700;text-align:center;", width) + top_value + "</div>"
            + box(left, 129, f"font-size:9.5px;line-height:13px;color:{GREY};text-align:center;", width) + label_html + "</div>")


MEASURES["Client Profile HTML"] = f"""
-- Client profile panel: averages per client and the top advisor by average client value
{SEGMENT}
VAR _rv = [Avg Relationship Value]
VAR _prod = [Avg Products Held]
VAR _inc = [Avg Estimated Income]
VAR _topRow = TOPN ( 1, VALUES ( banking_clients[investment_advisor] ), [Avg Relationship Value], DESC )
VAR _name = MAXX ( _topRow, banking_clients[investment_advisor] )
VAR _advN = CALCULATE ( [Total Clients], banking_clients[investment_advisor] = _name )
VAR _advAvg = CALCULATE ( [Avg Relationship Value], banking_clients[investment_advisor] = _name )
VAR _initials = LEFT ( _name, 1 ) & MID ( _name, FIND ( " ", _name, 1, 0 ) + 1, 1 )
RETURN
    {s(f"<div style='position:relative;width:322px;height:266px;{FONT}color:{INK};'>"
       + box(20, 18, TITLE) + "Client profile</div>"
       + box(19, 41, f"font-size:10.5px;line-height:14px;color:{GREY};white-space:nowrap;"))} & _segment & " · averages per client</div>"
        & {s(box(19, 102, "font-size:16px;line-height:20px;font-weight:700;text-align:center;", 89))} & {amt("_rv")} & "</div>"
        & {s(box(19, 129, f"font-size:9.5px;line-height:13px;color:{GREY};text-align:center;", 89) + "relationship<br>value</div>")}
        & {s(box(117, 102, "font-size:16px;line-height:20px;font-weight:700;text-align:center;", 88))} & FORMAT ( _prod, "0.0" ) & "</div>"
        & {s(box(117, 129, f"font-size:9.5px;line-height:13px;color:{GREY};text-align:center;", 88) + "products held</div>")}
        & {s(box(214, 102, "font-size:16px;line-height:20px;font-weight:700;text-align:center;", 89))} & {amt("_inc")} & "</div>"
        & {s(box(214, 129, f"font-size:9.5px;line-height:13px;color:{GREY};text-align:center;", 89) + "estimated<br>income</div>")}
        & {s(box(19, 180, f"font-size:11.5px;line-height:16px;font-weight:600;color:{INK2};white-space:nowrap;") + "Top advisor by client value</div>")}
        & {s(box(19, 209, f"width:40px;font-size:12px;line-height:40px;font-weight:700;color:{PALE};text-align:center;"))} & _initials & "</div>"
        & {s(box(70, 211, "font-size:13.5px;line-height:18px;font-weight:600;white-space:nowrap;"))} & _name & "</div>"
        & {s(box(70, 231, f"font-size:10.5px;line-height:14px;color:{GREY};white-space:nowrap;"))}
        & FORMAT ( _advN, "#,0" ) & " clients · avg " & {amt("_advAvg")} & " each</div></div>"
"""

# ---------------------------------------------------------------- Gold card headline (322 x 180)
MEASURES["Wealth Headline HTML"] = f"""
-- Top of the gold card: share of value held by the top 20% (within the current selection) and how many times the bottom 20%
{SEGMENT}
VAR _all = CALCULATE ( [Total Relationship Value], REMOVEFILTERS ( banking_clients[value_quintile] ) )
VAR _top = CALCULATE ( [Total Relationship Value], banking_clients[value_quintile] = "Top 20%" )
VAR _bottom = CALCULATE ( [Total Relationship Value], banking_clients[value_quintile] = "Bottom 20%" )
VAR _share = COALESCE ( DIVIDE ( _top, _all ), 0 )
VAR _ratio = DIVIDE ( _top, _bottom )
VAR _sentence =
    IF ( ISFILTERED ( banking_clients[banking_relationship] ),
        "of " & _segment & "' relationship value sits with clients in the bank-wide top 20%",
        "of all relationship value sits with the top 20% of clients" )
RETURN
    {s(f"<div style='position:relative;width:322px;height:180px;{FONT}color:{INK};'>"
       + box(19, 20, "font-size:10.5px;line-height:14px;font-weight:700;letter-spacing:1.6px;white-space:nowrap;") + "WEALTH CONCENTRATION</div>"
       + box(17, 41, "font-size:40px;line-height:46px;font-weight:800;letter-spacing:-0.4px;white-space:nowrap;"))}
        & FORMAT ( _share, "0.0%" ) & "</div>"
        & {s(box(19, 93, f"font-size:11.5px;line-height:15px;font-weight:500;color:{INK};", 280))} & _sentence & "</div>"
        & {s(box(19, 136, "height:6px;border-radius:3px;background:rgba(255,255,255,0.38);overflow:hidden;", 282)
             + "<div style='height:6px;border-radius:3px;background:#FFFFFF;width:")} & FORMAT ( _share * 282, "0" ) & "px;'></div></div>"
        & {s(box(19, 152, "display:flex;justify-content:space-between;font-size:10.5px;line-height:14px;font-weight:600;", 282)
             + "<span>Top 20%</span><span>")}
        & IF ( ISBLANK ( _ratio ), "", FORMAT ( _ratio, "0.0" ) & "× the bottom 20%" ) & "</span></div></div>"
"""

# ---------------------------------------------------------------- Product book panel (322 x 258)
MEASURES["Product Book HTML"] = f"""
-- Product book panel: total balances per product, bar length relative to the largest product
VAR _rows =
    DATATABLE ( "Label", STRING, "Order", INTEGER,
        {{ {{ "Deposits", 1 }}, {{ "Business lending", 2 }}, {{ "Loans", 3 }}, {{ "Checking", 4 }},
           {{ "Savings", 5 }}, {{ "Foreign currency", 6 }}, {{ "Superannuation", 7 }}, {{ "Credit cards", 8 }} }} )
VAR _vals =
    ADDCOLUMNS ( _rows, "@v",
        SWITCH ( [Order],
            1, SUM ( banking_clients[bank_deposits] ), 2, SUM ( banking_clients[business_lending] ),
            3, SUM ( banking_clients[bank_loans] ), 4, SUM ( banking_clients[checking_accounts] ),
            5, SUM ( banking_clients[saving_accounts] ), 6, SUM ( banking_clients[foreign_currency_account] ),
            7, SUM ( banking_clients[superannuation_savings] ), 8, SUM ( banking_clients[credit_card_balance] ) ) )
VAR _max = MAXX ( _vals, [@v] )
VAR _list =
    CONCATENATEX ( _vals,
        VAR _top = 50 + ( [Order] - 1 ) * 25
        VAR _v = [@v]
        VAR _w = MAX ( 3, ROUND ( DIVIDE ( _v, _max ) * 102, 0 ) )
        RETURN
            "<div style='position:absolute;left:20px;top:" & _top & "px;font-size:11.5px;line-height:16px;color:{INK2};white-space:nowrap;'>" & [Label] & "</div>"
            & "<div style='position:absolute;left:135px;top:" & ( _top + 3.5 ) & "px;width:102px;height:9px;border-radius:4.5px;background:#FFFFFF;overflow:hidden;'>"
            & "<div style='height:9px;border-radius:4.5px;width:" & _w & "px;background:" & IF ( _v >= _max * 0.5, "{INK}", "{GOLD_BAR}" ) & ";'></div></div>"
            & "<div style='position:absolute;right:21px;top:" & _top & "px;font-size:11.5px;line-height:16px;font-weight:700;white-space:nowrap;'>"
            & {amt("_v")} & "</div>",
        "", [Order], ASC )
RETURN
    {s(f"<div style='position:relative;width:322px;height:258px;{FONT}color:{INK};'>"
       + box(20, 17, TITLE) + "Product book</div>"
       + "<div style='position:absolute;right:21px;top:23px;font-size:10.5px;line-height:14px;color:" + GREY + ";'>Total balances</div>")}
        & _list & "</div>"
"""

# ---------------------------------------------------------------- What drives risk panel (322 x 658)
DRIVERS = [("income", "Income", "estimated_income"), ("super", "Superannuation", "superannuation_savings"),
           ("loans", "Loans", "bank_loans"), ("business", "Business lending", "business_lending"),
           ("fx", "Foreign currency", "foreign_currency_account"), ("cards", "Credit card balance", "credit_card_balance"),
           ("checking", "Checking", "checking_accounts"), ("property", "Properties owned", "properties_owned"),
           ("age", "Age", "age")]
X_SWITCH = "SWITCH ( _k, " + ", ".join(f'"{k}", banking_clients[{c}]' for k, _, c in DRIVERS) + " )"
DRIVER_ROWS = ", ".join(f'{{ "{k}", "{lab}" }}' for k, lab, _ in DRIVERS)

MEASURES["Risk Drivers HTML"] = f"""
-- What drives risk panel: Pearson correlation of each client attribute with risk weighting,
-- recalculated for the current selection, sorted strongest first, plus the key finding box.
{SEGMENT}
VAR _ybar = AVERAGE ( banking_clients[risk_weighting] )
VAR _syy = SUMX ( banking_clients, ( banking_clients[risk_weighting] - _ybar ) ^ 2 )
VAR _drivers = DATATABLE ( "Key", STRING, "Label", STRING, {{ {DRIVER_ROWS} }} )
VAR _withR =
    ADDCOLUMNS ( _drivers, "@r",
        VAR _k = [Key]
        VAR _xbar = AVERAGEX ( banking_clients, {X_SWITCH} )
        VAR _sxy = SUMX ( banking_clients, ( {X_SWITCH} - _xbar ) * ( banking_clients[risk_weighting] - _ybar ) )
        VAR _sxx = SUMX ( banking_clients, ( {X_SWITCH} - _xbar ) ^ 2 )
        RETURN DIVIDE ( _sxy, SQRT ( _sxx * _syy ) ) )
VAR _ranked = ADDCOLUMNS ( _withR, "@rank", RANKX ( _withR, [@r], , DESC, DENSE ) )
VAR _fmt = "0.00"
VAR _rows =
    CONCATENATEX ( _ranked,
        VAR _r = [@r]
        VAR _top = 105 + ( [@rank] - 1 ) * 37.5
        VAR _w = MIN ( 282, MAX ( 4, ROUND ( DIVIDE ( MAX ( _r, 0 ), 0.75 ) * 282, 0 ) ) )
        VAR _txt = IF ( ABS ( _r ) < 0.005, "0.00", FORMAT ( _r, _fmt ) )
        RETURN
            "<div style='position:absolute;left:19px;top:" & _top & "px;font-size:11.5px;line-height:15px;color:{INK2};white-space:nowrap;'>" & [Label] & "</div>"
            & "<div style='position:absolute;right:21px;top:" & _top & "px;font-size:11.5px;line-height:15px;font-weight:700;'>" & _txt & "</div>"
            & "<div style='position:absolute;left:19px;top:" & ( _top + 17.5 ) & "px;width:282px;height:7px;border-radius:3.5px;background:#FFFFFF;overflow:hidden;'>"
            & "<div style='height:7px;border-radius:3.5px;width:" & _w & "px;background:" & IF ( _r >= 0.45, "{INK}", "{GOLD_BAR}" ) & ";'></div></div>",
        "", [@rank], ASC )
VAR _rIncome = MAXX ( FILTER ( _withR, [Key] = "income" ), [@r] )
VAR _rAge = MAXX ( FILTER ( _withR, [Key] = "age" ), [@r] )
VAR _ageTxt = IF ( ABS ( _rAge ) < 0.005, "0.00", FORMAT ( _rAge, _fmt ) )
RETURN
    {s(f"<div style='position:relative;width:322px;height:658px;{FONT}color:{INK};'>"
       + box(19, 18, TITLE) + "What drives risk</div>"
       + box(220, 22, "font-size:10.5px;line-height:15px;font-weight:700;text-align:center;", 82) + "Correlation r</div>"
       + box(19, 56, "font-size:11.5px;line-height:17px;color:#4A463F;", 275)
       + "How strongly each client attribute moves with risk weighting.</div>")}
        & _rows
        & {s(box(36, 549, "font-size:9.5px;line-height:13px;font-weight:700;letter-spacing:1.2px;color:#DCC994;white-space:nowrap;") + "KEY FINDING</div>"
             + box(36, 568, "font-size:13.5px;line-height:19px;font-weight:600;color:#FFFFFF;", 252)
             + "Risk tracks wealth, not age or property count.</div>"
             + box(36, 611, "font-size:10.5px;line-height:14px;color:#D9D4CB;white-space:nowrap;"))}
        & "Income r = " & FORMAT ( _rIncome, _fmt ) & ", age r = " & _ageTxt & " for "
        & IF ( _segment = "All clients", "all clients", _segment ) & ".</div></div>"
"""

# ================================================================ Wealth & Cross-sell page
KPI_NOTE_GREY = box(160, 60, f"font-size:11px;line-height:15px;font-weight:600;color:{GREY};white-space:nowrap;")
KPI_NOTE_AT = lambda left: box(left, 60, f"font-size:11px;line-height:15px;font-weight:600;color:{GREEN};white-space:nowrap;")
TIERS = 'DATATABLE ( "Tier", STRING, "Order", INTEGER, { { "Jade", 1 }, { "Silver", 2 }, { "Gold", 3 }, { "Platinum", 4 } } )'
QUINTILES = ('DATATABLE ( "Quintile", STRING, "Label", STRING, "Order", INTEGER, { { "Top 20%", "Top 20%", 1 }, '
             '{ "4th", "4th", 2 }, { "3rd", "3rd", 3 }, { "2nd", "2nd", 4 }, { "Bottom 20%", "Bottom 20%", 5 } } )')
SVG_FONT = "font-family='Plus Jakarta Sans, Segoe UI, sans-serif'"


def mini_bars(table_var, n_bars, width, step, height=42, order_col="[Order]"):
    """DAX CONCATENATEX that draws small columns (tallest one highlighted) from a table with [@n]."""
    return f"""CONCATENATEX ( {table_var},
        VAR _h = ROUND ( DIVIDE ( [@n], _max ) * {height}, 1 )
        RETURN "<rect x='" & FORMAT ( ( {order_col} - 1 ) * {step}, "0.0" ) & "' y='" & FORMAT ( {height} - _h, "0.0" )
            & "' width='{width}' height='" & FORMAT ( _h, "0.0" ) & "' rx='2' fill='"
            & IF ( [@n] = _max, "{GOLD_BAR}", "{LIGHT_BAR}" ) & "'/>",
        "", {order_col}, ASC )"""


MEASURES["Wealth Subtitle HTML"] = f"""
-- Wealth page subtitle (follows the client-type pills)
{s(f"<div style='{FONT}font-size:12.5px;line-height:16px;color:#5E5A52;white-space:nowrap;'>")}
    & FORMAT ( [Total Clients], "#,0" ) & " clients · where value sits and how deep cross-sell goes</div>"
"""

MEASURES["Wealth KPI Value HTML"] = f"""
-- KPI card: average relationship value, the median, and the average per loyalty tier
VAR _avg = [Avg Relationship Value]
VAR _median = MEDIAN ( banking_clients[total_relationship_value] )
VAR _vals = ADDCOLUMNS ( {TIERS}, "@n", VAR _t = [Tier] RETURN CALCULATE ( [Avg Relationship Value], banking_clients[loyalty_classification] = _t ) )
VAR _max = MAXX ( _vals, [@n] )
VAR _bars = {mini_bars("_vals", 4, 12, 18)}
RETURN
    {s(KPI_WRAP + KPI_LABEL("Average relationship value") + KPI_VALUE)} & {amt("_avg")} & "</div>"
        & {s(KPI_NOTE_GREY)} & "median<br>" & {amt("_median")} & "</div>"
        & "<svg style='position:absolute;left:236px;top:24px;' width='66' height='42' viewBox='0 0 66 42'>" & _bars & "</svg>"
        & {s(CAPTION(236, 68) + "Avg value by tier,<br>Jade → Platinum</div></div>")}
"""

MEASURES["Wealth KPI Top Share HTML"] = f"""
-- KPI card: share of value held by the top 20%, how many times the bottom 20%, share per quintile
VAR _all = CALCULATE ( [Total Relationship Value], REMOVEFILTERS ( banking_clients[value_quintile] ) )
VAR _vals = ADDCOLUMNS ( {QUINTILES}, "@n", VAR _q = [Quintile] RETURN DIVIDE ( CALCULATE ( [Total Relationship Value], banking_clients[value_quintile] = _q ), _all ) )
VAR _max = MAXX ( _vals, [@n] )
VAR _top = MAXX ( FILTER ( _vals, [Order] = 1 ), [@n] )
VAR _bottom = MAXX ( FILTER ( _vals, [Order] = 5 ), [@n] )
VAR _bars = {mini_bars("_vals", 5, 11, 15.5)}
RETURN
    {s(KPI_WRAP + KPI_LABEL("Top 20% share of value") + KPI_VALUE)} & FORMAT ( COALESCE ( _top, 0 ), "0.0%" ) & "</div>"
        & {s(KPI_NOTE_AT(166))} & IF ( ISBLANK ( _bottom ), "", FORMAT ( DIVIDE ( _top, _bottom ), "0.0" ) & "×<br>bottom 20%" ) & "</div>"
        & "<svg style='position:absolute;left:244px;top:24px;' width='73' height='42' viewBox='0 0 73 42'>" & _bars & "</svg>"
        & {s(CAPTION(244, 68) + "Share by<br>quintile</div></div>")}
"""

MEASURES["Wealth KPI Products HTML"] = f"""
-- KPI card: average products held, share holding all 6, clients by number of products held
VAR _avg = [Avg Products Held]
VAR _all6 = [Clients With All 6 Products %]
VAR _vals = ADDCOLUMNS ( SELECTCOLUMNS ( GENERATESERIES ( 1, 6, 1 ), "Order", [Value] ), "@n",
    VAR _p = [Order] RETURN CALCULATE ( [Total Clients], banking_clients[product_count] = _p ) )
VAR _max = MAXX ( _vals, [@n] )
VAR _bars = {mini_bars("_vals", 6, 9, 12.5)}
RETURN
    {s(KPI_WRAP + KPI_LABEL("Average products held") + KPI_VALUE)} & FORMAT ( _avg, "0.00" ) & "</div>"
        & {s(KPI_NOTE_AT(166))} & FORMAT ( COALESCE ( _all6, 0 ), "0.0%" ) & "<br>hold all 6</div>"
        & "<svg style='position:absolute;left:244px;top:24px;' width='72' height='42' viewBox='0 0 72 42'>" & _bars & "</svg>"
        & {s(CAPTION(244, 68) + "Clients by<br>products, 1 → 6</div></div>")}
"""

MEASURES["Value By Quintile HTML"] = f"""
-- Left top panel: share of relationship value per client quintile, as columns (top 20% in black)
VAR _all = CALCULATE ( [Total Relationship Value], REMOVEFILTERS ( banking_clients[value_quintile] ) )
VAR _vals = ADDCOLUMNS ( {QUINTILES}, "@n", VAR _q = [Quintile] RETURN DIVIDE ( CALCULATE ( [Total Relationship Value], banking_clients[value_quintile] = _q ), _all ) )
VAR _max = MAXX ( _vals, [@n] )
VAR _top = MAXX ( FILTER ( _vals, [Order] = 1 ), [@n] )
VAR _bottom = MAXX ( FILTER ( _vals, [Order] = 5 ), [@n] )
VAR _cols =
    CONCATENATEX ( _vals,
        VAR _x = 4 + ( [Order] - 1 ) * 94
        VAR _h = ROUND ( DIVIDE ( [@n], _max ) * 160, 1 )
        RETURN
            "<rect x='" & _x & "' y='" & FORMAT ( 196 - _h, "0.0" ) & "' width='56' height='" & FORMAT ( _h, "0.0" )
                & "' rx='7' fill='" & IF ( [Order] = 1, "{INK}", "{GOLD_BAR}" ) & "'/>"
            & "<text x='" & ( _x + 28 ) & "' y='" & FORMAT ( 196 - _h - 9, "0.0" ) & "' text-anchor='middle' {SVG_FONT} font-size='12.5' font-weight='700' fill='{INK}'>"
                & FORMAT ( COALESCE ( [@n], 0 ), "0.0%" ) & "</text>"
            & "<text x='" & ( _x + 28 ) & "' y='218' text-anchor='middle' {SVG_FONT} font-size='11' fill='{INK2}'>" & [Label] & "</text>",
        "", [Order], ASC )
RETURN
    {s(f"<div style='position:relative;width:490px;height:350px;{FONT}color:{INK};'>"
       + box(20, 18, TITLE) + "Where the value sits</div>"
       + box(20, 41, f"font-size:10.5px;line-height:14px;color:{GREY};white-space:nowrap;") + "Share of total relationship value by client quintile</div>"
       + "<div style='position:absolute;right:20px;top:20px;padding:0 12px;height:25px;line-height:25px;border-radius:12.5px;background:#FFFFFF;font-size:10.5px;font-weight:700;white-space:nowrap;'>Top 20% = ")}
        & IF ( ISBLANK ( _bottom ), "–", FORMAT ( DIVIDE ( _top, _bottom ), "0.0" ) ) & "× bottom 20%</div>"
        & "<svg style='position:absolute;left:20px;top:78px;' width='450' height='230' viewBox='0 0 450 230'>"
        & "<line x1='0' y1='196.5' x2='450' y2='196.5' stroke='#E2DCD0' stroke-width='1'/>" & _cols & "</svg>"
        & {s(box(20, 318, f"font-size:10px;line-height:14px;color:{GREY};white-space:nowrap;") + "Quintiles rank all 3,000 clients by relationship value, so each fifth is 600 clients.</div></div>")}
"""

MEASURES["Tier Value HTML"] = f"""
-- Gold panel: average relationship value per loyalty tier; the title checks the data before claiming it
VAR _vals = ADDCOLUMNS ( {TIERS}, "@n", VAR _t = [Tier] RETURN CALCULATE ( [Avg Relationship Value], banking_clients[loyalty_classification] = _t ) )
VAR _max = MAXX ( _vals, [@n] )
VAR _plat = MAXX ( FILTER ( _vals, [Tier] = "Platinum" ), [@n] )
VAR _jade = MAXX ( FILTER ( _vals, [Tier] = "Jade" ), [@n] )
VAR _bestOther = MAXX ( FILTER ( _vals, [Tier] <> "Platinum" ), [@n] )
VAR _title = IF ( _plat <= _bestOther, "Higher tiers don't hold more value", "Platinum clients hold the most value" )
VAR _rows =
    CONCATENATEX ( _vals,
        VAR _top = 152 + ( [Order] - 1 ) * 44
        VAR _w = ROUND ( DIVIDE ( [@n], _max ) * 230, 0 )
        RETURN
            "<div style='position:absolute;left:19px;top:" & _top & "px;width:452px;height:34px;border-radius:13px;background:#FFFFFF;'>"
            & "<div style='position:absolute;left:16px;top:9px;font-size:12px;line-height:16px;font-weight:600;'>" & [Tier] & "</div>"
            & "<div style='position:absolute;left:110px;top:13px;width:230px;height:8px;border-radius:4px;background:#EFE9DD;overflow:hidden;'>"
            & "<div style='height:8px;border-radius:4px;background:{INK};width:" & _w & "px;'></div></div>"
            & "<div style='position:absolute;right:16px;top:9px;font-size:12px;line-height:16px;font-weight:700;'>" & {amt("[@n]")} & "</div></div>",
        "", [Order], ASC )
RETURN
    {s(f"<div style='position:relative;width:490px;height:350px;{FONT}color:{INK};'>"
       + box(19, 20, "font-size:10.5px;line-height:14px;font-weight:700;letter-spacing:1.6px;white-space:nowrap;") + "LOYALTY TIERS</div>"
       + box(19, 42, "", 445) + "<div style='font-size:21px;line-height:26px;font-weight:800;'>")} & _title & "</div>"
        & "<div style='margin-top:8px;font-size:11.5px;line-height:15px;font-weight:500;'>Average relationship value per client. Platinum clients average "
        & {amt("_plat")} & ", Jade clients " & {amt("_jade")} & ".</div></div>"
        & _rows & "</div>"
"""

MEASURES["Tier Depth HTML"] = f"""
-- Left bottom panel: cross-sell depth per loyalty tier (products per 100K income, average products, share holding all 6)
VAR _vals =
    ADDCOLUMNS ( {TIERS},
        "@p100", VAR _t = [Tier] RETURN CALCULATE ( [Avg Products per 100K Income], banking_clients[loyalty_classification] = _t ),
        "@prod", VAR _t = [Tier] RETURN CALCULATE ( [Avg Products Held], banking_clients[loyalty_classification] = _t ),
        "@all6", VAR _t = [Tier] RETURN CALCULATE ( [Clients With All 6 Products %], banking_clients[loyalty_classification] = _t ) )
VAR _cards =
    CONCATENATEX ( _vals,
        VAR _left = 20 + ( [Order] - 1 ) * 115
        RETURN
            "<div style='position:absolute;left:" & _left & "px;top:74px;width:103px;height:150px;border-radius:12px;background:#FFFFFF;text-align:center;'>"
            & "<div style='margin-top:16px;font-size:12px;line-height:16px;font-weight:700;'>" & [Tier] & "</div>"
            & "<div style='margin-top:10px;font-size:25px;line-height:30px;font-weight:800;'>" & FORMAT ( [@p100], "0.00" ) & "</div>"
            & "<div style='font-size:9.5px;line-height:13px;color:{GREY};'>products per<br>100K income</div>"
            & "<div style='margin:10px auto 0;width:60px;height:1px;background:#EAE4D8;'></div>"
            & "<div style='margin-top:9px;font-size:10px;line-height:14px;color:{INK2};'>avg " & FORMAT ( [@prod], "0.00" ) & " products</div>"
            & "<div style='font-size:10px;line-height:14px;color:{GREY};'>" & FORMAT ( COALESCE ( [@all6], 0 ), "0.0%" ) & " hold all 6</div></div>",
        "", [Order], ASC )
RETURN
    {s(f"<div style='position:relative;width:490px;height:292px;{FONT}color:{INK};'>"
       + box(20, 18, TITLE) + "Cross-sell depth by tier</div>"
       + box(20, 41, f"font-size:10.5px;line-height:14px;color:{GREY};white-space:nowrap;") + "Products held per 100K of estimated income, by loyalty tier</div>")}
        & _cards
        & {s(box(20, 240, f"font-size:10.5px;line-height:15px;color:#4A463F;", 450)
             + "Every tier holds close to 6 products, so cross-sell depth barely changes from tier to tier.</div></div>")}
"""

MEASURES["Wealth Finding HTML"] = f"""
-- Dark panel: key finding with live numbers for the current selection
{SEGMENT}
VAR _all = CALCULATE ( [Total Relationship Value], REMOVEFILTERS ( banking_clients[value_quintile] ) )
VAR _top = DIVIDE ( CALCULATE ( [Total Relationship Value], banking_clients[value_quintile] = "Top 20%" ), _all )
VAR _all6 = [Clients With All 6 Products %]
RETURN
    {s(f"<div style='position:relative;width:490px;height:292px;{FONT}color:#FFFFFF;'>"
       + box(24, 24, "font-size:9.5px;line-height:13px;font-weight:700;letter-spacing:1.2px;color:#DCC994;white-space:nowrap;") + "KEY FINDING</div>"
       + box(24, 44, "font-size:21px;line-height:27px;font-weight:700;", 440) + "Value is concentrated,<br>cross-sell is not the gap.</div>"
       + box(24, 112, "font-size:34px;line-height:40px;font-weight:800;color:#D9BC7E;"))}
        & FORMAT ( COALESCE ( _all6, 0 ), "0.0%" ) & "</div>"
        & {s(box(24, 156, "font-size:11px;line-height:15px;color:#D9D4CB;", 190) + "of clients already hold all 6 products</div>"
             + box(254, 112, "font-size:34px;line-height:40px;font-weight:800;color:#D9BC7E;"))}
        & FORMAT ( COALESCE ( _top, 0 ), "0.0%" ) & "</div>"
        & {s(box(254, 156, "font-size:11px;line-height:15px;color:#D9D4CB;", 200) + "of relationship value sits with the top 20% of clients</div>"
             + box(24, 248, "font-size:10px;line-height:14px;color:#A8A196;white-space:nowrap;") + "Based on ")}
        & FORMAT ( [Total Clients], "#,0" ) & " clients" & IF ( _segment = "All clients", "", " · " & _segment ) & ".</div></div>"
"""

# Earlier helpers from this phase that the Deneb switch and pills made unnecessary (removed if present)
RETIRED = ["Gauge Value", "Gauge Min", "Gauge Max", "Gauge Label", "Gauge Caption", "All Clients Pill Fill"]


# ---------------------------------------------------------------- write TMDL
def tmdl_measure(name, dax):
    lines = [l.rstrip() for l in dax.strip("\n").splitlines()]
    body = "\n".join("\t\t\t" + l if l.strip() else "" for l in lines)
    body = re.sub(r"\n{2,}", "\n", body)  # TMDL expressions must not contain blank lines
    return f"\tmeasure '{name}' =\n{body}\n\t\tlineageTag: {tag(name)}\n"


text = TABLE.read_text(encoding="utf-8")
for name in list(MEASURES) + RETIRED:  # drop previous versions of our generated measures only
    pattern = re.compile(rf"\tmeasure '{re.escape(name)}' =.*?\n(?=\t(?:measure|column|partition|hierarchy|annotation) |\Z)", re.S)
    text = pattern.sub("", text)
anchor = "\tmeasure 'Quintile List HTML' ="
end = text.index("\n\tcolumn ", text.index(anchor))  # insert after the last measure block
block = "".join("\n" + tmdl_measure(n, d) for n, d in MEASURES.items())
text = text[:end].rstrip("\n") + "\n" + block + text[end:]
TABLE.write_text(text, encoding="utf-8")
print(f"wrote {len(MEASURES)} measures into {TABLE.name}")

# The 'Gauge Metric' helper table from earlier in this phase is no longer needed: the Risk / Products
# switch now lives inside the Deneb gauge. Remove it if present.
(DEF / "tables" / "Gauge Metric.tmdl").unlink(missing_ok=True)
model = DEF / "model.tmdl"
m = model.read_text(encoding="utf-8")
if "ref table 'Gauge Metric'" in m:
    model.write_text(m.replace("ref table 'Gauge Metric'\n", ""), encoding="utf-8")
print("Gauge Metric helper table removed")
