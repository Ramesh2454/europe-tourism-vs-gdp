# Europe Tourism Flows vs GDP

A Tableau project by **Ramesh** testing two questions about travel between 30 European countries (EU-27, Norway, Iceland, Switzerland), 2010–2024, using only free public data.

| Hypothesis | Test | Result |
|---|---|---|
| **H1 – Wealth:** richer countries send more tourists abroad per resident | Pearson r, GDP per capita (PPP) vs outbound trips per 1,000 residents, excl. 2020–22 | r = **0.80** — Supported |
| **H2 – Distance:** tourists mostly visit nearby countries | Slope of log(arrivals) on log(distance), excl. 2020–22 | **−1.22** (double the distance ≈ 57% fewer arrivals) — Supported |

A gravity model (GDP, population, distance, border, language) explains 73% of the variation in flows. Its biggest positive outliers are close cultural pairs, e.g. Denmark → Iceland (20× expected), Finland → Estonia (17×), Slovenia → Croatia (14×).

**Patterns, not proof.** Eurostat counts arrivals at tourist accommodation, so one traveller staying in two hotels counts twice and stays with friends or family are missed. Distances are between capitals.

## Data sources

| Source | Dataset | Used for |
|---|---|---|
| [Eurostat](https://ec.europa.eu/eurostat/databrowser/view/tour_occ_arnraw/default/table) | `tour_occ_arnraw` | Arrivals by country of residence and destination |
| [World Bank WDI](https://data.worldbank.org/) | `NY.GDP.PCAP.PP.CD`, `SP.POP.TOTL` | GDP per capita (PPP), population |
| [CEPII GeoDist](https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=6) | `dist_cepii`, `geo_cepii` | Distance between capitals, shared border, common language, capital coordinates |

Download notes and code quirks: [`raw/SOURCES.md`](raw/SOURCES.md).

## Pipeline

```
raw/  ──(Colab notebook, Gemini-assisted)──▶  clean_gemini_v1/  ──(scripts/day2_finalise.py)──▶  clean/  ──▶  Tableau workbook
```

1. **Clean and join** (Google Colab): split Eurostat codes, keep 30 countries and 2010–2024, map country codes across sources, join on ISO3 + year. Prompt: [`docs/gemini_day2_prompt.md`](docs/gemini_day2_prompt.md).
2. **Finalise** — `python scripts/day2_finalise.py`: restores missing values to blank (not 0), adds COVID flag, corridor share and change vs 2019, fits the gravity model with population, and writes the analysis tables.
3. **Visualise** — `Europe Tourism vs GDP.twb` (Tableau Desktop / Tableau Public).

## Folder contents

| Path | What it holds |
|---|---|
| `docs/` | BRD (PDF), Colab prompt, raw data preview |
| `raw/` | Original downloads, unchanged |
| `clean_gemini_v1/` | Colab output; input to `day2_finalise.py` |
| `clean/` | Final tables for Tableau: `fact_pairs.csv` (origin × destination × year), `fact_origin_year.csv` (origin × year), analysis tables, [`data_dictionary.md`](clean/data_dictionary.md) |
| `scripts/` | `day2_finalise.py` (finalise + analysis), `build_workbook.py` (starter workbook) |

## Opening the workbook

The workbook reads the CSVs in `clean/`. If Tableau cannot find them after cloning, choose **Data → fact_pairs → Edit Connection** (and the same for `fact_origin_year`) and point it at your local `clean/` folder.
