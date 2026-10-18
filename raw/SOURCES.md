# Raw data sources

Downloaded 2026-10-10. These files are unchanged originals; cleaning happens in `/scripts`.

| File | Source | Notes |
|---|---|---|
| `eurostat/tour_occ_arnraw.tsv(.gz)` | Eurostat SDMX API, dataset `tour_occ_arnraw` | Annual arrivals at tourist accommodation by country of residence (`c_resid`) and destination (`geo`), 1990–2025. Use `unit=NR`, `nace_r2=I551-I553`. `:` = missing; letters after numbers (e.g. `e`, `p`) are flags. |
| `worldbank/gdp_pc_ppp/API_NY.GDP.PCAP.PP.CD_*.csv` | World Bank WDI, `NY.GDP.PCAP.PP.CD` | GDP per capita, PPP (current international $). Wide format, years as columns. |
| `worldbank/population/API_SP.POP.TOTL_*.csv` | World Bank WDI, `SP.POP.TOTL` | Total population. Wide format. |
| `cepii/dist_cepii/dist_cepii.xls` | CEPII GeoDist | Country pairs (`iso_o`, `iso_d`), `distcap` (km between capitals), `contig` (shared border), `comlang_off` (common official language). |
| `cepii/geo_cepii.xls` | CEPII GeoDist | Country capital latitude/longitude, for the flow map. |

## Code quirks to handle in the mapping table

- Eurostat uses `EL` for Greece and `UK` for the United Kingdom (ISO: `GR`, `GB`).
- Eurostat reports Switzerland as an **origin** only as `CH_LI` (Switzerland + Liechtenstein); as a destination it is `CH`.
- Eurostat aggregates to drop: `EU27_2020`, `EU28`, `EA*`, `EU25`, `EU`, `WORLD`, `INT_*`, `EUR_OTH`, `DOM`, continent codes, etc.
- Eurostat 2025 values are partial; the BRD scope is 2010–2024.
- CEPII uses ISO3 codes; Romania may appear as `ROM` instead of `ROU`.
