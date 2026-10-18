# Data Dictionary

## fact_pairs.csv
- `origin`: Origin country ISO3 code (source: World Bank)
- `destination`: Destination country ISO3 code (source: World Bank)
- `year`: Year of observations 2010-2024
- `arrivals`: Number of arrivals at tourist accommodation establishments (source: Eurostat)
- `flag`: Quality flags or footnotes (source: Eurostat)
- `distance_km`: Geographical distance between capitals (source: CEPII)
- `border`: Binary indicator for shared land border (source: CEPII)
- `common_lang`: Binary indicator for common official language (source: CEPII)
- `gdp_origin`: GDP per capita (PPP) of the origin country (source: World Bank)
- `pop_origin`: Total population of the origin country (source: World Bank)
- `gdp_dest`: GDP per capita (PPP) of the destination country (source: World Bank)
- `pop_dest`: Total population of the destination country (source: World Bank)
- `within_1000km`: Indicator if the capital distance is under 1000km
- `gdp_gap`: Ratio of destination GDP pc to origin GDP pc
- `origin_lat`, `origin_lon`: Location coordinates of origin capital city (source: CEPII)
- `dest_lat`, `dest_lon`: Location coordinates of destination capital city (source: CEPII)
