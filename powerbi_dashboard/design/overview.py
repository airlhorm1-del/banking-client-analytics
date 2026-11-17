"""Builds the redesigned Overview page (and the Client data page it links to) as PBIR visual.json files.

Re-runnable: wipes and rewrites the visuals of these two pages only. Positions are canvas pixels on the
1280 x 1008 page, measured from target_design.png.
Usage: python overview.py <Report folder>
"""
import hashlib
import json
import os
import shutil
import stat
import sys
from pathlib import Path

REPORT = Path(sys.argv[1])
PAGES = REPORT / "definition" / "pages"
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"
OVERVIEW, WEALTH, ADVISORS, RISK = "6abdf64baed257d60b90", "b7394d148872655d5ac0", "9380228668638e78207e", "93b82335099ea500518a"
DATA_PAGE = hashlib.md5(b"client data page").hexdigest()[:20]
HTML_VISUAL = "STANDALONEhtmlContent443BE3AD55E043BF878BED274D3A6855"
DENEB_VISUAL = "deneb7E15AEF80B9E4D4F8E12924291ECE89A"
T = "banking_clients"

INK, INK2, GREY, GOLD, PANEL = "#17140F", "#2F2B26", "#6B665D", "#C9A45C", "#F6F4EF"
REGULAR, SEMIBOLD = "Plus Jakarta Sans", "Plus Jakarta Sans SemiBold"


# ------------------------------------------------------------------ small JSON helpers
def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def b(v):
    return lit("true" if v else "false")


def num(v):
    return lit(f"{v}D")


def txt(v):
    return lit("'" + str(v).replace("'", "''") + "'")


def colour(c):
    return {"solid": {"color": txt(c)}}


def measure_colour(name):
    return {"solid": {"color": {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": T}}, "Property": name}}}}}


def measure(name, entity=T):
    return {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": name}},
            "queryRef": f"{entity}.{name}", "nativeQueryRef": name}


def column(name, entity=T, display=None):
    p = {"field": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": name}},
         "queryRef": f"{entity}.{name}", "nativeQueryRef": name}
    if display:
        p["displayName"] = display
    return p


def bare(padding=0):
    """Container chrome off: no background, border, title, header or shadow."""
    return {
        "background": [{"properties": {"show": b(False)}}],
        "border": [{"properties": {"show": b(False)}}],
        "title": [{"properties": {"show": b(False)}}],
        "visualHeader": [{"properties": {"show": b(False)}}],
        "dropShadow": [{"properties": {"show": b(False)}}],
        "padding": [{"properties": {k: num(padding) for k in ("top", "bottom", "left", "right")}}],
    }


class Page:
    def __init__(self, page_id):
        self.dir = PAGES / page_id / "visuals"
        self.items = []

    def add(self, key, x, y, w, h, visual, z=None):
        name = hashlib.md5(f"{self.dir.parent.name}/{key}".encode()).hexdigest()[:20]
        n = len(self.items)
        self.items.append({
            "$schema": SCHEMA, "name": name,
            "position": {"x": x, "y": y, "z": z if z is not None else 1000 + n, "height": h, "width": w, "tabOrder": n},
            "visual": visual,
        })

    def write(self):
        if self.dir.exists():
            # OneDrive marks folders read-only; clear the flag and retry instead of failing
            def unlock(func, path, _):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(self.dir, onexc=unlock)
        for v in self.items:
            d = self.dir / v["name"]
            d.mkdir(parents=True)
            (d / "visual.json").write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{self.dir.parent.name}: {len(self.items)} visuals")


# ------------------------------------------------------------------ visual builders
def textbox(paragraphs):
    """paragraphs: list of (text, size_px, colour, family, bold, align)."""
    paras = []
    for text, size, col, fam, bold, align in paragraphs:
        style = {"fontFamily": fam, "fontSize": f"{size}px", "color": col}
        if bold:
            style["fontWeight"] = "bold"
        paras.append({"textRuns": [{"value": text, "textStyle": style}], "horizontalTextAlignment": align})
    return {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paras}}]},
            "visualContainerObjects": bare(), "drillFilterOtherVisuals": True}


def html(measure_name):
    return {
        "visualType": HTML_VISUAL,
        "query": {"queryState": {"content": {"projections": [measure(measure_name)]}}},
        "objects": {"contentFormatting": [{"properties": {"noDataMessage": txt(" ")}}]},
        "visualContainerObjects": bare(), "drillFilterOtherVisuals": True,
    }


def link(kind, tooltip=None, page=None):
    p = {"show": b(True), "type": txt(kind)}
    if page:
        p["navigationSection"] = txt(page)
    if tooltip:
        p["tooltip"] = txt(tooltip)
    return [{"properties": p}]


def button(action, radius, label=None, fill=None, fill_measure=None, hover=GOLD, hover_transparency=82,
           text_colour=INK, size_pt=9, family=SEMIBOLD):
    """Clickable area. Transparent unless fill / fill_measure is given; label optional."""
    if fill_measure:
        default_fill = {"fillColor": measure_colour(fill_measure), "transparency": num(0)}
    elif fill:
        default_fill = {"fillColor": colour(fill), "transparency": num(0)}
    else:
        default_fill = {"fillColor": colour(GOLD), "transparency": num(100)}
    objects = {
        "icon": [{"properties": {"show": b(False)}},
                 {"properties": {"shapeType": txt("blank"), "placement": txt("left")}, "selector": {"id": "default"}}],
        "fill": [{"properties": {"show": b(True)}},
                 {"properties": default_fill, "selector": {"id": "default"}},
                 {"properties": {"fillColor": colour(hover), "transparency": num(hover_transparency)}, "selector": {"id": "hover"}}],
        "outline": [{"properties": {"show": b(False)}}],
        "shape": [{"properties": {"tileShape": txt("rectangleRounded"), "roundEdge": lit(f"{radius}L")}},
                  {"properties": {"tileShape": txt("rectangleRounded")}, "selector": {"id": "default"}}],
    }
    if label:
        objects["text"] = [{"properties": {"show": b(True)}},
                           {"properties": {"text": txt(label), "fontSize": num(size_pt), "fontColor": colour(text_colour),
                                           "fontFamily": txt(family), "horizontalAlignment": txt("center")},
                            "selector": {"id": "default"}}]
    else:
        objects["text"] = [{"properties": {"show": b(False)}}]
    vco = bare()
    vco["visualLink"] = action
    return {"visualType": "actionButton", "objects": objects, "visualContainerObjects": vco, "drillFilterOtherVisuals": True}


STATE = lambda s: {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "id": s}


def pill_slicer(field_proj, columns, radius, selected_filter=None, strict=False, sync=None, size_pt=9):
    objects = {
        "layout": [{"properties": {"autoGrid": b(False), "rowCount": lit("1L"), "columnCount": lit(f"{columns}L"),
                                   "maxTiles": lit(f"{columns}L"), "cellPadding": num(3),
                                   "innerPadding": num(2), "outerPadding": num(0)}}],
        "shapeCustomRectangle": [{"properties": {"tileShape": txt("rectangleRounded"), "rectangleRoundedCurve": lit(f"{radius}L")}},
                                 {"properties": {"tileShape": txt("rectangleRounded")}, "selector": STATE("default")}],
        "fillCustom": [{"properties": {"show": b(True)}},
                       {"properties": {"fillColor": colour(PANEL), "transparency": num(100)}, "selector": STATE("default")},
                       {"properties": {"fillColor": colour("#E6D9B8"), "transparency": num(0)}, "selector": STATE("hover")},
                       {"properties": {"fillColor": colour(GOLD), "transparency": num(0)}, "selector": STATE("selected")}],
        "value": [{"properties": {"show": b(True)}},
                  {"properties": {"fontColor": colour(INK2), "fontSize": num(size_pt), "fontFamily": txt(REGULAR),
                                  "horizontalAlignment": txt("center")}, "selector": STATE("default")},
                  {"properties": {"fontColor": colour(INK), "fontFamily": txt(SEMIBOLD)}, "selector": STATE("selected")}],
        "label": [{"properties": {"show": b(False)}}],
        "outline": [{"properties": {"show": b(False)}}],
        "accentBar": [{"properties": {"show": b(False)}}],
        "padding": [{"properties": {"paddingIndividual": b(False), "paddingUniform": num(2)}, "selector": STATE("default")}],
        "selection": [{"properties": {"singleSelect": b(True), "strictSingleSelect": b(strict)}}],
    }
    if selected_filter:
        objects["general"] = [{"properties": {"filter": {"filter": selected_filter}}}]
    v = {"visualType": "advancedSlicerVisual", "query": {"queryState": {"Values": {"projections": [field_proj]}}},
         "objects": objects, "visualContainerObjects": bare(), "drillFilterOtherVisuals": True}
    if sync:
        v["syncGroup"] = {"groupName": sync, "fieldChanges": True, "filterChanges": True}
    return v


def in_filter(entity, col, value):
    return {"Version": 2, "From": [{"Name": "g", "Entity": entity, "Type": 0}],
            "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "g"}}, "Property": col}}],
                                            "Values": [[{"Literal": {"Value": f"'{value}'"}}]]}}}]}


# ------------------------------------------------------------------ Deneb gauge spec (Vega-Lite 6)
# The visual covers the panel from the switch down (canvas 236,600 / 322 x 254). The Risk / Products
# switch is part of the spec: a click selection ("metric") picks which of the two folded rows is drawn.
W, H, CX, CY = 322, 254, 159.5, 164
GOLD_DARK = "#C9A45C"


def ticks(n, r1, r2, width, colour_expr):
    return {
        "transform": [
            {"filter": {"param": "metric"}},
            {"calculate": f"sequence(0, {n})", "as": "i"}, {"flatten": ["i"]},
            {"calculate": f"(-120 + 240 * datum.i / {n - 1}) * PI / 180", "as": "a"},
            {"calculate": f"{CX} + {r1} * sin(datum.a)", "as": "x1"}, {"calculate": f"{CY} - {r1} * cos(datum.a)", "as": "y1"},
            {"calculate": f"{CX} + {r2} * sin(datum.a)", "as": "x2"}, {"calculate": f"{CY} - {r2} * cos(datum.a)", "as": "y2"},
            {"calculate": colour_expr, "as": "c"},
        ],
        "mark": {"type": "rule", "strokeWidth": width, "strokeCap": "round"},
        "encoding": {
            "x": {"field": "x1", "type": "quantitative", "scale": None, "axis": None},
            "y": {"field": "y1", "type": "quantitative", "scale": None, "axis": None},
            "x2": {"field": "x2"}, "y2": {"field": "y2"},
            "color": {"field": "c", "type": "nominal", "scale": None, "legend": None},
        },
    }


def text_mark(x, y, size, weight, fill, text=None, field=None, align="left", filt=None):
    mark = {"type": "text", "x": x, "y": y, "fontSize": size, "fontWeight": weight, "fill": fill, "align": align,
            "baseline": "alphabetic", "font": REGULAR}
    layer = {"mark": mark}
    if filt:
        layer["transform"] = [{"filter": filt}]
    if text:
        mark["text"] = text
    else:
        layer["encoding"] = {"text": {"field": field, "type": "nominal"}}
    return layer


def px(field):
    return {"field": field, "type": "quantitative", "scale": None, "axis": None}


def switch_layers():
    """Risk / Products switch drawn inside the gauge (canvas 422,603 is local 186,3)."""
    return [
        {"transform": [{"filter": {"param": "metric"}}],
         "mark": {"type": "rect", "cornerRadius": 13, "fill": GOLD_DARK},
         "encoding": {"x": px("px1"), "x2": {"field": "px2"}, "y": {"value": 6}, "y2": {"value": 32}}},
        {"transform": [{"filter": {"param": "metric"}}],
         "mark": {"type": "text", "font": REGULAR, "fontSize": 10.5, "fontWeight": 700, "fill": INK, "align": "center", "baseline": "middle"},
         "encoding": {"x": px("pcx"), "y": {"value": 19.5}, "text": {"field": "m", "type": "nominal"}}},
        {"transform": [{"filter": {"not": {"param": "metric"}}}],
         "mark": {"type": "text", "font": REGULAR, "fontSize": 10.5, "fontWeight": 400, "fill": INK2, "align": "center", "baseline": "middle"},
         "encoding": {"x": px("pcx"), "y": {"value": 19.5}, "text": {"field": "m", "type": "nominal"}}},
        {"params": [{"name": "metric", "value": [{"m": "Risk"}],
                     "select": {"type": "point", "fields": ["m"], "on": "click", "toggle": False, "clear": False}}],
         "mark": {"type": "rect", "fill": "#FFFFFF", "opacity": 0, "cursor": "pointer"},
         "encoding": {"x": px("px1"), "x2": {"field": "px2"}, "y": {"value": 6}, "y2": {"value": 32}}},
    ]


GAUGE_SPEC = {
    "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
    "data": {"name": "dataset"},
    "width": W, "height": H, "padding": 0, "autosize": {"type": "none"}, "background": "transparent",
    "config": {"view": {"stroke": None}},
    "transform": [
        {"fold": ["Avg Risk Weighting", "Avg Products Held"], "as": ["key", "value"]},
        {"calculate": "datum.key == 'Avg Risk Weighting' ? 'Risk' : 'Products'", "as": "m"},
        {"calculate": "datum.m == 'Risk' ? 5 : 6", "as": "hi"},
        {"calculate": "clamp((datum.value - 1) / (datum.hi - 1), 0, 1)", "as": "frac"},
        {"calculate": "format(datum.value, '.2f')", "as": "label"},
        {"calculate": "datum.m == 'Risk' ? 'avg risk level, scale 1 to 5' : 'avg products held, scale 1 to 6'", "as": "caption"},
        {"calculate": "datum.m == 'Risk' ? 188 : 232", "as": "px1"},
        {"calculate": "datum.m == 'Risk' ? 230 : 301", "as": "px2"},
        {"calculate": "(datum.px1 + datum.px2) / 2", "as": "pcx"},
    ],
    "layer": switch_layers() + [
        ticks(36, 73, 94, 7, "datum.i % 2 == 0 ? '#D9BC7E' : '#E8D6AE'"),
        ticks(30, 51, 65, 4.5, "datum.i / 29 <= datum.frac ? '#17140F' : '#E4DFD5'"),
        text_mark(CX, 175, 36, 700, INK, field="label", align="center", filt={"param": "metric"}),
        text_mark(CX, 197, 10.5, 400, GREY, field="caption", align="center", filt={"param": "metric"}),
        {"mark": {"type": "circle", "x": 23, "y": 50, "size": 45, "fill": INK, "opacity": 1}},
        text_mark(32, 54, 10.5, 400, GREY, text="Average level"),
        {"mark": {"type": "circle", "x": 115, "y": 50, "size": 45, "fill": "#D9BC7E", "opacity": 1}},
        text_mark(125, 54, 10.5, 400, GREY, text="Full scale"),
    ],
}

# ------------------------------------------------------------------ Deneb client-type pills (cross-filter)
# Covers the slicer bar (canvas 779,52 / 453 x 43). Clicking a pill filters the page; the "All clients" pill
# is an aggregated row with no data identity, so clicking it clears the selection.
PILL_CX, PILL_W = "[138, 219, 300.5, 399.5]", "[94, 58, 95, 93]"
PILLS_SPEC = {
    "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
    "data": {"name": "dataset"},
    "width": 453, "height": 43, "padding": 0, "autosize": {"type": "none"}, "background": "transparent",
    "config": {"view": {"stroke": None}},
    "transform": [
        {"calculate": "datum['__selected__'] == 'on' ? 1 : 0", "as": "isOn"},
        {"calculate": f"{PILL_CX}[datum['Relationship Order'] - 1]", "as": "cx"},
        {"calculate": f"{PILL_W}[datum['Relationship Order'] - 1]", "as": "w"},
        {"calculate": "datum.cx - datum.w / 2", "as": "x1"},
        {"calculate": "datum.cx + datum.w / 2", "as": "x2"},
    ],
    "layer": [
        {"transform": [{"filter": "datum.isOn == 1"}],
         "mark": {"type": "rect", "cornerRadius": 16.5, "fill": GOLD_DARK},
         "encoding": {"x": px("x1"), "x2": {"field": "x2"}, "y": {"value": 5}, "y2": {"value": 38}}},
        {"mark": {"type": "rect", "fill": "#FFFFFF", "opacity": 0, "cursor": "pointer"},
         "encoding": {"x": px("x1"), "x2": {"field": "x2"}, "y": {"value": 5}, "y2": {"value": 38}}},
        {"transform": [{"filter": "datum.isOn == 1"}],
         "mark": {"type": "text", "font": REGULAR, "fontSize": 12, "fontWeight": 700, "fill": INK, "align": "center", "baseline": "middle", "cursor": "pointer"},
         "encoding": {"x": px("cx"), "y": {"value": 22}, "text": {"field": "banking_relationship", "type": "nominal"}}},
        {"transform": [{"filter": "datum.isOn == 0"}],
         "mark": {"type": "text", "font": REGULAR, "fontSize": 12, "fontWeight": 400, "fill": INK2, "align": "center", "baseline": "middle", "cursor": "pointer"},
         "encoding": {"x": px("cx"), "y": {"value": 22}, "text": {"field": "banking_relationship", "type": "nominal"}}},
        {"transform": [{"aggregate": [{"op": "sum", "field": "isOn", "as": "nOn"}]}],
         "mark": {"type": "rect", "cornerRadius": 16.5, "cursor": "pointer"},
         "encoding": {"x": {"value": 6}, "x2": {"value": 87}, "y": {"value": 5}, "y2": {"value": 38},
                      "fill": {"condition": {"test": "datum.nOn == 0", "value": GOLD_DARK}, "value": PANEL}}},
        {"transform": [{"aggregate": [{"op": "sum", "field": "isOn", "as": "nOn"}]}],
         "mark": {"type": "text", "font": REGULAR, "fontSize": 12, "align": "center", "baseline": "middle", "cursor": "pointer", "text": "All clients"},
         "encoding": {"x": {"value": 46.5}, "y": {"value": 22},
                      "fill": {"condition": {"test": "datum.nOn == 0", "value": INK}, "value": INK2},
                      "fontWeight": {"condition": {"test": "datum.nOn == 0", "value": 700}, "value": 400}}},
    ],
}


def deneb(spec, fields, selection=False):
    """fields: list of ("measure"|"column", name)."""
    projections = [measure(n) if kind == "measure" else column(n) for kind, n in fields]
    return {
        "visualType": DENEB_VISUAL,
        "query": {"queryState": {"dataset": {"projections": projections}}},
        "objects": {"vega": [{"properties": {
            "provider": txt("vegaLite"), "version": txt("6.4.3"), "renderMode": txt("svg"),
            "jsonSpec": txt(json.dumps(spec, indent=2)), "jsonConfig": txt("{}"),
            "enableTooltips": b(False), "enableContextMenu": b(False), "enableSelection": b(selection),
            "enableHighlight": b(False)}}]},
        "visualContainerObjects": bare(), "drillFilterOtherVisuals": True,
    }


# ------------------------------------------------------------------ shared sidebar + header
NAV = [("Overview", OVERVIEW, 158), ("Wealth & Cross-sell", WEALTH, 206), ("Advisors", ADVISORS, 254), ("Risk Drivers", RISK, 303)]


def sidebar_and_header(p, active_page, show_header_buttons=True):
    p.add("brand 1", 41, 95, 160, 18, textbox([("C L I E N T", 11.5, INK, REGULAR, True, "left")]))
    p.add("brand 2", 41, 109, 160, 18, textbox([("A N A L Y T I C S", 11.5, INK, REGULAR, True, "left")]))
    # nav labels (textboxes) + transparent click areas on top
    for label, page_id, top in NAV:
        active = page_id == active_page
        fam, col = (SEMIBOLD, INK) if active else (REGULAR, "#2A2723")
        if label == "Wealth & Cross-sell":
            p.add("nav label wealth", 79, top + 3, 105, 38, textbox([("Wealth &", 12.5, col, fam, False, "left"), ("Cross-sell", 12.5, col, fam, False, "left")]))
        else:
            p.add(f"nav label {label}", 79, top + 11, 105, 20, textbox([(label, 13 if active else 12.5, col, fam, False, "left")]))
    for label, page_id, top in NAV:
        if page_id != active_page:
            p.add(f"nav button {label}", 41, top, 151, 42,
                  button(link("PageNavigation", f"Go to {label}", page_id), 21), z=5000 + len(p.items))
    # footer
    p.add("initials", 41, 866, 39, 20, textbox([("EN", 12, "#D9BC7E", REGULAR, True, "center")]))
    p.add("footer name", 90, 859, 118, 36, textbox([("Elom Nyadzi", 12, INK, SEMIBOLD, False, "left"),
                                                    ("Data Analyst · Berlin", 10.5, GREY, REGULAR, False, "left")]))
    p.add("dataset note", 50, 911, 140, 60, textbox([("Synthetic dataset · 3,000", 9.5, GREY, REGULAR, False, "left"),
                                                    ("clients · Python, TMDL,", 9.5, GREY, REGULAR, False, "left"),
                                                    ("Power BI", 9.5, GREY, REGULAR, False, "left")]))
    # client-type pills (Deneb, clicking a pill filters the page)
    p.add("relationship pills", 779, 52, 453, 43,
          deneb(PILLS_SPEC, [("column", "banking_relationship"), ("column", "Relationship Order"), ("measure", "Total Clients")],
                selection=True), z=3000)
    if show_header_buttons:
        p.add("export label", 380, 127, 100, 20, textbox([("Export report", 12.5, INK, SEMIBOLD, False, "left")]))
        p.add("filter button", 236, 116, 41, 41, button(link("PageNavigation", "Filter and find clients", DATA_PAGE), 20, hover="#FFFFFF", hover_transparency=80), z=5100)
        p.add("search button", 286, 116, 41, 41, button(link("PageNavigation", "Find a client", DATA_PAGE), 20, hover="#FFFFFF", hover_transparency=80), z=5101)
        p.add("export button", 336, 115, 148, 42, button(link("PageNavigation", "Open the client table to export", DATA_PAGE), 21, hover="#FFFFFF", hover_transparency=75), z=5102)


# ------------------------------------------------------------------ Overview page
ov = Page(OVERVIEW)
sidebar_and_header(ov, OVERVIEW)
ov.add("title", 236, 49, 440, 34, textbox([("Client Portfolio Overview", 25, INK, "Plus Jakarta Sans ExtraBold", False, "left")]))
ov.add("subtitle", 236, 86, 420, 20, html("Overview Subtitle HTML"))
ov.add("kpi value", 236, 175, 322, 111, html("KPI Value HTML"))
ov.add("kpi clients", 573, 175, 322, 111, html("KPI Clients HTML"))
ov.add("kpi risk", 910, 175, 322, 111, html("KPI Risk HTML"))
ov.add("client profile", 236, 304, 322, 266, html("Client Profile HTML"))
ov.add("advisor arrow", 498, 512, 41, 41, button(link("PageNavigation", "See all advisors", ADVISORS), 20, hover="#FFFFFF", hover_transparency=75), z=5200)
ov.add("risk title", 256, 608, 160, 26, textbox([("Risk weighting", 16.5, INK, "Plus Jakarta Sans ExtraBold", False, "left")]))
ov.add("gauge", 236, 600, 322, 254, deneb(GAUGE_SPEC, [("measure", "Avg Risk Weighting"), ("measure", "Avg Products Held")]))
ov.add("wealth headline", 573, 304, 322, 180, html("Wealth Headline HTML"))
ov.add("quintile list", 593, 489, 282, 182, html("Quintile List HTML"))
ov.add("product book", 573, 704, 322, 258, html("Product Book HTML"))
ov.add("risk drivers", 910, 304, 322, 658, html("Risk Drivers HTML"))
ov.write()


def filter_not_highlight(page_id, page_obj):
    """Deneb supports cross-highlight, so tell the page to pass pill clicks to Deneb visuals as a filter."""
    pj_path = PAGES / page_id / "page.json"
    page_def = json.loads(pj_path.read_text(encoding="utf-8"))
    names = {v["visual"]["visualType"]: [] for v in page_obj.items}
    pills = [v["name"] for v in page_obj.items if v["name"] == hashlib.md5(f"{page_id}/relationship pills".encode()).hexdigest()[:20]]
    targets = [v["name"] for v in page_obj.items if v["visual"]["visualType"] == DENEB_VISUAL and v["name"] not in pills]
    page_def["visualInteractions"] = [{"source": pills[0], "target": t, "type": "DataFilter"} for t in targets]
    pj_path.write_text(json.dumps(page_def, indent=2, ensure_ascii=False), encoding="utf-8")


filter_not_highlight(OVERVIEW, ov)

# ------------------------------------------------------------------ Wealth & Cross-sell page
wl = Page(WEALTH)
sidebar_and_header(wl, WEALTH)
wl.add("title", 236, 49, 440, 34, textbox([("Wealth & Cross-sell", 25, INK, "Plus Jakarta Sans ExtraBold", False, "left")]))
wl.add("subtitle", 236, 86, 520, 20, html("Wealth Subtitle HTML"))
wl.add("kpi value", 236, 175, 322, 111, html("Wealth KPI Value HTML"))
wl.add("kpi top share", 573, 175, 322, 111, html("Wealth KPI Top Share HTML"))
wl.add("kpi products", 910, 175, 322, 111, html("Wealth KPI Products HTML"))
wl.add("value by quintile", 236, 304, 490, 350, html("Value By Quintile HTML"))
wl.add("tier value", 742, 304, 490, 350, html("Tier Value HTML"))
wl.add("tier depth", 236, 670, 490, 292, html("Tier Depth HTML"))
wl.add("finding", 742, 670, 490, 292, html("Wealth Finding HTML"))
wl.write()

# ------------------------------------------------------------------ Advisors page
ad = Page(ADVISORS)
sidebar_and_header(ad, ADVISORS)
ad.add("title", 236, 49, 440, 34, textbox([("Advisors", 25, INK, "Plus Jakarta Sans ExtraBold", False, "left")]))
ad.add("subtitle", 236, 86, 520, 20, html("Advisors Subtitle HTML"))
ad.add("kpi count", 236, 175, 322, 111, html("Advisor KPI Count HTML"))
ad.add("kpi gap", 573, 175, 322, 111, html("Advisor KPI Gap HTML"))
ad.add("kpi value", 910, 175, 322, 111, html("Advisor KPI Value HTML"))
ad.add("ranking", 236, 304, 490, 658, html("Advisor Ranking HTML"))
ad.add("spread", 742, 304, 490, 202, html("Advisor Spread HTML"))
ad.add("fee structure", 742, 522, 490, 213, html("Fee Structure HTML"))
ad.add("age bands", 742, 751, 490, 211, html("Age Band Income HTML"))
ad.write()

# ------------------------------------------------------------------ Client data page (search + export)
page_dir = PAGES / DATA_PAGE
page_dir.mkdir(parents=True, exist_ok=True)
(page_dir / "page.json").write_text(json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
    "name": DATA_PAGE, "displayName": "Client data", "displayOption": "FitToPage", "height": 1008, "width": 1280,
    "objects": {"background": [{"properties": {
        "color": colour("#E7E1D5"),
        "image": {"image": {"name": txt("bg_05_client_data.png"),
                            "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1, "ItemName": "bg_05_client_data.png"}}},
                            "scaling": txt("Fit")}},
        "transparency": num(0)}}]},
}, indent=2), encoding="utf-8")

cd = Page(DATA_PAGE)
sidebar_and_header(cd, None, show_header_buttons=False)
cd.add("title", 236, 49, 440, 34, textbox([("Client data", 25, INK, REGULAR, True, "left")]))
cd.add("subtitle", 236, 86, 520, 20, textbox([("Search for a client, or export the table from its ... menu (top right of the table).", 12.5, GREY, REGULAR, False, "left")]))
cd.add("back", 236, 116, 170, 42, button(link("PageNavigation", "Back to the overview", OVERVIEW), 21, label="← Back to overview",
                                         fill=GOLD, hover="#B8924A", hover_transparency=0), z=5000)
search = {
    "visualType": "slicer",
    "query": {"queryState": {"Values": {"projections": [column("name", display="Client")]}}},
    "objects": {
        "data": [{"properties": {"mode": txt("Dropdown")}}],
        "general": [{"properties": {"selfFilterEnabled": b(True)}}],
        "header": [{"properties": {"show": b(False)}}],
        "items": [{"properties": {"fontFamily": txt(REGULAR), "textSize": num(10), "fontColor": colour(INK)}}],
    },
    "visualContainerObjects": bare(4), "drillFilterOtherVisuals": True,
}
cd.add("name search", 424, 116, 300, 42, search, z=3002)
table_cols = [("name", "Client"), ("client_id", "ID"), ("banking_relationship", "Relationship"),
              ("loyalty_classification", "Loyalty tier"), ("investment_advisor", "Advisor"),
              ("total_relationship_value", "Relationship value"), ("estimated_income", "Estimated income"),
              ("risk_weighting", "Risk level"), ("product_count", "Products")]
table_vco = bare()
table_vco["visualHeader"] = [{"properties": {"show": b(True)}}]   # keeps the ... menu with Export data
cd.add("client table", 252, 191, 964, 755, {
    "visualType": "tableEx",
    "query": {"queryState": {"Values": {"projections": [column(c, display=d) for c, d in table_cols]}}},
    "objects": {
        "columnHeaders": [{"properties": {"columnAdjustment": txt("growToFit"), "autoSizeColumnWidth": b(True),
                                          "fontFamily": txt(SEMIBOLD), "fontColor": colour(INK), "backColor": colour(PANEL)}}],
        "values": [{"properties": {"fontFamily": txt(REGULAR), "fontColorPrimary": colour(INK2), "backColorPrimary": colour("#FFFFFF"),
                                   "fontColorSecondary": colour(INK2), "backColorSecondary": colour("#FBFAF7")}}],
        "grid": [{"properties": {"gridVertical": b(False), "outlineColor": colour("#E8E3D8")}}],
    },
    "visualContainerObjects": table_vco, "drillFilterOtherVisuals": True,
})
cd.write()

# hidden in reading view, listed last; remove the temporary slicer test page if it is still there
pj = PAGES / "pages.json"
pages = json.loads(pj.read_text(encoding="utf-8"))
if DATA_PAGE not in pages["pageOrder"]:
    pages["pageOrder"].append(DATA_PAGE)
TEST_PAGE = "zz0test0slicer0page0"
pages["pageOrder"] = [x for x in pages["pageOrder"] if x != TEST_PAGE]
if (PAGES / TEST_PAGE).exists():
    def _unlock(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    shutil.rmtree(PAGES / TEST_PAGE, onexc=_unlock)
pj.write_text(json.dumps(pages, indent=2), encoding="utf-8")
page = json.loads((page_dir / "page.json").read_text(encoding="utf-8"))
page["visibility"] = "HiddenInViewMode"
(page_dir / "page.json").write_text(json.dumps(page, indent=2), encoding="utf-8")
print("client data page:", DATA_PAGE)
