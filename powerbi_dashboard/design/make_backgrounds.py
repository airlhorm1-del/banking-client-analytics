"""Draws the 4 page backgrounds at the target picture's shape (1280 x 1008).

Shapes and icons only, no text: every word and number stays a real Power BI object.
Positions come from measuring target_design.png (shifted by -2, -1 to fit 1280 wide).
Output: <out_dir>/bg_01_overview.png ... bg_04_risk.png at 2x (2560 x 2016).

Usage: python make_backgrounds.py <out_dir> <chrome.exe>
"""
import subprocess
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
CHROME = sys.argv[2]
W, H = 1280, 1008

# Palette (sampled from the kit backgrounds)
OUTER_A, OUTER_B = "#E9E3D7", "#E7E1D5"
WHITE, PANEL, DARK = "#FFFFFF", "#F6F4EF", "#17140F"
GOLD, GOLD_ICON = "#C9A45C", "#B08A3E"
GOLD_GRAD = "linear-gradient(135deg, #D8BA7C 0%, #C49D52 55%, #B18B3F 100%)"
DIVIDER = "#EEEAE2"

# --- Icons: 24x24 outline paths (thin, rounded, same style as the kit) -------------
ICONS = {
    "landmark": '<path d="M3 9.5 12 4l9 5.5"/><path d="M6 12v6M10 12v6M14 12v6M18 12v6"/><path d="M3 21h18"/>',
    "house": '<path d="M4 10.5 12 4l8 6.5V20H4z"/>',
    "chart": '<path d="M3 20h18"/><path d="M7 20v-8M12 20V7M17 20v-5"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20v-1.5A4.5 4.5 0 0 1 7 14h4a4.5 4.5 0 0 1 4.5 4.5V20"/>'
             '<circle cx="17.5" cy="9" r="2.5"/><path d="M18 14h.5a3.5 3.5 0 0 1 3.5 3.5V20"/>',
    "shield": '<path d="M12 3 5 6v5.5c0 4.4 3 7.9 7 9.5 4-1.6 7-5.1 7-9.5V6z"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4.5 21v-1.5A5.5 5.5 0 0 1 10 14h4a5.5 5.5 0 0 1 5.5 5.5V21"/>',
    "download": '<path d="M12 4v11"/><path d="m7 10 5 5 5-5"/><path d="M5 20h14"/>',
    "filter": '<path d="M3.5 4.5h17l-6.5 8v6.5l-4 2v-8.5z"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20.5 20.5-4.5-4.5"/>',
    "chevron": '<path d="m9 6 6 6-6 6"/>',
    "arrow": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "coin": '<circle cx="12" cy="12" r="9"/><path d="M15 9h-4.5a1.75 1.75 0 0 0 0 3.5h3a1.75 1.75 0 0 1 0 3.5H9"/><path d="M12 7v10"/>',
    "grid": '<rect x="4" y="4" width="6.5" height="6.5" rx="1.2"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.2"/>'
            '<rect x="4" y="13.5" width="6.5" height="6.5" rx="1.2"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.2"/>',
    "trend": '<path d="m3 17 6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "pie": '<path d="M12 3a9 9 0 1 0 9 9h-9z"/><path d="M15 3.5A9 9 0 0 1 20.5 9H15z"/>',
    "alert": '<path d="M12 4 2.8 19.5a1 1 0 0 0 .9 1.5h16.6a1 1 0 0 0 .9-1.5z"/><path d="M12 10v4.5"/><path d="M12 17.6v.1"/>',
}


def icon(name, x, y, size, color, stroke=1.7):
    return (f'<svg style="position:absolute;left:{x}px;top:{y}px" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


def box(x, y, w, h, bg, r):
    return f'<div style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{bg};border-radius:{r}px"></div>'


def circle(cx_left, top, d, bg, icon_name=None, icon_color=WHITE, icon_size=17, stroke=1.8):
    html = box(cx_left, top, d, d, bg, d / 2)
    if icon_name:
        off = (d - icon_size) / 2
        html += icon(icon_name, cx_left + off, top + off, icon_size, icon_color, stroke)
    return html


# Sidebar logo, drawn in canvas pixels to match the target: wide roof, two pairs of columns, heavy base
LOGO = ('<svg style="position:absolute;left:99px;top:53px" width="35" height="32" viewBox="0 0 35 32" fill="none" '
        f'stroke="{GOLD}" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M1.5 11 17.5 1.5 33.5 11" stroke-width="2.1"/>'
        '<path d="M6 14.5v13M12.5 14.5v13M22.5 14.5v13M29 14.5v13" stroke-width="1.9"/>'
        '<path d="M1.5 30.3h32" stroke-width="2.6"/></svg>')

# --- Shared frame: app panel, sidebar, header, KPI row -----------------------------
NAV = [("house", 178.5), ("chart", 227), ("users", 275), ("shield", 324)]  # icon, centre y
KPI_X = [236, 573, 910]
KPI_W, KPI_Y, KPI_H = 322, 175, 111


def frame(active, kpi_icons):
    h = [box(22, 22, 1235, 964, WHITE, 26)]                      # app panel
    h.append(box(210, 46, 1, 916, DIVIDER, 0))                    # sidebar divider
    h.append(LOGO)                                                # logo
    for i, (name, cy) in enumerate(NAV):                         # nav
        if i == active:
            h.append(box(41, cy - 21, 151, 42, GOLD, 21))
            h.append(icon("chevron", 168, cy - 7, 14, DARK, 2))
        h.append(icon(name, 58, cy - 8, 16, DARK, 1.7))
    h.append(box(41, 856, 39, 39, DARK, 19.5))                    # initials circle
    h.append(box(41, 908, 151, 54, PANEL, 12))                    # dataset note box
    h.append(circle(236, 116, 41, DARK, "filter", WHITE, 16))    # header buttons
    h.append(circle(286, 116, 41, DARK, "search", WHITE, 16))
    h.append(box(336, 115, 148, 42, GOLD, 21))                    # export pill
    h.append(icon("download", 357, 129, 15, DARK, 2))
    h.append(box(779, 52, 453, 43, PANEL, 21.5))                  # slicer bar
    for x, ic in zip(KPI_X, kpi_icons):                           # KPI cards
        h.append(box(x, KPI_Y, KPI_W, KPI_H, PANEL, 18))
        h.append(circle(x + 19, 227, 41, DARK, ic, WHITE, 17))
    return h


# --- Page bodies ------------------------------------------------------------------
def overview():
    h = frame(0, ["landmark", "user", "shield"])
    # Client profile: panel, 3 white mini cards with gold icons, initials + arrow circles
    h.append(box(236, 304, 322, 266, PANEL, 18))
    for x, w, ic in ((255, 89, "coin"), (353, 88, "grid"), (450, 89, "trend")):
        h.append(box(x, 371, w, 100, WHITE, 12))
        h.append(icon(ic, x + w / 2 - 8, 384, 16, GOLD_ICON, 1.8))
    h.append(box(255, 513, 40, 40, DARK, 20))
    h.append(circle(498, 512, 41, GOLD, "arrow", DARK, 16, 2))
    # Risk weighting: panel + white toggle track
    h.append(box(236, 585, 322, 269, PANEL, 18))
    h.append(box(422, 603, 117, 32, WHITE, 16))
    # Gold wealth-concentration card, product book
    h.append(box(573, 304, 322, 386, GOLD_GRAD, 18))
    h.append(box(573, 704, 322, 258, PANEL, 18))
    # What drives risk: panel, white "Correlation r" pill, dark key-finding box
    h.append(box(910, 304, 322, 658, PANEL, 18))
    h.append(box(1130, 322, 82, 25, WHITE, 12.5))
    h.append(box(929, 841, 284, 104, DARK, 14))
    return h


COL_A, COL_B, COL_W = 236, 742, 490   # two-column pages


def wealth():
    h = frame(1, ["coin", "pie", "grid"])
    h.append(box(COL_A, 304, COL_W, 350, PANEL, 18))
    h.append(box(COL_B, 304, COL_W, 350, GOLD_GRAD, 18))
    h.append(box(COL_A, 670, COL_W, 292, PANEL, 18))
    h.append(box(COL_B, 670, COL_W, 292, DARK, 18))
    return h


def advisors():
    h = frame(2, ["users", "trend", "coin"])
    h.append(box(COL_A, 304, COL_W, 658, PANEL, 18))
    h.append(box(COL_B, 304, COL_W, 202, GOLD_GRAD, 18))
    h.append(box(COL_B, 522, COL_W, 213, PANEL, 18))
    h.append(box(COL_B, 751, COL_W, 211, PANEL, 18))
    return h


def risk():
    h = frame(3, ["shield", "alert", "coin"])
    h.append(box(COL_A, 304, COL_W, 334, GOLD_GRAD, 18))
    h.append(box(COL_A, 654, COL_W, 308, PANEL, 18))
    h.append(box(COL_B, 304, COL_W, 658, PANEL, 18))
    h.append(box(COL_B + 18, 841, COL_W - 36, 104, DARK, 14))
    return h


PAGES = {"bg_01_overview": overview, "bg_02_wealth": wealth, "bg_03_advisors": advisors, "bg_04_risk": risk}

OUT.mkdir(parents=True, exist_ok=True)
for name, build in PAGES.items():
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;padding:0}}'
            f'#c{{position:relative;width:{W}px;height:{H}px;overflow:hidden;'
            f'background:linear-gradient(135deg,{OUTER_A},{OUTER_B})}}</style></head>'
            f'<body><div id="c">{"".join(build())}</div></body></html>')
    src = OUT / f"{name}.html"
    src.write_text(html, encoding="utf-8")
    png = OUT / f"{name}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=2", f"--window-size={W},{H}",
                    f"--screenshot={png}", src.resolve().as_uri()],
                   check=True, capture_output=True)
    print("rendered", png.name)
