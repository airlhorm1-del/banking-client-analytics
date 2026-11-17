# Notes

Working notes for the Power BI dashboard redesign (November 2026). The README is the public summary; this file is for whoever changes the dashboard next.

## What was built

- **4 redesigned pages** in a gold and ivory style: Overview, Wealth & Cross-sell, Advisors, Risk Drivers. The Overview follows `target_design.png` from the redesign kit.
- **1 hidden page, Client data**: a searchable table of all clients. The Search, Filter and Export buttons in the header open it; export uses the table's `...` menu (Export data).
- **Page size 1280 x 1008** (the shape of the target picture, not 16:9).
- **Backgrounds** are images (cards, icons, menu pill) with no text, so every word and number stays a live Power BI object.
- **Cards and panels** are HTML Content visuals that show HTML built by DAX measures, so every number follows the client-type selection.
- **Gauge and client-type pills** are Deneb visuals (Vega-Lite 6). Clicking a pill filters the page.
- **Correlations** in "What drives risk" are calculated live (Pearson r) for the current selection, not read from `risk_correlations.csv`.
- Titles and footnotes that make a claim check the data first (for example "Average income climbs at every risk level" changes to "mostly rises" for Private Bank).

## How to open it

1. Install **Power BI Desktop** (free).
2. Install the **Plus Jakarta Sans** font (free, Google Fonts) for the intended look. Without it, text falls back to Segoe UI.
3. Open `powerbi_dashboard/BankingDashboard.pbix`, or the project version `BankingDashboard.pbip`.
4. If the project was cloned to a new folder: Transform data > Edit parameters > set **DataFolder** to the full path of this repo's `clean\` folder (ending with `\`), then Refresh.

Custom visuals: Deneb 2.0.1 loads from AppSource automatically. HTML Content 2.0.0 (Standalone edition) is stored inside the report (`BankingDashboard.Report/CustomVisuals/`).

## How to change or rebuild it

The design scripts in `powerbi_dashboard/design/` write the files directly. Close Power BI Desktop first, run them from the repo root, then reopen the `.pbip`.

```
python powerbi_dashboard/design/make_backgrounds.py <output folder> "C:/Program Files/Google/Chrome/Application/chrome.exe"
python powerbi_dashboard/design/measures.py powerbi_dashboard/BankingDashboard.SemanticModel/definition
python powerbi_dashboard/design/overview.py powerbi_dashboard/BankingDashboard.Report
```

- `make_backgrounds.py`: draws the 5 page backgrounds with headless Chrome (copy the PNGs into `BankingDashboard.Report/StaticResources/RegisteredResources/`).
- `measures.py`: writes the HTML and card measures into `banking_clients.tmdl`. It only replaces measures it created; other measures are left alone.
- `overview.py`: rewrites the visuals of all 4 pages and the Client data page (positions are canvas pixels).

After changing the `.pbip`, save a fresh `.pbix` from Power BI Desktop: File > Save as > Browse this device > Save as type **Power BI file (\*.pbix)**.

## Sharing online

- Publishing to the Power BI service needs a Power BI account (Pro or Fabric workspace for sharing with others).
- In the service, Plus Jakarta Sans is not available, so text shows in the default font.
- HTML Content Standalone is not certified, so it does not appear in PDF or PowerPoint exports from the service, and some organisations block uncertified visuals.

## Known quirks

- In Power BI Desktop, buttons need **Ctrl+click** while editing. A plain click works in reading view and in the service.
- The client-type pills are a Deneb cross-filter, not a synced slicer, so each page keeps its own selection. Click "All clients" to clear it.
- The Risk / Products switch on the gauge goes back to "Risk" when the client type changes.
- Power BI's own button slicer ignored styling written into the files (open Microsoft issues: microsoft/powerbi-desktop-samples #93 and #98), which is why the pills use Deneb.
- The target picture shows income r = 0.67 and 11.8% for the 2nd quintile; the real data gives 0.66 and 11.7%, and the dashboard shows the real values.
- Power BI adds `legacyRendering: true` to HTML Content visuals when it saves; `overview.py` writes the same setting so files stay stable.
