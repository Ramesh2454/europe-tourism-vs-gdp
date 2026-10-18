# Data dictionary

Sources: Eurostat `tour_occ_arnraw` (arrivals at tourist accommodation, all types I551-I553),
World Bank WDI (`NY.GDP.PCAP.PP.CD`, `SP.POP.TOTL`), CEPII GeoDist (`dist_cepii`, `geo_cepii`).
Scope: EU-27 + Norway, Iceland, Switzerland; 2010-2024. Missing values are blank, never 0.
Caveat: Eurostat counts arrivals at accommodation, so one traveller visiting two hotels counts twice
and stays with friends or family are missed. Patterns, not proof.

## fact_pairs.csv - one row per origin x destination x year
| Column | Definition | Unit / formula | Source |
|---|---|---|---|
| origin_iso3, origin_name | Country of residence of the traveller | ISO3 | Eurostat `c_resid` (CH_LI mapped to CHE) |
| dest_iso3, dest_name | Country of the accommodation | ISO3 | Eurostat `geo` (EL mapped to GRC) |
| year | Calendar year | 2010-2024 | Eurostat |
| arrivals | Arrivals at tourist accommodation | count | Eurostat |
| flag | Eurostat flag (e = estimated, p = provisional, b = break, etc.) | text | Eurostat |
| distance_km | Distance between capitals | km | CEPII `distcap` |
| border | Shared land border | 1/0 | CEPII `contig` |
| common_lang | Common official language | 1/0 | CEPII `comlang_off` |
| gdp_origin, gdp_dest | GDP per capita, PPP | current international $ | World Bank |
| pop_origin, pop_dest | Total population | people | World Bank |
| within_1000km | Capital distance under 1,000 km | 1/0 | distance_km < 1000 |
| gdp_gap | Destination wealth relative to origin | ratio | gdp_dest / gdp_origin (< 1 = cheaper destination) |
| origin_lat, origin_lon, dest_lat, dest_lon | Capital coordinates for the flow map | degrees | CEPII `geo_cepii` (cap = 1) |
| covid_flag | COVID year | 1/0 | year in 2020-2022 |
| corridor_share | Pair's share of all arrivals in Europe that year | ratio | arrivals / sum of arrivals in year |
| change_vs_2019 | Change against the same pair in 2019 | ratio | arrivals / arrivals_2019 - 1 |
| residual | Actual vs expected flow (gravity model) | log points | log(arrivals) - predicted; exp(residual) = times expected |
| outlier_flag | Top 10 pairs above / below the model | above / below / blank | ranked on average residual, non-COVID years |

## fact_origin_year.csv - one row per origin x year
| Column | Definition | Unit / formula | Source |
|---|---|---|---|
| origin_iso3, origin_name, year | Origin country and year | | |
| outbound_arrivals | Arrivals in the other 29 countries | count | sum of fact_pairs.arrivals |
| gdp_pc_ppp | GDP per capita, PPP | current international $ | World Bank |
| population | Total population | people | World Bank |
| n_destinations_reported | Destinations with data that year (max 29) | count | gaps lower outbound_arrivals |
| trips_per_1000 | Outbound trips per 1,000 residents | count | outbound_arrivals / population x 1000 |
| share_within_1000km | Share of outbound arrivals to capitals < 1,000 km away | ratio | |
| covid_flag | COVID year | 1/0 | year in 2020-2022 |

## Summary tables
- analysis_summary.csv: H1/H2 statistics and verdicts. H1: r >= 0.5 Supported, 0.3-0.5 Partly, < 0.3 Not.
  H2: slope <= -1 and median share >= 50% Supported; slope < 0 Partly; else Not.
- h1_r_by_year.csv: Pearson r per year (COVID years included).
- outliers.csv: 10 pairs most above and below the gravity model; times_expected = exp(avg_residual).
- top15_corridors.csv: largest pairs in 2024 with corridor_share and change_vs_2019.
- rich_to_cheaper.csv: arrivals-weighted average gdp_gap per origin and share of arrivals to cheaper countries.
- coverage_report.csv: years with data per country and % of origin pairs missing.
- country_map.csv: code mapping across Eurostat, World Bank and CEPII.
