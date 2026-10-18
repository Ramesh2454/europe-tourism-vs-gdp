You are a senior data analyst working in Google Colab with pandas and numpy. Write a clean, well-commented notebook, one step per cell with a markdown heading, for the Day 2 work of my project "Europe Tourism Flows vs GDP". The output feeds a Tableau Public dashboard.

## Goal
Test two hypotheses for 30 European countries, 2010–2024:
- H1 (Wealth): countries with higher GDP per capita send more tourists abroad per resident.
- H2 (Distance): tourists mostly visit nearby countries, and arrivals fall as distance grows.

## Input
A zip in Google Drive with 5 CSV files. Mount Drive and unzip:
```python
from google.colab import drive
drive.mount('/content/drive')
!unzip -o /content/drive/MyDrive/europe-tourism/colab_upload.zip -d /content/raw
RAW = '/content/raw/'
OUT = '/content/drive/MyDrive/europe-tourism/clean/'
```

1. `eurostat_tour_occ_arnraw.csv` (27,189 rows × 37 columns)
   - First column is named `freq,unit,c_resid,nace_r2,geo\TIME_PERIOD` and holds 5 comma-separated codes in one string, e.g. `A,NR,AT,I551-I553,DE`. Split it into freq, unit, c_resid (origin = country of residence), nace_r2 (accommodation type), geo (destination).
   - The remaining columns are years 1990–2025, one column per year. Values are strings: `:` means missing, and a value may carry a flag letter after a space, e.g. `1656 e` or `939 p`. Put the number in `arrivals` and the letters in `flag`. Missing must be NaN, never 0.
2. `worldbank_gdp_pc_ppp.csv` (266 × 70): columns Country Name, Country Code (ISO3), Indicator Name, Indicator Code, then years 1960–2025. GDP per capita, PPP, current international $.
3. `worldbank_population.csv` (266 × 70): same layout, total population.
4. `cepii_dist.csv` (50,176 × 14): iso_o, iso_d (ISO3), contig (1 = shared border), comlang_off (1 = common official language), distcap (km between capitals), plus other columns we do not need.
5. `cepii_geo.csv` (238 × 34): iso2, iso3, country, city_en, lat, lon, cap (1 = capital city), and others.

## Country scope and code mapping (critical)
Build `country_map` with columns: eurostat_dest_code, eurostat_origin_code, iso3_wb, iso3_cepii, country_name, capital, lat, lon. Use the 30 countries EU-27 plus Norway, Iceland and Switzerland:
AT BE BG HR CY CZ DK EE FI FR DE EL HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE NO IS CH.

Known quirks, all verified in these files:
- Eurostat uses `EL` for Greece (ISO3 GRC).
- Eurostat reports Switzerland as a destination as `CH`, but as an origin only as `CH_LI` (Switzerland + Liechtenstein). Map `CH_LI` → CHE for origins.
- CEPII uses `ROM` for Romania; the World Bank uses `ROU`. Keep both columns in the map.
- `cepii_geo` has 2 rows for Germany (Berlin and Essen). Use only rows where `cap == 1`.
- Drop every Eurostat aggregate or non-country code (EU27_2020, EU28, EA*, EU25, EU, WORLD, INT_*, EUR_OTH, DOM, continents, etc.). Keeping only the 30 codes above does this.
Assert that all 30 countries are found in every source, and print any that are missing.

## Cleaning steps
1. Eurostat: keep unit == 'NR', nace_r2 == 'I551-I553' (all accommodation), years 2010–2024 only (2025 is incomplete), geo in the 30 destinations, c_resid in the 30 origins. Remove domestic rows where origin == destination. Reshape wide to long: origin, destination, year, arrivals, flag.
2. World Bank: reshape both files to long (iso3, year, value), merge into one table (iso3, year, gdp_pc_ppp, population), keep the 30 countries and 2010–2024.
3. CEPII: keep pairs where both countries are in the 30. Columns: origin, destination, distance_km (= distcap), border (= contig), common_lang (= comlang_off).
4. Join everything on ISO3 for origin and destination, plus year. Use one internal key, `iso3` = the World Bank code; translate CEPII codes through the map.

## Output table 1: fact_pairs.csv (one row per origin × destination × year)
origin_iso3, origin_name, dest_iso3, dest_name, year, arrivals, flag, distance_km, border, common_lang, within_1000km (distance_km < 1000), gdp_origin, gdp_dest, gdp_gap (= gdp_dest / gdp_origin), origin_lat, origin_lon, dest_lat, dest_lon, covid_flag (year in 2020–2022), corridor_share (= arrivals / total arrivals of all pairs that year), change_vs_2019 (= arrivals / same pair's 2019 arrivals − 1), residual, outlier_flag.

## Output table 2: fact_origin_year.csv (one row per origin × year)
origin_iso3, origin_name, year, outbound_arrivals (sum of arrivals to the other 29 countries; NaN if no destination reported), n_destinations_reported, population, gdp_pc_ppp, trips_per_1000 (= outbound_arrivals / population × 1000), share_within_1000km (= arrivals to destinations < 1000 km / outbound_arrivals), covid_flag.

## Analysis (exclude covid years 2020–2022 unless stated)
1. H1: Pearson r between gdp_pc_ppp and trips_per_1000, pooled over origin-years, and also for each year 2010–2024 (include covid years in the per-year series). Also report Spearman r as a robustness check. Verdict: r ≥ 0.5 "Supported", 0.3–0.5 "Partly supported", < 0.3 "Not supported".
2. H2: OLS slope of log(arrivals) on log(distance_km) over all pairs with arrivals > 0 (distance-decay elasticity), plus the median share_within_1000km across origins. Verdict: slope ≤ −1 and median share ≥ 50% "Supported"; slope < 0 "Partly supported"; otherwise "Not supported".
3. Outliers (gravity model, patterns not proof): fit OLS with numpy or statsmodels: log(arrivals) ~ log(gdp_origin) + log(gdp_dest) + log(distance_km) + border + common_lang on non-covid years. Store residual = actual log − predicted log on every row. Average the residual per pair over non-covid years. Mark outlier_flag = 'above' for the 10 highest average residuals, 'below' for the 10 lowest, otherwise blank.
4. Rich-to-cheaper: for each origin, the arrivals-weighted average gdp_gap, and the share of its arrivals going to destinations with gdp_gap < 1.
5. Top 15 corridors by 2024 arrivals, with change_vs_2019.

## Save to OUT
- fact_pairs.csv, fact_origin_year.csv, country_map.csv
- analysis_summary.csv with columns metric, value, verdict, note (H1 r pooled, H1 Spearman, H2 slope, H2 median share within 1000 km, model R², number of countries, number of pairs, year range)
- h1_r_by_year.csv, outliers.csv (top 10 above and below, with the average residual), top15_corridors.csv, rich_to_cheaper.csv
- data_dictionary.md: every column of every output file with its definition, unit, source and formula
- coverage_report.csv: for each country, how many years of arrivals data it has as an origin and as a destination
Check that every file is under 10 MB.

## Validation (print the results)
- Row counts after each step, and the number of unique origins, destinations and years. Expect 30, 30 and 15; flag any gaps.
- No negative arrivals, no duplicate keys (origin, destination, year), no origin == destination.
- Spot check: print raw versus clean arrivals for DE→AT 2019, NL→BE 2023 and FR→ES 2015. They must match the raw Eurostat file exactly.
- Missing data stays NaN, never 0. Print the % missing arrivals by year.

## Style
- Use pandas only, plus numpy/statsmodels for the regressions. No hard-coded numbers except the country list.
- After each step print df.head(3) and df.shape.
- End with a short markdown summary: the H1 and H2 verdicts with their numbers, the 3 most interesting outlier pairs with a one-line plausible explanation each (e.g. shared border or language), and any data caveats. Caveat to state: Eurostat counts arrivals at accommodation, so one traveller visiting two hotels counts twice and stays with friends are missed.
