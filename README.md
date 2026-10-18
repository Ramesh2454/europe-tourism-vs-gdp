# Europe Tourism Flows vs GDP

A Tableau project by **Ramesh** testing two questions about travel between 30 European countries (EU-27, Norway, Iceland, Switzerland), 2010–2024, using only free public data.

| Hypothesis | Test | Result |
|---|---|---|
| **H1 – Wealth:** richer countries send more tourists abroad per resident | Pearson r, GDP per capita (PPP) vs outbound trips per 1,000 residents, excl. 2020–22 | r = **0.80** — Supported |
| **H2 – Distance:** tourists mostly visit nearby countries | Slope of log(arrivals) on log(distance), excl. 2020–22 | **−1.22** (double the distance ≈ 57% fewer arrivals) — Supported |

A gravity model (GDP, population, distance, border, language) explains 73% of the variation in flows. Its biggest positive outliers are close cultural pairs, e.g. Denmark → Iceland (20× expected), Finland → Estonia (17×), Slovenia → Croatia (14×).

**Patterns, not proof.** Eurostat counts arrivals at tourist accommodation, so one traveller staying in two hotels counts twice and stays with friends or family are missed. Distances are between capitals.

## Key findings

1. **Richer countries travel more — and the link is strong.** GDP per capita and outbound trips per resident correlate at r = 0.80 (rank correlation 0.80, so a few outliers do not drive it). The average resident makes 0.63 trips a year to the other 29 countries.
2. **Distance cuts travel sharply.** Every doubling of distance between capitals means about 57% fewer arrivals (elasticity −1.22). The typical country sends 56% of its trips to capitals under 1,000 km away.
3. **But sun beats distance for the biggest flows.** Germany's top destination is Italy (14.1M arrivals, 1,187 km), ahead of neighbouring Austria (13.0M, 523 km); Spain is third (9.8M, 1,873 km). Mediterranean countries pull tourists from well beyond their neighbours.
4. **Culture and closeness create "super-corridors".** After allowing for wealth, size, distance, border and language, some pairs are far busier than expected: Denmark → Iceland (20×), Finland → Estonia (17×), Slovenia → Croatia (14×), Cyprus → Greece (12×). Austria and Czechia → Croatia (11–12×) show the pull of the Adriatic coast.
5. **COVID broke the pattern, and it is coming back.** Arrivals between the 30 countries fell 66% in 2020 versus 2019. The wealth–travel link weakened from r = 0.82 (2019) to 0.64 (2021) and has recovered to 0.75 (2024). By 2024, arrivals were 12% above 2019 on comparable country pairs, and every one of the 15 busiest corridors was above its 2019 level (+4% to +31%).
6. **Rich countries mostly travel "down" the wealth ladder.** Luxembourg, Norway, Switzerland, Ireland, the Netherlands and Austria send 94–100% of their trips to countries with lower GDP per capita. This is partly arithmetic — few destinations are richer than they are — so it shows where money flows, not proof of bargain hunting.

**Limits:** accommodation arrivals, not people; capital-to-capital distances understate how close some neighbours are (Paris–Madrid counts as 1,054 km); correlations show patterns, not causes.

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
