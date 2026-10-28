# Open datasets

Downloaded copies of the open datasets listed in `data/sources.md` ("Open datasets" section).

Use simple file names with no spaces:

| File | Dataset |
|---|---|
| `dubai_government_service_prices.csv` | Dubai Government Service Prices (Dubai Pulse) |
| `cause_of_traffic_fines.xlsx` | Cause of Traffic Fines (Bayanat) |
| `unified_federal_traffic_system_2023/` | the 8 XLSX tables (Bayanat) |

**Files over 50 MB** (for example the full Ejari rent contracts) go in `data/open/large/`.
git ignores that folder, because GitHub rejects files over 100 MB. Commit a small summary
instead (for example contracts per year), as a CSV in this folder.

Add the download date for each file to `data/sources.md`.
