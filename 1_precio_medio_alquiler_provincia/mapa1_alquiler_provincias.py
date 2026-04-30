from pathlib import Path
import html
import math

import branca.colormap as cm
import folium
from folium.plugins import Fullscreen, MeasureControl, MiniMap, Search
import geopandas as gpd
import mapclassify
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "datos"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"

MIVAU_URL = "https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv"
NUTS_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson"
LAU_URL = "https://gisco-services.ec.europa.eu/distribution/v2/lau/geojson/LAU_RG_01M_2024_4326.geojson"

RENT_FILE = DATA_DIR / "mivau_alquiler_municipios.csv"
NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"
LAU_FILE = DATA_DIR / "lau_2024_01m.geojson"

PRICE_MEASURES = {
    "PERCENT25": "p25_rent_eur",
    "MEDIANA": "median_rent_eur",
    "PERCENT75": "p75_rent_eur",
}

PROVINCE_BY_NUTS = {
    "ES111": "15",  # A Coruna
    "ES112": "27",
    "ES113": "32",
    "ES114": "36",
    "ES120": "33",
    "ES130": "39",
    "ES211": "01",
    "ES212": "20",
    "ES213": "48",
    "ES220": "31",
    "ES230": "26",
    "ES241": "22",
    "ES242": "44",
    "ES243": "50",
    "ES300": "28",
    "ES411": "05",
    "ES412": "09",
    "ES413": "24",
    "ES414": "34",
    "ES415": "37",
    "ES416": "40",
    "ES417": "42",
    "ES418": "47",
    "ES419": "49",
    "ES421": "02",
    "ES422": "13",
    "ES423": "16",
    "ES424": "19",
    "ES425": "45",
    "ES431": "06",
    "ES432": "10",
    "ES511": "08",
    "ES512": "17",
    "ES513": "25",
    "ES514": "43",
    "ES521": "03",
    "ES522": "12",
    "ES523": "46",
    "ES531": "07",
    "ES532": "07",
    "ES533": "07",
    "ES611": "04",
    "ES612": "11",
    "ES613": "14",
    "ES614": "18",
    "ES615": "21",
    "ES616": "23",
    "ES617": "29",
    "ES618": "41",
    "ES620": "30",
    "ES630": "51",
    "ES640": "52",
    "ES703": "38",
    "ES704": "35",
    "ES705": "35",
    "ES706": "38",
    "ES707": "38",
    "ES708": "35",
    "ES709": "38",
}


def download_file(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=90, headers={"User-Agent": "VD-map-project/1.0"})
    response.raise_for_status()
    target.write_bytes(response.content)


def format_eur(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):,.0f} €".replace(",", ".")


def format_int(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):,.0f}".replace(",", ".")


def clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def read_mivau(year: int | None = None) -> tuple[pd.DataFrame, int]:
    rent = pd.read_csv(
        RENT_FILE,
        sep=";",
        encoding="utf-8-sig",
        dtype={"COD_PROVINCIA": str, "COD_POSTAL": str},
    )
    rent["AÑO"] = rent["AÑO"].astype(int)
    rent["VALOR"] = clean_numeric(rent["VALOR"])

    selected_year = int(rent["AÑO"].max() if year is None else year)
    return rent[rent["AÑO"].eq(selected_year)].copy(), selected_year


def load_municipal_rent(year: int | None = None) -> tuple[pd.DataFrame, int]:
    current, selected_year = read_mivau(year)
    keys = ["COD_PROVINCIA", "PROVINCIA", "COD_POSTAL", "NOMBRE_MUNICIPIO", "TIPO_VIVIENDA"]

    prices = current[
        current["ELEMENTO"].eq("PRECIO") & current["TIPO_MEDIDA"].isin(PRICE_MEASURES)
    ].pivot_table(
        index=keys,
        columns="TIPO_MEDIDA",
        values="VALOR",
        aggfunc="first",
    )
    prices = prices.rename(columns=PRICE_MEASURES).reset_index()

    weights = current[
        current["ELEMENTO"].eq("VIVIENDA") & current["TIPO_MEDIDA"].eq("RECUENTO")
    ][keys + ["VALOR"]].rename(columns={"VALOR": "rent_homes"})

    by_type = prices.merge(weights, on=keys, how="left")
    by_type = by_type.dropna(subset=["median_rent_eur", "rent_homes"])
    by_type = by_type[by_type["rent_homes"].gt(0)].copy()

    for column in PRICE_MEASURES.values():
        by_type[f"{column}_weighted"] = by_type[column] * by_type["rent_homes"]
        by_type[f"{column}_weight"] = by_type["rent_homes"].where(by_type[column].notna(), 0)

    aggregations = {
        "rental_homes": ("rent_homes", "sum"),
        "dwelling_types": ("TIPO_VIVIENDA", "nunique"),
    }
    for column in PRICE_MEASURES.values():
        aggregations[f"{column}_weighted_sum"] = (f"{column}_weighted", "sum")
        aggregations[f"{column}_weight_sum"] = (f"{column}_weight", "sum")

    municipal = (
        by_type.groupby(["COD_PROVINCIA", "PROVINCIA", "COD_POSTAL", "NOMBRE_MUNICIPIO"], as_index=False)
        .agg(**aggregations)
    )

    for column in PRICE_MEASURES.values():
        municipal[column] = municipal[f"{column}_weighted_sum"] / municipal[f"{column}_weight_sum"]

    drop_columns = [
        name
        for column in PRICE_MEASURES.values()
        for name in (f"{column}_weighted_sum", f"{column}_weight_sum")
    ]
    municipal = municipal.drop(columns=drop_columns)
    municipal["iqr_rent_eur"] = municipal["p75_rent_eur"] - municipal["p25_rent_eur"]
    municipal["year"] = selected_year
    municipal["municipality_label"] = municipal["NOMBRE_MUNICIPIO"] + " (" + municipal["PROVINCIA"] + ")"
    return municipal, selected_year


def summarize_by_province(municipal: pd.DataFrame) -> pd.DataFrame:
    work = municipal.copy()
    for column in PRICE_MEASURES.values():
        work[f"{column}_weighted"] = work[column] * work["rental_homes"]
        work[f"{column}_weight"] = work["rental_homes"].where(work[column].notna(), 0)

    aggregations = {
        "rental_homes": ("rental_homes", "sum"),
        "municipalities": ("COD_POSTAL", "nunique"),
        "municipal_min_rent_eur": ("median_rent_eur", "min"),
        "municipal_max_rent_eur": ("median_rent_eur", "max"),
        "municipal_q25_rent_eur": ("median_rent_eur", lambda values: values.quantile(0.25)),
        "municipal_q75_rent_eur": ("median_rent_eur", lambda values: values.quantile(0.75)),
    }
    for column in PRICE_MEASURES.values():
        aggregations[f"{column}_weighted_sum"] = (f"{column}_weighted", "sum")
        aggregations[f"{column}_weight_sum"] = (f"{column}_weight", "sum")

    province = work.groupby(["COD_PROVINCIA", "PROVINCIA"], as_index=False).agg(**aggregations)

    for column in PRICE_MEASURES.values():
        province[column] = province[f"{column}_weighted_sum"] / province[f"{column}_weight_sum"]

    drop_columns = [
        name
        for column in PRICE_MEASURES.values()
        for name in (f"{column}_weighted_sum", f"{column}_weight_sum")
    ]
    province = province.drop(columns=drop_columns)
    province["rent_eur_month"] = province["median_rent_eur"]
    province["iqr_rent_eur"] = province["p75_rent_eur"] - province["p25_rent_eur"]
    province["municipal_spread_eur"] = (
        province["municipal_q75_rent_eur"] - province["municipal_q25_rent_eur"]
    )
    return province


def load_province_geometries() -> gpd.GeoDataFrame:
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])

    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    provinces = provinces[["COD_PROVINCIA", "geometry"]].copy()
    return provinces.to_crs("EPSG:4326")


def standardize_lau_code(series: pd.Series) -> pd.Series:
    extracted = series.astype(str).str.extract(r"(\d{5})", expand=False)
    return extracted.fillna(series.astype(str)).str.zfill(5)


def load_municipality_points(municipal: pd.DataFrame) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    lau = gpd.read_file(LAU_FILE)
    if "CNTR_CODE" in lau.columns:
        lau = lau[lau["CNTR_CODE"].eq("ES")].copy()

    code_column = next(
        (column for column in ["LAU_ID", "LAU_CODE", "COMM_ID", "GISCO_ID"] if column in lau.columns),
        None,
    )
    if code_column is None:
        raise ValueError("No se ha encontrado una columna de codigo municipal en la cartografia LAU.")

    lau["COD_POSTAL"] = standardize_lau_code(lau[code_column])
    lau = lau[["COD_POSTAL", "geometry"]].drop_duplicates("COD_POSTAL").to_crs("EPSG:4326")
    lau["geometry"] = lau.geometry.representative_point()

    points = municipal.merge(lau, on="COD_POSTAL", how="left")
    unmatched = points[points["geometry"].isna()].drop(columns=["geometry"]).copy()
    points = points.dropna(subset=["geometry"]).copy()
    points = gpd.GeoDataFrame(points, geometry="geometry", crs="EPSG:4326")
    return points, unmatched


def build_dataset(year: int | None = None) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame, int]:
    download_file(MIVAU_URL, RENT_FILE)
    download_file(NUTS_URL, NUTS_FILE)
    download_file(LAU_URL, LAU_FILE)

    municipal, selected_year = load_municipal_rent(year)
    provincial = summarize_by_province(municipal)
    provinces = load_province_geometries()
    map_data = provinces.merge(provincial, on="COD_PROVINCIA", how="left")
    municipal_points, unmatched = load_municipality_points(municipal)

    missing = map_data[map_data["rent_eur_month"].isna()]
    if not missing.empty:
        missing_codes = ", ".join(missing["COD_PROVINCIA"].tolist())
        raise ValueError(f"Faltan datos de alquiler para estas provincias: {missing_codes}")

    return map_data, municipal_points, municipal, unmatched, selected_year


def marker_size(values: pd.Series, min_size: float = 8, max_size: float = 58) -> pd.Series:
    max_value = float(values.max())
    if max_value <= 0:
        return pd.Series(min_size, index=values.index)
    max_log = math.log1p(max_value)
    return min_size + (max_size - min_size) * values.apply(lambda value: math.log1p(value) / max_log)


def save_static_map(map_data: gpd.GeoDataFrame, municipal_points: gpd.GeoDataFrame, municipal: pd.DataFrame, year: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(16, 9.8), dpi=180)
    grid = fig.add_gridspec(
        nrows=2,
        ncols=3,
        width_ratios=[1.25, 1.25, 1.0],
        height_ratios=[1, 1],
        wspace=0.2,
        hspace=0.28,
    )
    map_ax = fig.add_subplot(grid[:, :2])
    box_ax = fig.add_subplot(grid[0, 2])
    hist_ax = fig.add_subplot(grid[1, 2])

    map_data.plot(
        column="rent_eur_month",
        ax=map_ax,
        cmap="YlOrBr",
        scheme="Quantiles",
        k=5,
        linewidth=0.5,
        edgecolor="#ffffff",
        legend=True,
        legend_kwds={
            "title": "Provincia (€ / mes)",
            "loc": "upper left",
            "frameon": True,
            "fmt": "{:.0f}",
        },
    )

    point_sizes = marker_size(municipal_points["rental_homes"])
    municipal_points.plot(
        ax=map_ax,
        column="median_rent_eur",
        cmap="viridis",
        markersize=point_sizes,
        alpha=0.78,
        edgecolor="#1b1b1b",
        linewidth=0.12,
    )
    map_ax.set_xlim(-10.2, 5.0)
    map_ax.set_ylim(35.0, 44.5)

    canary_codes = ["35", "38"]
    canary_ax = map_ax.inset_axes([0.035, 0.06, 0.2, 0.2])
    canary_map = map_data[map_data["COD_PROVINCIA"].isin(canary_codes)]
    canary_points = municipal_points[municipal_points["COD_PROVINCIA"].isin(canary_codes)]
    canary_map.plot(
        column="rent_eur_month",
        ax=canary_ax,
        cmap="YlOrBr",
        linewidth=0.45,
        edgecolor="#ffffff",
    )
    canary_points.plot(
        ax=canary_ax,
        column="median_rent_eur",
        cmap="viridis",
        markersize=marker_size(canary_points["rental_homes"], min_size=8, max_size=34),
        alpha=0.8,
        edgecolor="#1b1b1b",
        linewidth=0.12,
    )
    canary_ax.set_xlim(-18.4, -13.1)
    canary_ax.set_ylim(27.55, 29.65)
    canary_ax.set_title("Canarias", fontsize=8.2, pad=2)
    canary_ax.set_xticks([])
    canary_ax.set_yticks([])
    for spine in canary_ax.spines.values():
        spine.set_edgecolor("#8c8c8c")
        spine.set_linewidth(0.8)

    top_provinces = map_data.nlargest(4, "rent_eur_month")
    for _, row in top_provinces.iterrows():
        point = row.geometry.representative_point()
        label = f"{row['PROVINCIA']}\n{row['rent_eur_month']:.0f} €"
        text = map_ax.annotate(
            label,
            xy=(point.x, point.y),
            xycoords=map_ax.transData,
            ha="center",
            va="center",
            fontsize=7.2,
            color="#111111",
        )
        text.set_path_effects(
            [path_effects.withStroke(linewidth=2.5, foreground="white", alpha=0.95)]
        )

    price_min = municipal_points["median_rent_eur"].min()
    price_max = municipal_points["median_rent_eur"].max()
    scalar = plt.cm.ScalarMappable(cmap="viridis", norm=plt.Normalize(price_min, price_max))
    scalar.set_array([])
    colorbar = fig.colorbar(scalar, ax=map_ax, orientation="horizontal", fraction=0.035, pad=0.02)
    colorbar.set_label("Municipios (€ / mes)", fontsize=8.5)
    colorbar.ax.tick_params(labelsize=7.5)

    map_ax.set_title(
        f"Alquiler 2024: media provincial y puntos municipales",
        fontsize=17,
        fontweight="bold",
        pad=13,
    )
    map_ax.set_axis_off()

    province_order = map_data.sort_values("rent_eur_month", ascending=False)["PROVINCIA"].head(12).tolist()
    province_labels = [
        "Valencia"
        if province.startswith("Valencia/")
        else province.replace("Balears, Illes", "Balears").replace("Araba/Álava", "Álava")
        for province in province_order
    ]
    box_data = [
        municipal.loc[municipal["PROVINCIA"].eq(province), "median_rent_eur"].dropna()
        for province in province_order
    ]
    boxplot = box_ax.boxplot(
        box_data,
        vert=False,
        tick_labels=province_labels,
        showfliers=False,
        patch_artist=True,
        medianprops={"color": "#111111", "linewidth": 1.2},
        boxprops={"facecolor": "#9ecae1", "edgecolor": "#225ea8", "linewidth": 0.9},
        whiskerprops={"color": "#225ea8", "linewidth": 0.9},
        capprops={"color": "#225ea8", "linewidth": 0.9},
    )
    for patch in boxplot["boxes"]:
        patch.set_alpha(0.88)
    box_ax.invert_yaxis()
    box_ax.set_title("Distribucion municipal\nprovincias mas caras", fontsize=11.5, fontweight="bold")
    box_ax.set_xlabel("Mediana municipal (€ / mes)", fontsize=8.8)
    box_ax.grid(axis="x", color="#d9d9d9", linewidth=0.6)
    box_ax.tick_params(axis="both", labelsize=7.6)

    national_price = (
        (municipal["median_rent_eur"] * municipal["rental_homes"]).sum()
        / municipal["rental_homes"].sum()
    )
    hist_ax.hist(
        municipal["median_rent_eur"],
        bins=28,
        weights=municipal["rental_homes"],
        color="#f28e2b",
        alpha=0.82,
        edgecolor="white",
        linewidth=0.4,
    )
    hist_ax.axvline(national_price, color="#222222", linestyle="--", linewidth=1.2)
    hist_ax.text(
        national_price,
        hist_ax.get_ylim()[1] * 0.92,
        f" media ponderada\n {national_price:.0f} €",
        fontsize=7.6,
        ha="left",
        va="top",
        color="#222222",
    )
    hist_ax.set_title("Distribucion estatal ponderada\npor viviendas observadas", fontsize=11.5, fontweight="bold")
    hist_ax.set_xlabel("Mediana municipal (€ / mes)", fontsize=8.8)
    hist_ax.set_ylabel("Viviendas observadas", fontsize=8.8)
    hist_ax.grid(axis="y", color="#d9d9d9", linewidth=0.6)
    hist_ax.tick_params(axis="both", labelsize=7.6)

    fig.suptitle(
        "Mapa 1. Precio actual del alquiler y dispersion interna",
        fontsize=20,
        fontweight="bold",
        x=0.44,
        y=0.985,
    )
    fig.text(
        0.02,
        0.012,
        "Fuente: MIVAU, Sistema Estatal de Referencia del Precio del Alquiler; cartografia Eurostat/GISCO NUTS y LAU 2024.",
        fontsize=8.2,
        color="#4a4a4a",
    )
    fig.savefig(OUTPUT_DIR / "mapa1_alquiler_provincias.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa1_alquiler_provincias.pdf", bbox_inches="tight")
    plt.close(fig)


def add_province_layer(web_map: folium.Map, map_data: gpd.GeoDataFrame) -> folium.GeoJson:
    popup_fields = [
        "PROVINCIA",
        "rent_eur_month",
        "p25_rent_eur",
        "p75_rent_eur",
        "iqr_rent_eur",
        "municipal_spread_eur",
        "rental_homes",
        "municipalities",
        "municipal_min_rent_eur",
        "municipal_max_rent_eur",
    ]
    aliases = [
        "Provincia",
        "Media ponderada",
        "P25 ponderado",
        "P75 ponderado",
        "IQR P75-P25",
        "IQR entre municipios",
        "Viviendas observadas",
        "Municipios con dato",
        "Municipio mas barato",
        "Municipio mas caro",
    ]

    return folium.GeoJson(
        map_data,
        name="Detalle provincial",
        style_function=lambda _: {"fillOpacity": 0, "color": "#222222", "weight": 0.35},
        highlight_function=lambda _: {"fillOpacity": 0.08, "color": "#111111", "weight": 1.8},
        tooltip=folium.GeoJsonTooltip(
            fields=["PROVINCIA", "rent_eur_month", "rental_homes", "municipalities"],
            aliases=["Provincia", "Alquiler medio", "Viviendas observadas", "Municipios"],
            localize=True,
            labels=True,
            sticky=False,
        ),
        popup=folium.GeoJsonPopup(
            fields=popup_fields,
            aliases=aliases,
            localize=True,
            labels=True,
            max_width=360,
        ),
    ).add_to(web_map)


def municipal_popup(row: pd.Series) -> str:
    municipality = html.escape(str(row["NOMBRE_MUNICIPIO"]))
    province = html.escape(str(row["PROVINCIA"]))
    return f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.35; min-width: 220px;">
      <strong style="font-size: 13px;">{municipality}</strong><br>
      <span>{province}</span>
      <hr style="margin: 6px 0;">
      <table>
        <tr><td>Mediana</td><td style="text-align:right; padding-left:10px;"><b>{format_eur(row['median_rent_eur'])}</b></td></tr>
        <tr><td>P25</td><td style="text-align:right; padding-left:10px;">{format_eur(row['p25_rent_eur'])}</td></tr>
        <tr><td>P75</td><td style="text-align:right; padding-left:10px;">{format_eur(row['p75_rent_eur'])}</td></tr>
        <tr><td>IQR</td><td style="text-align:right; padding-left:10px;">{format_eur(row['iqr_rent_eur'])}</td></tr>
        <tr><td>Viviendas</td><td style="text-align:right; padding-left:10px;">{format_int(row['rental_homes'])}</td></tr>
      </table>
    </div>
    """


def save_interactive_map(map_data: gpd.GeoDataFrame, municipal_points: gpd.GeoDataFrame, year: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    classifier = mapclassify.Quantiles(map_data["rent_eur_month"], k=5)
    thresholds = [float(map_data["rent_eur_month"].min())] + [float(value) for value in classifier.bins]
    thresholds[0] = max(0, thresholds[0] - 1)

    web_map = folium.Map(
        location=[40.1, -3.7],
        zoom_start=6,
        tiles="cartodbpositron",
        control_scale=True,
    )

    folium.Choropleth(
        geo_data=map_data.to_json(),
        data=map_data,
        columns=["COD_PROVINCIA", "rent_eur_month"],
        key_on="feature.properties.COD_PROVINCIA",
        fill_color="YlOrBr",
        fill_opacity=0.7,
        line_opacity=0.5,
        line_weight=0.7,
        bins=thresholds,
        name="Coropleta provincial",
        legend_name=f"Precio medio ponderado provincial (€), {year}",
    ).add_to(web_map)

    province_layer = add_province_layer(web_map, map_data)

    price_scale = cm.linear.viridis.scale(
        municipal_points["median_rent_eur"].min(),
        municipal_points["median_rent_eur"].max(),
    )
    price_scale.caption = f"Alquiler mediano municipal (€), {year}"
    price_scale.add_to(web_map)

    points_layer = folium.FeatureGroup(
        name="Puntos municipales: precio y viviendas observadas",
        show=True,
    )
    top_markets_layer = folium.FeatureGroup(
        name="Mayores mercados municipales",
        show=False,
    )

    max_homes_log = math.log1p(float(municipal_points["rental_homes"].max()))
    for _, row in municipal_points.iterrows():
        radius = 2.2 + 9.5 * math.log1p(float(row["rental_homes"])) / max_homes_log
        tooltip = (
            f"{row['NOMBRE_MUNICIPIO']} ({row['PROVINCIA']}): "
            f"{row['median_rent_eur']:.0f} €; {row['rental_homes']:.0f} viviendas"
        )
        marker = folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=radius,
            color="#1a1a1a",
            weight=0.35,
            fill=True,
            fill_color=price_scale(float(row["median_rent_eur"])),
            fill_opacity=0.78,
            tooltip=tooltip,
            popup=folium.Popup(municipal_popup(row), max_width=300),
            title=row["municipality_label"],
        )
        marker.add_to(points_layer)

    for _, row in municipal_points.nlargest(35, "rental_homes").iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5.5,
            color="#000000",
            weight=1.5,
            fill=True,
            fill_color="#ffffff",
            fill_opacity=0.15,
            tooltip=f"{row['NOMBRE_MUNICIPIO']}: {row['rental_homes']:.0f} viviendas observadas",
            popup=folium.Popup(municipal_popup(row), max_width=300),
            title=row["municipality_label"],
        ).add_to(top_markets_layer)

    points_layer.add_to(web_map)
    top_markets_layer.add_to(web_map)

    summary_html = f"""
    <div style="
        position: fixed;
        bottom: 28px;
        left: 28px;
        z-index: 9999;
        background: rgba(255, 255, 255, 0.92);
        border: 1px solid #bdbdbd;
        border-radius: 4px;
        padding: 10px 12px;
        font-family: Arial, sans-serif;
        font-size: 12px;
        line-height: 1.35;
        box-shadow: 0 1px 5px rgba(0,0,0,0.18);
    ">
      <strong>Mapa 1 · alquiler {year}</strong><br>
      {format_int(len(municipal_points))} municipios con punto<br>
      Tamano = viviendas observadas<br>
      Color = mediana municipal
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(summary_html))

    Search(
        layer=province_layer,
        search_label="PROVINCIA",
        placeholder="Buscar provincia",
        collapsed=True,
        geom_type="Polygon",
        position="topleft",
    ).add_to(web_map)
    Search(
        layer=points_layer,
        placeholder="Buscar municipio",
        search_zoom=11,
        collapsed=True,
        position="topleft",
    ).add_to(web_map)

    Fullscreen(position="topright").add_to(web_map)
    MiniMap(toggle_display=True, minimized=True, position="bottomright").add_to(web_map)
    MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(web_map)
    folium.LayerControl(collapsed=True).add_to(web_map)
    web_map.save(OUTPUT_DIR / "mapa1_alquiler_provincias_interactivo.html")


def save_tables(
    map_data: gpd.GeoDataFrame,
    municipal_points: gpd.GeoDataFrame,
    municipal: pd.DataFrame,
    unmatched: pd.DataFrame,
    year: int,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    province_columns = [
        "COD_PROVINCIA",
        "PROVINCIA",
        "rent_eur_month",
        "p25_rent_eur",
        "p75_rent_eur",
        "iqr_rent_eur",
        "municipal_spread_eur",
        "rental_homes",
        "municipalities",
        "municipal_min_rent_eur",
        "municipal_max_rent_eur",
    ]
    province_table = map_data[province_columns].sort_values("rent_eur_month", ascending=False).copy()
    province_table["year"] = year
    province_table.to_csv(OUTPUT_DIR / "mapa1_alquiler_provincias_datos.csv", index=False)

    municipal_columns = [
        "COD_PROVINCIA",
        "PROVINCIA",
        "COD_POSTAL",
        "NOMBRE_MUNICIPIO",
        "median_rent_eur",
        "p25_rent_eur",
        "p75_rent_eur",
        "iqr_rent_eur",
        "rental_homes",
        "dwelling_types",
        "year",
    ]
    municipal[municipal_columns].sort_values("median_rent_eur", ascending=False).to_csv(
        OUTPUT_DIR / "mapa1_alquiler_municipios_2024.csv",
        index=False,
    )

    points_table = municipal_points[municipal_columns].copy()
    points_table["lon"] = municipal_points.geometry.x
    points_table["lat"] = municipal_points.geometry.y
    points_table.sort_values("median_rent_eur", ascending=False).to_csv(
        OUTPUT_DIR / "mapa1_alquiler_municipios_puntos_2024.csv",
        index=False,
    )

    if not unmatched.empty:
        unmatched[municipal_columns].sort_values("PROVINCIA").to_csv(
            OUTPUT_DIR / "mapa1_municipios_sin_geometria.csv",
            index=False,
        )


def main() -> None:
    map_data, municipal_points, municipal, unmatched, year = build_dataset()
    save_static_map(map_data, municipal_points, municipal, year)
    save_interactive_map(map_data, municipal_points, year)
    save_tables(map_data, municipal_points, municipal, unmatched, year)

    print(f"Mapa 1 generado con datos de {year}.")
    print(f"Municipios con alquiler: {len(municipal)}.")
    print(f"Municipios con punto en el mapa: {len(municipal_points)}.")
    if not unmatched.empty:
        print(f"Municipios sin geometria LAU: {len(unmatched)}.")
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
