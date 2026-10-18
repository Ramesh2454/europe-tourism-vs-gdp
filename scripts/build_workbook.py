"""Builds the starter Tableau workbook (Page 1 - Wealth / H1) from clean/.

Writes "Europe Tourism vs GDP.twb" in the project folder. Open it in Tableau Desktop,
then finish layout and formatting by hand.

Run from the project folder:  python scripts/build_workbook.py
"""
import os
import uuid

PROJECT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLEAN = os.path.join(PROJECT, "clean")
OUT = os.path.join(PROJECT, "Europe Tourism vs GDP.twb")


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;").replace("\n", "&#10;"))


def uid():
    return "{" + str(uuid.uuid4()).upper() + "}"


# ---------- data sources ----------
# (name, datatype, role, type, caption, default-format)
ORIGIN_COLS = [
    ("origin_iso3", "string", "dimension", "nominal", "Origin ISO3", None),
    ("origin_name", "string", "dimension", "nominal", "Country", None),
    ("year", "integer", "dimension", "ordinal", "Year", "n0"),
    ("outbound_arrivals", "real", "measure", "quantitative", "Outbound Arrivals", "n#,##0"),
    ("gdp_pc_ppp", "real", "measure", "quantitative", "GDP per Capita (PPP)", 'c"$"#,##0'),
    ("population", "real", "measure", "quantitative", "Population", "n#,##0"),
    ("n_destinations_reported", "integer", "measure", "quantitative", "Destinations Reported", "n0"),
    ("trips_per_1000", "real", "measure", "quantitative", "Trips per 1,000 Residents", "n#,##0"),
    ("share_within_1000km", "real", "measure", "quantitative", "Share within 1,000 km", "p0.0%"),
    ("covid_flag", "integer", "dimension", "nominal", "COVID Year", None),
]
PAIR_COLS = [
    ("origin_iso3", "string", "dimension", "nominal", "Origin ISO3", None),
    ("origin_name", "string", "dimension", "nominal", "Origin", None),
    ("dest_iso3", "string", "dimension", "nominal", "Destination ISO3", None),
    ("dest_name", "string", "dimension", "nominal", "Destination", None),
    ("year", "integer", "dimension", "ordinal", "Year", "n0"),
    ("arrivals", "real", "measure", "quantitative", "Arrivals", "n#,##0"),
    ("flag", "string", "dimension", "nominal", "Eurostat Flag", None),
    ("distance_km", "real", "measure", "quantitative", "Distance (km)", "n#,##0"),
    ("border", "integer", "dimension", "nominal", "Shared Border", None),
    ("common_lang", "integer", "dimension", "nominal", "Common Language", None),
    ("gdp_origin", "real", "measure", "quantitative", "GDP pc Origin", 'c"$"#,##0'),
    ("pop_origin", "real", "measure", "quantitative", "Population Origin", "n#,##0"),
    ("gdp_dest", "real", "measure", "quantitative", "GDP pc Destination", 'c"$"#,##0'),
    ("pop_dest", "real", "measure", "quantitative", "Population Destination", "n#,##0"),
    ("within_1000km", "integer", "dimension", "nominal", "Within 1,000 km", None),
    ("gdp_gap", "real", "measure", "quantitative", "GDP Gap (dest / origin)", "n0.00"),
    ("origin_lat", "real", "measure", "quantitative", "Origin Lat", None),
    ("origin_lon", "real", "measure", "quantitative", "Origin Lon", None),
    ("dest_lat", "real", "measure", "quantitative", "Dest Lat", None),
    ("dest_lon", "real", "measure", "quantitative", "Dest Lon", None),
    ("covid_flag", "integer", "dimension", "nominal", "COVID Year", None),
    ("corridor_share", "real", "measure", "quantitative", "Corridor Share", "p0.00%"),
    ("change_vs_2019", "real", "measure", "quantitative", "Change vs 2019", "p0.0%"),
    ("residual", "real", "measure", "quantitative", "Residual (log)", "n0.00"),
    ("outlier_flag", "string", "dimension", "nominal", "Outlier Flag", None),
]
PAIR_ROLES = {"origin_lat": "latitude", "dest_lat": "latitude",
              "origin_lon": "longitude", "dest_lon": "longitude"}

# Calculated fields on fact_origin_year: (name, caption, datatype, role, type, format, formula)
PARAM = "[Parameters].[COVID Years]"
CALCS = [
    ("Keep Year", "Keep Year", "boolean", "dimension", "nominal", None,
     "// Drops 2020-2022 unless the COVID Years parameter says include\n"
     f'{PARAM} = "Include all years" OR [covid_flag] = 0'),
    ("GDP Paired", "GDP (paired)", "real", "measure", "quantitative", 'c"$"#,##0',
     "// GDP only where trips exist, so r uses complete pairs\n"
     "IF NOT ISNULL([trips_per_1000]) THEN [gdp_pc_ppp] END"),
    ("r GDP vs Trips", "r (GDP vs trips)", "real", "measure", "quantitative", "n0.00",
     "// Pearson r of GDP per capita vs trips per 1,000 across all country-years in view (H1)\n"
     "(AVG([GDP Paired] * [trips_per_1000]) - AVG([GDP Paired]) * AVG([trips_per_1000]))\n"
     "/ (STDEVP([GDP Paired]) * STDEVP([trips_per_1000]))"),
    ("H1 Verdict", "H1 Verdict", "string", "measure", "nominal", None,
     "// BRD rule: r >= 0.5 supported, 0.3-0.5 partly, < 0.3 not\n"
     'IF [r GDP vs Trips] >= 0.5 THEN "Supported"\n'
     'ELSEIF [r GDP vs Trips] >= 0.3 THEN "Partly supported"\n'
     'ELSE "Not supported" END'),
    ("Trips per Resident", "Trips per Resident", "real", "measure", "quantitative", "n0.00",
     "// Average outbound trips per resident (easier to read than per 1,000)\n"
     "AVG([trips_per_1000]) / 1000"),
]

DS_O = "federated.originyear0001"
DS_P = "federated.factpairs00001"
REMOTE = {"string": 129, "integer": 20, "real": 5}


def col_xml(c, roles=None):
    name, dt, role, typ, cap, fmt = c
    sr = f" semantic-role='[Geographical].[{roles[name].capitalize()}]'" if roles and name in roles else ""
    f = f" default-format='{esc(fmt)}'" if fmt else ""
    return f"<column caption='{esc(cap)}' datatype='{dt}'{f} name='[{name}]' role='{role}'{sr} type='{typ}' />"


def calc_xml(c):
    name, cap, dt, role, typ, fmt, formula = c
    f = f" default-format='{esc(fmt)}'" if fmt else ""
    return (f"<column caption='{esc(cap)}' datatype='{dt}'{f} name='[{name}]' role='{role}' type='{typ}'>"
            f"<calculation class='tableau' formula='{esc(formula)}' /></column>")


def datasource(ds, caption, filename, cols, calcs=(), roles=None):
    conn = "textscan." + ds.split(".")[1]
    table = filename.replace(".csv", "#csv")
    rel_cols = "".join(f"<column datatype='{c[1]}' name='{c[0]}' ordinal='{i}' />" for i, c in enumerate(cols))
    meta = "".join(
        f"<metadata-record class='column'><remote-name>{c[0]}</remote-name><remote-type>{REMOTE[c[1]]}</remote-type>"
        f"<local-name>[{c[0]}]</local-name><parent-name>[{filename}]</parent-name><remote-alias>{c[0]}</remote-alias>"
        f"<ordinal>{i}</ordinal><local-type>{c[1]}</local-type>"
        f"<aggregation>{'Count' if c[1] == 'string' else 'Sum'}</aggregation><contains-null>true</contains-null>"
        f"</metadata-record>" for i, c in enumerate(cols))
    return f"""
    <datasource caption='{caption}' inline='true' name='{ds}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='{caption}' name='{conn}'>
            <connection class='textscan' directory='{esc(CLEAN)}' filename='{filename}' password='' server='' />
          </named-connection>
        </named-connections>
        <relation connection='{conn}' name='{filename}' table='[{table}]' type='table'>
          <columns character-set='UTF-8' header='yes' locale='en_US' separator=','>{rel_cols}</columns>
        </relation>
        <metadata-records>{meta}</metadata-records>
      </connection>
      <aliases enabled='yes' />
      {''.join(col_xml(c, roles) for c in cols)}
      {''.join(calc_xml(c) for c in calcs)}
    </datasource>"""


PARAMS_DS = f"""
    <datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>
      <aliases enabled='yes' />
      <column caption='COVID Years' datatype='string' name='[COVID Years]' param-domain-type='list' role='measure' type='nominal' value='&quot;Exclude 2020-22&quot;'>
        <calculation class='tableau' formula='&quot;Exclude 2020-22&quot;' />
        <members>
          <member value='&quot;Exclude 2020-22&quot;' />
          <member value='&quot;Include all years&quot;' />
        </members>
      </column>
    </datasource>"""

# ---------- worksheets ----------
D = f"[{DS_O}]"
INST = {  # column-instance name -> (column, derivation, type)
    "none:origin_name:nk": ("origin_name", "None", "nominal"),
    "none:year:ok": ("year", "None", "ordinal"),
    "none:Keep Year:nk": ("Keep Year", "None", "nominal"),
    "avg:gdp_pc_ppp:qk": ("gdp_pc_ppp", "Avg", "quantitative"),
    "avg:trips_per_1000:qk": ("trips_per_1000", "Avg", "quantitative"),
    "ctd:origin_iso3:qk": ("origin_iso3", "CountD", "quantitative"),
    "usr:r GDP vs Trips:qk": ("r GDP vs Trips", "User", "quantitative"),
    "usr:H1 Verdict:nk": ("H1 Verdict", "User", "nominal"),
    "usr:Trips per Resident:qk": ("Trips per Resident", "User", "quantitative"),
}


def deps(instances):
    cols = "".join(col_xml(c) for c in ORIGIN_COLS) + "".join(calc_xml(c) for c in CALCS)
    ci = "".join(f"<column-instance column='[{INST[i][0]}]' derivation='{INST[i][1]}' name='[{i}]' pivot='key' type='{INST[i][2]}' />"
                 for i in sorted(set(instances)))
    return (f"<datasources><datasource name='Parameters' /><datasource caption='fact_origin_year' name='{DS_O}' /></datasources>"
            f"<datasource-dependencies datasource='Parameters'>"
            f"<column caption='COVID Years' datatype='string' name='[COVID Years]' param-domain-type='list' role='measure' type='nominal' value='&quot;Exclude 2020-22&quot;'>"
            f"<calculation class='tableau' formula='&quot;Exclude 2020-22&quot;' /></column></datasource-dependencies>"
            f"<datasource-dependencies datasource='{DS_O}'>{cols}{ci}</datasource-dependencies>")


def filters(keep=True):
    f = (f"<filter class='categorical' column='{D}.[none:year:ok]'>"
         f"<groupfilter function='level-members' level='[none:year:ok]' user:ui-enumeration='all' user:ui-marker='enumerate' />"
         f"</filter>")
    sl = [f"{D}.[none:year:ok]"]
    if keep:
        f += (f"<filter class='categorical' column='{D}.[none:Keep Year:nk]'>"
              f"<groupfilter function='member' level='[none:Keep Year:nk]' member='true' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />"
              f"</filter>")
        sl.append(f"{D}.[none:Keep Year:nk]")
    return f, "<slices>" + "".join(f"<column>{s}</column>" for s in sl) + "</slices>"


def worksheet(name, title, mark, rows, cols, enc, instances, keep=True, extra_pane="", sort="", labels=False, axis_titles=()):
    flt, slices = filters(keep)
    # Filtered fields must also be declared as column-instances, or Tableau drops the filter.
    instances = list(instances) + ["none:year:ok"] + (["none:Keep Year:nk"] if keep else [])
    lab = "<style><style-rule element='mark'><format attr='mark-labels-show' value='true' /></style-rule></style>" if labels else ""
    ax = "".join(f"<format attr='title' class='0' field='{D}.[{f}]' scope='{s}' value='{esc(v)}' />" for f, s, v in axis_titles)
    style = f"<style><style-rule element='axis'>{ax}</style-rule></style>" if ax else "<style />"
    return f"""
    <worksheet name='{esc(name)}'>
      <layout-options><title><formatted-text><run>{esc(title)}</run></formatted-text></title></layout-options>
      <table>
        <view>{deps(instances)}{flt}{sort}{slices}<aggregation value='true' /></view>
        {style}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view><breakdown value='auto' /></view>
            <mark class='{mark}' />
            <encodings>{enc}</encodings>
            {extra_pane}{lab}
          </pane>
        </panes>
        <rows>{rows}</rows>
        <cols>{cols}</cols>
      </table>
    </worksheet>"""


def text_tile(name, title, inst):
    return worksheet(name, title, "Text", "", "", f"<text column='{D}.[{inst}]' />", [inst])


sheets = [
    worksheet("H1 Scatter", "Richer countries travel more: GDP per capita vs outbound trips per 1,000 residents",
              "Circle", f"{D}.[avg:trips_per_1000:qk]", f"{D}.[avg:gdp_pc_ppp:qk]",
              f"<lod column='{D}.[none:origin_name:nk]' /><text column='{D}.[none:origin_name:nk]' />",
              ["avg:trips_per_1000:qk", "avg:gdp_pc_ppp:qk", "none:origin_name:nk"],
              extra_pane="<trendline enable-confidence-bands='false' enable-instant-analytics='false' enabled='true' exclude-color='true' exclude-intercept='false' fit='linear' />",
              labels=True,
              axis_titles=[("avg:gdp_pc_ppp:qk", "cols", "GDP per capita, PPP (international $)"),
                           ("avg:trips_per_1000:qk", "rows", "Outbound trips per 1,000 residents")]),
    text_tile("KPI r", "r (GDP vs trips)", "usr:r GDP vs Trips:qk"),
    text_tile("KPI Verdict", "H1 verdict", "usr:H1 Verdict:nk"),
    text_tile("KPI Avg Trips", "Trips per resident", "usr:Trips per Resident:qk"),
    text_tile("KPI Countries", "Countries", "ctd:origin_iso3:qk"),
    worksheet("r by Year", "Wealth-travel link by year (r); dip = COVID 2020-22",
              "Line", f"{D}.[usr:r GDP vs Trips:qk]", f"{D}.[none:year:ok]", "",
              ["usr:r GDP vs Trips:qk", "none:year:ok"], keep=False),
    worksheet("Trips Ranking", "Outbound trips per 1,000 residents (colour = GDP per capita)",
              "Bar", f"{D}.[none:origin_name:nk]", f"{D}.[avg:trips_per_1000:qk]",
              f"<color column='{D}.[avg:gdp_pc_ppp:qk]' />",
              ["none:origin_name:nk", "avg:trips_per_1000:qk", "avg:gdp_pc_ppp:qk"],
              sort=f"<sort class='computed' column='{D}.[none:origin_name:nk]' direction='DESC' using='{D}.[avg:trips_per_1000:qk]' />"),
]

CARDS = """<cards>
        <edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge>
        <edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip><strip size='31'><card type='title' /></strip></edge>
      </cards>"""
names = ["H1 Scatter", "KPI r", "KPI Verdict", "KPI Avg Trips", "KPI Countries", "r by Year", "Trips Ranking"]
MAX = " maximized='true'"
windows = "".join(
    f"<window class='worksheet'{MAX if i == 0 else ''} name='{esc(n)}'>{CARDS}</window>"
    for i, n in enumerate(names))

xml = f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook source-build='2026.2' source-platform='mac' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <preferences />
  <datasources>{PARAMS_DS}
    {datasource(DS_O, 'fact_origin_year', 'fact_origin_year.csv', ORIGIN_COLS, CALCS)}
    {datasource(DS_P, 'fact_pairs', 'fact_pairs.csv', PAIR_COLS, roles=PAIR_ROLES)}
  </datasources>
  <worksheets>{''.join(sheets)}
  </worksheets>
  <windows source-height='30'>{windows}</windows>
</workbook>
"""
with open(OUT, "w", encoding="utf-8") as f:
    f.write(xml)
print("wrote", OUT)
