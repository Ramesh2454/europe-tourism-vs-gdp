"""Day 2 finalise: completes the Gemini Colab outputs so they match the BRD.

Reads clean_gemini_v1/ (fact_pairs, fact_origin_year, country_map) and writes clean/.
Adds missing columns, refits the outlier model with population, and rebuilds the
summary tables and data dictionary.

Run from the project folder:  python scripts/day2_finalise.py
"""
import os
import numpy as np
import pandas as pd

SRC, OUT = "clean_gemini_v1", "clean"
COVID = [2020, 2021, 2022]

pairs = pd.read_csv(f"{SRC}/fact_pairs.csv")
orig = pd.read_csv(f"{SRC}/fact_origin_year.csv")
cmap = pd.read_csv(f"{SRC}/country_map.csv")

# CEPII names Belgium "Belgium and Luxembourg"; Luxembourg is its own row.
cmap.loc[cmap.iso3_wb == "BEL", "country_name"] = "Belgium"
names = cmap.set_index("iso3_wb").country_name

# ---------- fact_pairs ----------
p = pairs.rename(columns={"origin": "origin_iso3", "destination": "dest_iso3"})
p.insert(1, "origin_name", p.origin_iso3.map(names))
p.insert(3, "dest_name", p.dest_iso3.map(names))
p["covid_flag"] = p.year.isin(COVID).astype(int)
p["corridor_share"] = p.arrivals / p.groupby("year").arrivals.transform("sum")

base = p[p.year == 2019].set_index(["origin_iso3", "dest_iso3"]).arrivals
p["arrivals_2019"] = p.set_index(["origin_iso3", "dest_iso3"]).index.map(base)
p["change_vs_2019"] = p.arrivals / p.arrivals_2019 - 1
p = p.drop(columns="arrivals_2019")

# Gravity model: population is included so big countries are not flagged just for being big.
X_COLS = ["gdp_origin", "gdp_dest", "pop_origin", "pop_dest", "distance_km"]
fit_rows = (p.covid_flag == 0) & (p.arrivals > 0)

def design(df):
    X = np.log(df[X_COLS].to_numpy())
    X = np.column_stack([np.ones(len(df)), X, df[["border", "common_lang"]].to_numpy()])
    return X

beta, *_ = np.linalg.lstsq(design(p[fit_rows]), np.log(p.loc[fit_rows, "arrivals"]), rcond=None)
pred = design(p) @ beta
y = np.log(p.arrivals.where(p.arrivals > 0))
p["residual"] = y - pred
ss_res = np.nansum((y[fit_rows] - pred[fit_rows]) ** 2)
ss_tot = np.nansum((y[fit_rows] - y[fit_rows].mean()) ** 2)
r2 = 1 - ss_res / ss_tot

pair_res = (p[p.covid_flag == 0].groupby(["origin_iso3", "dest_iso3"]).residual.mean()
            .dropna().sort_values())
above, below = pair_res.tail(10)[::-1], pair_res.head(10)
flag = pd.concat([pd.Series("above", above.index), pd.Series("below", below.index)])
p["outlier_flag"] = p.set_index(["origin_iso3", "dest_iso3"]).index.map(flag)

# ---------- fact_origin_year ----------
within = (p[p.within_1000km == 1].groupby(["origin_iso3", "year"]).arrivals.sum(min_count=1))
reported = p.groupby(["origin_iso3", "year"]).arrivals.count()
o = orig.rename(columns={"origin": "origin_iso3", "arrivals_out": "outbound_arrivals"})
o.insert(1, "origin_name", o.origin_iso3.map(names))
idx = pd.MultiIndex.from_frame(o[["origin_iso3", "year"]])
o["n_destinations_reported"] = idx.map(reported)
# Gemini summed all-missing years to 0 (e.g. Croatia 2010-12); missing must stay blank.
o.loc[o.n_destinations_reported == 0, "outbound_arrivals"] = np.nan
o["trips_per_1000"] = o.outbound_arrivals / o.population * 1000
o["share_within_1000km"] = idx.map(within) / o.outbound_arrivals
o["covid_flag"] = o.year.isin(COVID).astype(int)
o = o.drop(columns="outbound_trips_per_capita")

# ---------- analysis ----------
o_nc = o[o.covid_flag == 0]
h1_r = o_nc.gdp_pc_ppp.corr(o_nc.trips_per_1000)
h1_rho = o_nc.gdp_pc_ppp.rank().corr(o_nc.trips_per_1000.rank())  # Spearman without scipy
h1_by_year = (o.groupby("year").apply(lambda d: d.gdp_pc_ppp.corr(d.trips_per_1000))
              .rename("r").reset_index())

d_rows = fit_rows
h2_slope = np.polyfit(np.log(p.loc[d_rows, "distance_km"]), np.log(p.loc[d_rows, "arrivals"]), 1)[0]
h2_share = o_nc.groupby("origin_iso3").share_within_1000km.mean().median()

def h1_verdict(r):
    return "Supported" if r >= 0.5 else "Partly supported" if r >= 0.3 else "Not supported"

def h2_verdict(slope, share):
    return "Supported" if slope <= -1 and share >= 0.5 else "Partly supported" if slope < 0 else "Not supported"

summary = pd.DataFrame([
    ("H1 r pooled", h1_r, h1_verdict(h1_r), "Pearson r, GDP per capita vs trips per 1,000; excl. 2020-22"),
    ("H1 Spearman", h1_rho, h1_verdict(h1_rho), "Rank correlation, robustness check"),
    ("H2 slope", h2_slope, h2_verdict(h2_slope, h2_share), "Slope of log(arrivals) on log(distance); excl. 2020-22"),
    ("H2 median share within 1000 km", h2_share, h2_verdict(h2_slope, h2_share), "Median across origins of share of arrivals < 1,000 km"),
    ("Outlier model R2", r2, "", "log(arrivals) ~ log GDP pc, log population (both sides), log distance, border, language"),
    ("Countries", p.origin_iso3.nunique(), "", "EU-27 + NO, IS, CH"),
    ("Pairs", p.groupby(["origin_iso3", "dest_iso3"]).ngroups, "", "30 x 29 origin-destination pairs"),
    ("Year range", "2010-2024", "", "2020-2022 flagged as COVID years"),
], columns=["metric", "value", "verdict", "note"])

outliers = (pd.concat([above.rename("avg_residual").reset_index().assign(outlier_flag="above"),
                       below.rename("avg_residual").reset_index().assign(outlier_flag="below")]))
outliers.insert(1, "origin_name", outliers.origin_iso3.map(names))
outliers.insert(3, "dest_name", outliers.dest_iso3.map(names))
outliers["times_expected"] = np.exp(outliers.avg_residual)

top15 = (p[p.year == 2024].nlargest(15, "arrivals")
         [["origin_iso3", "origin_name", "dest_iso3", "dest_name", "arrivals", "corridor_share", "change_vs_2019"]]
         .rename(columns={"arrivals": "arrivals_2024"}))

w = p[p.covid_flag == 0].dropna(subset=["arrivals"])
rich = (w.assign(wg=w.gdp_gap * w.arrivals, cheap=(w.gdp_gap < 1) * w.arrivals)
        .groupby("origin_iso3")[["wg", "cheap", "arrivals"]].sum())
rich = pd.DataFrame({"origin_name": rich.index.map(names),
                     "avg_gdp_gap": rich.wg / rich.arrivals,
                     "cheaper_destination_share": rich.cheap / rich.arrivals}).reset_index()

coverage = (p.dropna(subset=["arrivals"]).groupby("origin_iso3").year.nunique().rename("origin_years").to_frame()
            .join(p.dropna(subset=["arrivals"]).groupby("dest_iso3").year.nunique().rename("destination_years"))
            .join(p.groupby("origin_iso3").arrivals.apply(lambda s: s.isna().mean()).rename("origin_pairs_missing_pct")))
coverage.index.name = "iso3"

# ---------- save ----------
os.makedirs(OUT, exist_ok=True)
out = {"fact_pairs.csv": p, "fact_origin_year.csv": o, "country_map.csv": cmap,
       "analysis_summary.csv": summary, "h1_r_by_year.csv": h1_by_year, "outliers.csv": outliers,
       "top15_corridors.csv": top15, "rich_to_cheaper.csv": rich, "coverage_report.csv": coverage.reset_index()}
for name, df in out.items():
    df.to_csv(f"{OUT}/{name}", index=False)
    print(f"{name:24s} {df.shape}")

DICT = """# Data dictionary

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
"""
with open(f"{OUT}/data_dictionary.md", "w") as f:
    f.write(DICT)

print()
print(summary.to_string(index=False))
print()
print(outliers[["origin_name", "dest_name", "avg_residual", "times_expected", "outlier_flag"]].to_string(index=False))
