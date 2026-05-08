from __future__ import annotations

import json
from pathlib import Path
import os
import sys
import unicodedata


BASE_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / ".matplotlib"))

proj_data = Path(sys.prefix) / "share" / "proj"
if proj_data.exists():
    os.environ.setdefault("PROJ_DATA", str(proj_data))
    os.environ.setdefault("PROJ_LIB", str(proj_data))

import folium
from folium import plugins
import geopandas as gpd
import mapclassify
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import pandas as pd
import requests
from branca.element import MacroElement, Template


DATA_DIR = BASE_DIR / "datos"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"

MIVAU_URL = "https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv"
BROADBAND_URL = (
    "https://digital.gob.es/content/dam/portal-mtdfp/avance-digital/"
    "telecomunicacion-e-infraestructuras-digitales/areas_interes/banda-ancha/"
    "cobertura/documents/cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx"
)
NUTS_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson"

RENT_FILE = DATA_DIR / "mivau_alquiler_municipios.csv"
BROADBAND_FILE = DATA_DIR / "cobertura_ba_espana_2021_2024.xlsx"
NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"
CLIMATE_FILE = DATA_DIR / "nasa_power_temperatura_estacional_provincias_1995_2024.csv"

SHEET_NAME = "Provincia_%hogar"
COVERAGE_COLUMN_2024 = "Cob. 1Gbps descarga condiciones maxima demanda\n(junio 2024)"
BASELINE_YEAR = 2019

WEIGHTS = {
    "rent_score_low_price": 0.35,
    "rent_growth_score": 0.20,
    "availability_score": 0.15,
    "connectivity_score": 0.20,
    "climate_score": 0.10,
}

COMPONENTS = [
    ("Alquiler bajo", "rent_contribution", "#2a9d8f"),
    ("Subida moderada", "growth_contribution", "#577590"),
    ("Disponibilidad", "availability_contribution", "#f4a261"),
    ("Conectividad", "connectivity_contribution", "#277da1"),
    ("Confort climatico", "climate_contribution", "#90be6d"),
]

INDEX_PALETTE = ["#8c2d04", "#cc4c02", "#fdb863", "#80cdc1", "#018571"]
SCORE_BINS = [0, 20, 40, 60, 80, 100]
INDEX_CLASS_LABELS = [
    "Quintil 1 - equilibrio bajo",
    "Quintil 2 - equilibrio medio-bajo",
    "Quintil 3 - equilibrio medio",
    "Quintil 4 - equilibrio alto",
    "Quintil 5 - mejor equilibrio",
]

PROVINCE_BY_NUTS = {
    "ES111": "15",
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

PROVINCE_CODE_BY_NAME = {
    "araba/alava": "01",
    "albacete": "02",
    "alicante/alacant": "03",
    "almeria": "04",
    "avila": "05",
    "badajoz": "06",
    "balears, illes": "07",
    "illes balears": "07",
    "barcelona": "08",
    "burgos": "09",
    "caceres": "10",
    "cadiz": "11",
    "castellon/castello": "12",
    "ciudad real": "13",
    "cordoba": "14",
    "coruna, a": "15",
    "a coruna": "15",
    "cuenca": "16",
    "girona": "17",
    "granada": "18",
    "guadalajara": "19",
    "gipuzkoa": "20",
    "huelva": "21",
    "huesca": "22",
    "jaen": "23",
    "leon": "24",
    "lleida": "25",
    "rioja, la": "26",
    "la rioja": "26",
    "lugo": "27",
    "madrid": "28",
    "malaga": "29",
    "murcia": "30",
    "navarra": "31",
    "ourense": "32",
    "asturias": "33",
    "palencia": "34",
    "palmas, las": "35",
    "las palmas": "35",
    "pontevedra": "36",
    "salamanca": "37",
    "santa cruz de tenerife": "38",
    "cantabria": "39",
    "segovia": "40",
    "sevilla": "41",
    "soria": "42",
    "tarragona": "43",
    "teruel": "44",
    "toledo": "45",
    "valencia/valencia": "46",
    "valencia": "46",
    "valladolid": "47",
    "bizkaia": "48",
    "zamora": "49",
    "zaragoza": "50",
    "ceuta": "51",
    "melilla": "52",
}


def download_file(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    target.write_bytes(response.content)


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.strip().lower()


def normalize_columns(columns: pd.Index) -> dict[str, str]:
    return {
        column: unicodedata.normalize("NFKD", str(column))
        .encode("ascii", "ignore")
        .decode("ascii")
        for column in columns
    }


def to_percent(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.dropna().max() <= 1.5:
        values = values * 100
    return values


def format_int(value: float) -> str:
    return f"{int(round(value)):,}".replace(",", ".")


def format_score(value: float) -> str:
    return f"{float(value):.1f}"


def rescale_0_100(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    clean = pd.to_numeric(series, errors="coerce")
    minimum = clean.min()
    maximum = clean.max()
    if pd.isna(minimum) or pd.isna(maximum) or maximum == minimum:
        return pd.Series(50.0, index=series.index)

    score = (clean - minimum) / (maximum - minimum) * 100
    if not higher_is_better:
        score = 100 - score
    return score.clip(0, 100)


def build_quantile_bins(values: pd.Series, k: int = 5) -> list[float]:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    classifier = mapclassify.Quantiles(clean, k=k)
    bins = [float(clean.min())] + [float(value) for value in classifier.bins]
    bins[0] -= 0.01

    for index in range(1, len(bins)):
        if bins[index] <= bins[index - 1]:
            bins[index] = bins[index - 1] + 0.01
    return bins


def color_for_bins(value: float | int | None, bins: list[float], colors: list[str]) -> str:
    if value is None or pd.isna(value):
        return "#bdbdbd"

    numeric_value = float(value)
    for index, upper in enumerate(bins[1:]):
        is_last = index == len(colors) - 1
        if numeric_value <= upper or is_last:
            return colors[index]
    return colors[-1]


def label_for_bins(value: float, bins: list[float]) -> str:
    for index, upper in enumerate(bins[1:]):
        is_last = index == len(INDEX_CLASS_LABELS) - 1
        if float(value) <= upper or is_last:
            return INDEX_CLASS_LABELS[index]
    return INDEX_CLASS_LABELS[-1]


def build_bin_labels(bins: list[float]) -> list[str]:
    labels = []
    for index in range(len(bins) - 1):
        lower = bins[index]
        upper = bins[index + 1]
        if index == 0:
            labels.append(f"<= {upper:.1f}")
        elif index == len(bins) - 2:
            labels.append(f"> {lower:.1f}")
        else:
            labels.append(f"{lower:.1f} - {upper:.1f}")
    return labels


def load_province_geometries() -> gpd.GeoDataFrame:
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])

    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    provinces = provinces[["COD_PROVINCIA", "geometry"]].copy()
    return provinces.to_crs("EPSG:4326")


def load_mivau() -> pd.DataFrame:
    rent = pd.read_csv(
        RENT_FILE,
        sep=";",
        encoding="utf-8-sig",
        dtype={"COD_PROVINCIA": str, "COD_POSTAL": str},
    )
    rent["ANO"] = rent["AÑO"].astype(int)
    rent["VALOR"] = pd.to_numeric(
        rent["VALOR"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    return rent


def aggregate_rent_by_year(rent: pd.DataFrame, year: int) -> pd.DataFrame:
    current = rent[rent["ANO"].eq(year)].copy()

    price = current[
        current["ELEMENTO"].eq("PRECIO") & current["TIPO_MEDIDA"].eq("MEDIANA")
    ][
        [
            "COD_PROVINCIA",
            "PROVINCIA",
            "COD_POSTAL",
            "NOMBRE_MUNICIPIO",
            "TIPO_VIVIENDA",
            "VALOR",
        ]
    ].rename(columns={"VALOR": "median_rent_eur"})

    weights = current[
        current["ELEMENTO"].eq("VIVIENDA") & current["TIPO_MEDIDA"].eq("RECUENTO")
    ][
        [
            "COD_PROVINCIA",
            "COD_POSTAL",
            "NOMBRE_MUNICIPIO",
            "TIPO_VIVIENDA",
            "VALOR",
        ]
    ].rename(columns={"VALOR": "rental_homes"})

    merged = price.merge(
        weights,
        on=["COD_PROVINCIA", "COD_POSTAL", "NOMBRE_MUNICIPIO", "TIPO_VIVIENDA"],
        how="left",
    ).dropna(subset=["median_rent_eur", "rental_homes"])
    merged = merged[merged["rental_homes"].gt(0)]
    merged["weighted_price"] = merged["median_rent_eur"] * merged["rental_homes"]

    summary = (
        merged.groupby(["COD_PROVINCIA", "PROVINCIA"], as_index=False)
        .agg(
            total_weighted_price=("weighted_price", "sum"),
            rental_homes=("rental_homes", "sum"),
            municipalities=("COD_POSTAL", "nunique"),
        )
    )
    summary["rent_eur_month"] = summary["total_weighted_price"] / summary["rental_homes"]
    summary["year"] = year
    return summary.drop(columns=["total_weighted_price"])


def load_rent_metrics() -> tuple[pd.DataFrame, int]:
    rent = load_mivau()
    current_year = int(rent["ANO"].max())
    current = aggregate_rent_by_year(rent, current_year).rename(
        columns={"PROVINCIA": "province_name"}
    )

    yearly_frames = []
    for year in sorted(rent["ANO"].unique()):
        if BASELINE_YEAR <= year < current_year:
            yearly = aggregate_rent_by_year(rent, int(year))
            yearly_frames.append(
                yearly[
                    [
                        "COD_PROVINCIA",
                        "rent_eur_month",
                        "year",
                    ]
                ].rename(
                    columns={
                        "rent_eur_month": "baseline_rent_eur_month",
                        "year": "baseline_year",
                    }
                )
            )

    baseline = (
        pd.concat(yearly_frames, ignore_index=True)
        .sort_values(["COD_PROVINCIA", "baseline_year"])
        .groupby("COD_PROVINCIA", as_index=False)
        .first()
    )
    summary = current.merge(baseline, on="COD_PROVINCIA", how="left")
    years_between = current_year - summary["baseline_year"]
    summary["rent_growth_total_pct"] = (
        (summary["rent_eur_month"] / summary["baseline_rent_eur_month"] - 1) * 100
    )
    summary["rent_growth_annual_pct"] = (
        (summary["rent_eur_month"] / summary["baseline_rent_eur_month"])
        ** (1 / years_between)
        - 1
    ) * 100
    summary.loc[years_between.le(0), ["rent_growth_total_pct", "rent_growth_annual_pct"]] = pd.NA
    summary["has_growth_history"] = summary["rent_growth_annual_pct"].notna()
    return summary, current_year


def load_broadband_by_province() -> pd.DataFrame:
    broadband = pd.read_excel(BROADBAND_FILE, sheet_name=SHEET_NAME)
    broadband = broadband.rename(columns=normalize_columns(broadband.columns))
    broadband["COD_PROVINCIA"] = broadband["Provincia"].map(
        lambda value: PROVINCE_CODE_BY_NAME.get(normalize_text(value))
    )

    missing_codes = broadband[broadband["COD_PROVINCIA"].isna()]["Provincia"].tolist()
    if missing_codes:
        raise ValueError(f"No se pudo asignar codigo INE a estas provincias: {missing_codes}")

    summary = broadband[
        [
            "COD_PROVINCIA",
            "Comunidad Autonoma",
            "Provincia",
            "Habitantes",
            "Hogares",
            COVERAGE_COLUMN_2024,
        ]
    ].rename(
        columns={
            "Comunidad Autonoma": "ccaa",
            "Provincia": "broadband_province_name",
            "Habitantes": "population",
            "Hogares": "households",
            COVERAGE_COLUMN_2024: "coverage_1gbps_2024_pct",
        }
    )
    summary["population"] = pd.to_numeric(summary["population"], errors="coerce")
    summary["households"] = pd.to_numeric(summary["households"], errors="coerce")
    summary["coverage_1gbps_2024_pct"] = to_percent(summary["coverage_1gbps_2024_pct"])
    return summary


def load_climate_by_province() -> pd.DataFrame:
    if not CLIMATE_FILE.exists():
        raise FileNotFoundError(
            "No se encontro la cache climatica. Ejecuta primero el mapa 5 o coloca "
            f"el archivo en {CLIMATE_FILE}."
        )

    climate = pd.read_csv(CLIMATE_FILE, dtype={"COD_PROVINCIA": str})
    comfort_target = 17.0
    if "climate_comfort_score" not in climate.columns:
        comfort_gap = (climate["annual_mean_c"] - comfort_target).abs()
        climate["climate_comfort_score"] = 100 * (1 - comfort_gap / comfort_gap.max())

    return climate[
        [
            "COD_PROVINCIA",
            "annual_mean_c",
            "summer_c",
            "winter_c",
            "climate_comfort_score",
        ]
    ].copy()


def add_geographic_metrics(map_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    data = map_data.copy()
    projected = data.to_crs("EPSG:3035")
    points = gpd.GeoSeries(projected.geometry.representative_point(), crs=projected.crs)
    points_wgs84 = points.to_crs("EPSG:4326")
    data["label_lon"] = points_wgs84.x
    data["label_lat"] = points_wgs84.y
    data["area_km2"] = (projected.area / 1_000_000).round(1)
    return data


def add_scores(data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    scored = data.copy()
    scored["rental_homes_per_1000_households"] = (
        scored["rental_homes"] / scored["households"] * 1000
    )
    scored["rent_score_low_price"] = rescale_0_100(
        scored["rent_eur_month"], higher_is_better=False
    )
    scored["rent_growth_score"] = rescale_0_100(
        scored["rent_growth_annual_pct"], higher_is_better=False
    ).fillna(50)
    scored["availability_score"] = rescale_0_100(
        scored["rental_homes_per_1000_households"], higher_is_better=True
    )
    scored["connectivity_score"] = scored["coverage_1gbps_2024_pct"].clip(0, 100)
    scored["climate_score"] = scored["climate_comfort_score"].clip(0, 100)

    scored["rent_contribution"] = scored["rent_score_low_price"] * WEIGHTS["rent_score_low_price"]
    scored["growth_contribution"] = scored["rent_growth_score"] * WEIGHTS["rent_growth_score"]
    scored["availability_contribution"] = (
        scored["availability_score"] * WEIGHTS["availability_score"]
    )
    scored["connectivity_contribution"] = (
        scored["connectivity_score"] * WEIGHTS["connectivity_score"]
    )
    scored["climate_contribution"] = scored["climate_score"] * WEIGHTS["climate_score"]

    scored["tech_destination_index"] = sum(scored[column] for _, column, _ in COMPONENTS)
    scored["rank_tech"] = (
        scored["tech_destination_index"].rank(method="min", ascending=False).astype(int)
    )
    return scored


def add_labels(data: gpd.GeoDataFrame, bins: list[float], current_year: int) -> gpd.GeoDataFrame:
    labelled = data.copy()
    labelled["index_color"] = labelled["tech_destination_index"].map(
        lambda value: color_for_bins(value, bins, INDEX_PALETTE)
    )
    labelled["index_class"] = labelled["tech_destination_index"].map(
        lambda value: label_for_bins(value, bins)
    )
    labelled["rent_growth_annual_label"] = labelled["rent_growth_annual_pct"].map(
        lambda value: "sin historico comparable"
        if pd.isna(value)
        else f"{float(value):.1f}% anual"
    )
    labelled["rent_baseline_label"] = labelled.apply(
        lambda row: "sin historico comparable"
        if pd.isna(row["baseline_year"])
        else f"{int(row['baseline_year'])}-{current_year}",
        axis=1,
    )
    labelled["recommendation"] = labelled["rank_tech"].map(
        lambda rank: "Destino muy competitivo"
        if rank <= 10
        else ("Buen equilibrio general" if rank <= 25 else "Revisar trade-offs")
    )

    numeric_columns = [
        "rent_eur_month",
        "baseline_rent_eur_month",
        "rent_growth_total_pct",
        "rent_growth_annual_pct",
        "rental_homes_per_1000_households",
        "coverage_1gbps_2024_pct",
        "annual_mean_c",
        "climate_comfort_score",
        "rent_score_low_price",
        "rent_growth_score",
        "availability_score",
        "connectivity_score",
        "climate_score",
        "rent_contribution",
        "growth_contribution",
        "availability_contribution",
        "connectivity_contribution",
        "climate_contribution",
        "tech_destination_index",
    ]
    labelled[numeric_columns] = labelled[numeric_columns].round(2)
    return labelled


def build_dataset() -> tuple[gpd.GeoDataFrame, int, list[float]]:
    download_file(MIVAU_URL, RENT_FILE)
    download_file(BROADBAND_URL, BROADBAND_FILE)
    download_file(NUTS_URL, NUTS_FILE)

    provinces = load_province_geometries()
    rent, current_year = load_rent_metrics()
    broadband = load_broadband_by_province()
    climate = load_climate_by_province()

    map_data = (
        provinces.merge(rent, on="COD_PROVINCIA", how="left")
        .merge(broadband, on="COD_PROVINCIA", how="left")
        .merge(climate, on="COD_PROVINCIA", how="left")
    )

    required_columns = [
        "rent_eur_month",
        "rental_homes",
        "households",
        "coverage_1gbps_2024_pct",
        "climate_comfort_score",
    ]
    missing = map_data[map_data[required_columns].isna().any(axis=1)]
    if not missing.empty:
        missing_codes = ", ".join(missing["COD_PROVINCIA"].tolist())
        raise ValueError(f"Faltan indicadores para estas provincias: {missing_codes}")

    map_data = add_geographic_metrics(map_data)
    map_data = add_scores(map_data)
    bins = build_quantile_bins(map_data["tech_destination_index"], k=5)
    map_data = add_labels(map_data, bins, current_year)
    return map_data, current_year, bins


def plot_canary_inset(
    map_ax: plt.Axes,
    map_data: gpd.GeoDataFrame,
    top_labels: gpd.GeoDataFrame,
) -> None:
    canary_codes = ["35", "38"]
    canary_map = map_data[map_data["COD_PROVINCIA"].isin(canary_codes)]
    if canary_map.empty:
        return

    canary_ax = map_ax.inset_axes([0.035, 0.055, 0.22, 0.19])
    canary_map.plot(
        ax=canary_ax,
        color=canary_map["index_color"],
        linewidth=0.45,
        edgecolor="#ffffff",
    )
    canary_map.boundary.plot(ax=canary_ax, color="#575757", linewidth=0.16, alpha=0.6)

    selected_canary = top_labels[top_labels["COD_PROVINCIA"].isin(canary_codes)]
    for _, row in selected_canary.iterrows():
        text = canary_ax.annotate(
            f"#{int(row['rank_tech'])} {row['province_name']}\n{row['tech_destination_index']:.1f}",
            xy=(row["label_lon"], row["label_lat"]),
            ha="center",
            va="center",
            fontsize=5.9,
            color="#111111",
            zorder=5,
        )
        text.set_path_effects(
            [path_effects.withStroke(linewidth=2.1, foreground="white", alpha=0.96)]
        )

    canary_ax.set_xlim(-18.4, -13.1)
    canary_ax.set_ylim(27.55, 29.65)
    canary_ax.set_title("Canarias", fontsize=8.2, pad=2)
    canary_ax.set_xticks([])
    canary_ax.set_yticks([])
    for spine in canary_ax.spines.values():
        spine.set_edgecolor("#8c8c8c")
        spine.set_linewidth(0.8)


def save_static_map(map_data: gpd.GeoDataFrame, current_year: int, bins: list[float]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(16, 9.8), dpi=180)
    grid = fig.add_gridspec(
        3,
        3,
        width_ratios=[1.25, 1.25, 0.95],
        height_ratios=[0.42, 1, 1],
        wspace=0.18,
        hspace=0.36,
    )
    map_ax = fig.add_subplot(grid[:, :2])
    summary_ax = fig.add_subplot(grid[0, 2])
    rank_ax = fig.add_subplot(grid[1, 2])
    breakdown_ax = fig.add_subplot(grid[2, 2])

    map_data.plot(
        ax=map_ax,
        color=map_data["index_color"],
        linewidth=0.42,
        edgecolor="#ffffff",
    )
    map_data.boundary.plot(ax=map_ax, color="#575757", linewidth=0.14, alpha=0.55)

    top_labels = map_data.nsmallest(8, "rank_tech")
    top_labels_main = top_labels[~top_labels["COD_PROVINCIA"].isin(["35", "38"])]
    for _, row in top_labels_main.iterrows():
        text = map_ax.annotate(
            f"#{int(row['rank_tech'])} {row['province_name']}\n{row['tech_destination_index']:.1f}",
            xy=(row["label_lon"], row["label_lat"]),
            ha="center",
            va="center",
            fontsize=6.7,
            color="#111111",
            zorder=5,
        )
        text.set_path_effects(
            [path_effects.withStroke(linewidth=2.4, foreground="white", alpha=0.96)]
        )

    map_ax.set_xlim(-10.2, 5.0)
    map_ax.set_ylim(35.0, 44.5)
    legend_handles = [
        mpatches.Patch(facecolor=color, edgecolor="#666666", label=label)
        for color, label in zip(INDEX_PALETTE, build_bin_labels(bins))
    ]
    map_ax.legend(
        handles=legend_handles,
        title="Indice final",
        loc="lower right",
        fontsize=7.7,
        title_fontsize=8.8,
        frameon=True,
        framealpha=0.96,
    )
    map_ax.set_title(
        "Equilibrio provincial entre vivienda, conectividad y confort",
        fontsize=16.2,
        fontweight="bold",
        pad=12,
    )
    map_ax.set_axis_off()
    plot_canary_inset(map_ax, map_data, top_labels)

    summary_ax.set_axis_off()
    winner = map_data.nsmallest(1, "rank_tech").iloc[0]
    no_history = int((~map_data["has_growth_history"]).sum())
    summary_ax.text(0.0, 0.98, "Lectura rapida", fontsize=11, fontweight="bold", va="top")
    summary_ax.text(
        0.0,
        0.58,
        f"#{int(winner['rank_tech'])} {winner['province_name']}",
        fontsize=18,
        fontweight="bold",
    )
    summary_ax.text(
        0.0,
        0.35,
        f"{winner['tech_destination_index']:.1f} puntos de indice final",
        fontsize=9,
        color="#333333",
    )
    summary_ax.text(
        0.0,
        0.08,
        f"Pesos: 35 alquiler, 20 evolucion, 15 disponibilidad, 20 conectividad, 10 clima. "
        f"{no_history} provincias sin historico comparable de alquiler.",
        fontsize=8.1,
        color="#444444",
        wrap=True,
    )

    ranking = map_data.nsmallest(10, "rank_tech").sort_values("tech_destination_index")
    rank_ax.barh(
        ranking["province_name"],
        ranking["tech_destination_index"],
        color=ranking["index_color"],
        edgecolor="#555555",
        linewidth=0.35,
    )
    for _, row in ranking.iterrows():
        rank_ax.text(
            row["tech_destination_index"] + 0.35,
            row["province_name"],
            f"{row['tech_destination_index']:.1f}",
            va="center",
            fontsize=7.4,
            color="#333333",
        )
    rank_ax.set_xlim(0, max(82, map_data["tech_destination_index"].max() + 7))
    rank_ax.set_title("Top 10 destinos", fontsize=11, fontweight="bold")
    rank_ax.set_xlabel("Indice final 0-100", fontsize=8.5)
    rank_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    rank_ax.tick_params(axis="both", labelsize=8)

    top_breakdown = map_data.nsmallest(8, "rank_tech").sort_values("tech_destination_index")
    left = pd.Series(0.0, index=top_breakdown.index)
    for label, column, color in COMPONENTS:
        breakdown_ax.barh(
            top_breakdown["province_name"],
            top_breakdown[column],
            left=left,
            label=label,
            color=color,
            edgecolor="white",
            linewidth=0.25,
        )
        left = left + top_breakdown[column]
    breakdown_ax.set_xlim(0, 100)
    breakdown_ax.set_title("Desglose ponderado del top 8", fontsize=11, fontweight="bold")
    breakdown_ax.set_xlabel("Aportacion al indice", fontsize=8.5)
    breakdown_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    breakdown_ax.tick_params(axis="both", labelsize=8)
    breakdown_ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.42),
        ncol=2,
        fontsize=7.1,
        frameon=False,
    )

    for side_ax in [rank_ax, breakdown_ax]:
        for spine in ["top", "right", "left"]:
            side_ax.spines[spine].set_visible(False)

    fig.suptitle(
        f"Mapa 6. Indice final de destino residencial tech ({current_year})",
        fontsize=20,
        fontweight="bold",
        x=0.44,
        y=0.985,
    )
    fig.text(
        0.02,
        0.018,
        "Fuentes: MIVAU alquiler municipal, SETELECO cobertura 1 Gbps, NASA POWER T2M y Eurostat/GISCO NUTS3. "
        "Coropleta provincial en 5 cuantiles; los pesos son una decision metodologica.",
        fontsize=8,
        color="#555555",
    )

    fig.savefig(OUTPUT_DIR / "mapa6_indice_destino_tech.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa6_indice_destino_tech.pdf", bbox_inches="tight")
    plt.close(fig)


class WeightedIndexControl(MacroElement):
    _template = Template(
        """
        {% macro header(this, kwargs) %}
        <style>
          #{{ this._parent.get_name() }} .index-panel {
            width: 318px;
            max-width: calc(100vw - 34px);
            padding: 10px 12px;
            border: 1px solid rgba(60, 60, 60, 0.55);
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.22);
            color: #1f1f1f;
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.34;
          }

          #{{ this._parent.get_name() }} .index-panel-title {
            margin-bottom: 5px;
            font-size: 12.5px;
            font-weight: 700;
          }

          #{{ this._parent.get_name() }} .index-weight-row {
            display: grid;
            grid-template-columns: 102px 1fr 36px;
            align-items: center;
            gap: 6px;
            margin: 6px 0;
          }

          #{{ this._parent.get_name() }} .index-weight-row label {
            font-size: 11px;
            font-weight: 700;
          }

          #{{ this._parent.get_name() }} .index-weight-row input {
            width: 100%;
            accent-color: #018571;
          }

          #{{ this._parent.get_name() }} .index-weight-value {
            text-align: right;
            font-variant-numeric: tabular-nums;
          }

          #{{ this._parent.get_name() }} .index-summary {
            margin-top: 8px;
            padding-top: 7px;
            border-top: 1px solid rgba(0,0,0,0.16);
          }

          #{{ this._parent.get_name() }} .index-top-list {
            margin: 5px 0 0 0;
            padding-left: 18px;
          }

          #{{ this._parent.get_name() }} .index-top-list li {
            margin: 2px 0;
          }

          #{{ this._parent.get_name() }} .index-legend-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin: 3px 0;
            font-size: 11px;
          }

          #{{ this._parent.get_name() }} .index-legend-swatch {
            width: 18px;
            height: 12px;
            display: inline-block;
            border: 1px solid rgba(0,0,0,0.35);
          }

          #{{ this._parent.get_name() }} .dynamic-rank-label {
            background: transparent;
            border: 0;
          }
        </style>
        {% endmacro %}

        {% macro script(this, kwargs) %}
        (function () {
          const map = {{ this._parent.get_name() }};
          const indexLayer = {{ this.index_layer_name }};
          const components = {{ this.components_json | safe }};
          const palette = {{ this.palette_json | safe }};
          const labelsLayer = L.layerGroup().addTo(map);
          const formatter = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 1 });

          function asNumber(value) {
            const parsed = Number(value);
            return Number.isFinite(parsed) ? parsed : 0;
          }

          function quantileBins(values, classes) {
            const sorted = values
              .filter((value) => Number.isFinite(value))
              .sort((a, b) => a - b);
            if (!sorted.length) {
              return [0, 20, 40, 60, 80, 100];
            }
            const bins = [];
            for (let i = 0; i <= classes; i += 1) {
              const pos = Math.round((sorted.length - 1) * i / classes);
              bins.push(sorted[pos]);
            }
            bins[0] = Math.floor(bins[0] * 10) / 10;
            bins[bins.length - 1] = Math.ceil(bins[bins.length - 1] * 10) / 10;
            return bins;
          }

          function colorForValue(value, bins) {
            if (!Number.isFinite(value)) {
              return "#d3d3d3";
            }
            for (let i = 0; i < palette.length; i += 1) {
              if (value <= bins[i + 1]) {
                return palette[i];
              }
            }
            return palette[palette.length - 1];
          }

          function binLabel(bins, index) {
            const low = formatter.format(bins[index]);
            const high = formatter.format(bins[index + 1]);
            return `${low} - ${high}`;
          }

          function readRawWeights(container) {
            const rawWeights = {};
            components.forEach((component) => {
              const input = container.querySelector(`[data-weight="${component.key}"]`);
              rawWeights[component.key] = asNumber(input.value);
            });
            return rawWeights;
          }

          function normalizeWeights(rawWeights) {
            const total = Object.values(rawWeights).reduce((acc, value) => acc + value, 0);
            if (total <= 0) {
              const equal = 1 / components.length;
              return {
                total,
                normalized: Object.fromEntries(components.map((component) => [component.key, equal])),
              };
            }
            return {
              total,
              normalized: Object.fromEntries(
                components.map((component) => [component.key, rawWeights[component.key] / total])
              ),
            };
          }

          function calculateIndex(properties, weights) {
            return components.reduce(
              (acc, component) => acc + asNumber(properties[component.key]) * weights[component.key],
              0
            );
          }

          function popupHtml(properties, weights) {
            const rows = components.map((component) => {
              const score = asNumber(properties[component.key]);
              const contribution = score * weights[component.key];
              return `<tr><td>${component.label}</td><td style="text-align:right; padding-left:10px;">${formatter.format(score)}</td><td style="text-align:right; padding-left:10px;">${formatter.format(contribution)}</td></tr>`;
            }).join("");
            return `
              <div style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.35; min-width: 260px;">
                <strong style="font-size: 13px;">${properties.province_name}</strong><br>
                Indice recalculado: <strong>${formatter.format(properties.dynamic_index)}</strong><br>
                Ranking recalculado: <strong>#${properties.dynamic_rank}</strong>
                <hr style="margin: 6px 0;">
                <table>
                  <thead><tr><th style="text-align:left;">Componente</th><th>Score</th><th>Aporte</th></tr></thead>
                  <tbody>${rows}</tbody>
                </table>
              </div>
            `;
          }

          function tooltipHtml(properties) {
            return `
              <div>
                <strong>${properties.province_name}</strong><br>
                Ranking: #${properties.dynamic_rank}<br>
                Indice recalculado: ${formatter.format(properties.dynamic_index)}<br>
                Alquiler: ${formatter.format(asNumber(properties.rent_eur_month))} EUR/mes<br>
                Cobertura 1 Gbps: ${formatter.format(asNumber(properties.coverage_1gbps_2024_pct))}%
              </div>
            `;
          }

          function dynamicStyle(properties, bins) {
            return {
              fillColor: colorForValue(properties.dynamic_index, bins),
              color: "#4a4a4a",
              weight: 0.5,
              fillOpacity: 0.84,
            };
          }

          function updateMap(container) {
            const rawWeights = readRawWeights(container);
            const weightInfo = normalizeWeights(rawWeights);
            const weights = weightInfo.normalized;
            const rows = [];

            indexLayer.eachLayer((layer) => {
              const properties = layer.feature.properties;
              properties.dynamic_index = calculateIndex(properties, weights);
              rows.push({ layer, properties });
            });

            rows.sort((a, b) => b.properties.dynamic_index - a.properties.dynamic_index);
            rows.forEach((row, index) => {
              row.properties.dynamic_rank = index + 1;
            });

            const bins = quantileBins(rows.map((row) => row.properties.dynamic_index), 5);
            rows.forEach((row) => {
              row.layer.setStyle(dynamicStyle(row.properties, bins));
              if (row.layer.__dynamicMouseoutHandler) {
                row.layer.off("mouseout", row.layer.__dynamicMouseoutHandler);
              }
              row.layer.__dynamicMouseoutHandler = function () {
                window.setTimeout(() => row.layer.setStyle(dynamicStyle(row.properties, bins)), 0);
              };
              row.layer.on("mouseout", row.layer.__dynamicMouseoutHandler);
              if (row.layer.getTooltip && row.layer.getTooltip()) {
                row.layer.setTooltipContent(tooltipHtml(row.properties));
              } else {
                row.layer.bindTooltip(tooltipHtml(row.properties), { sticky: false });
              }
              if (row.layer.getPopup && row.layer.getPopup()) {
                row.layer.setPopupContent(popupHtml(row.properties, weights));
              } else {
                row.layer.bindPopup(popupHtml(row.properties, weights), { maxWidth: 390 });
              }
            });

            labelsLayer.clearLayers();
            rows.slice(0, 10).forEach((row) => {
              const properties = row.properties;
              const lat = Number(properties.label_lat);
              const lon = Number(properties.label_lon);
              if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
                return;
              }
              const html = `
                <div style="
                  min-width: 92px; padding: 2px 5px;
                  background: rgba(255, 255, 255, 0.90);
                  border: 1px solid #444; border-radius: 3px;
                  color: #111; font-family: Arial, sans-serif;
                  font-size: 10px; font-weight: 700; line-height: 1.15;
                  text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.25);">
                  #${properties.dynamic_rank} ${properties.province_name}<br>${formatter.format(properties.dynamic_index)}
                </div>
              `;
              L.marker([lat, lon], {
                icon: L.divIcon({
                  html,
                  className: "dynamic-rank-label",
                  iconSize: [98, 32],
                  iconAnchor: [49, 16],
                }),
              }).addTo(labelsLayer);
            });

            components.forEach((component) => {
              const value = container.querySelector(`[data-value="${component.key}"]`);
              value.textContent = `${Math.round(rawWeights[component.key])}`;
            });

            const normalized = components.map((component) => (
              `${component.label}: ${(weights[component.key] * 100).toFixed(1)}%`
            )).join(" · ");
            container.querySelector("[data-summary]").textContent =
              `Suma bruta: ${weightInfo.total}. Pesos normalizados: ${normalized}`;

            const topList = container.querySelector("[data-top]");
            topList.innerHTML = rows.slice(0, 5).map((row) => (
              `<li><strong>#${row.properties.dynamic_rank} ${row.properties.province_name}</strong>: ${formatter.format(row.properties.dynamic_index)}</li>`
            )).join("");

            const legend = container.querySelector("[data-legend]");
            legend.innerHTML = palette.map((color, index) => (
              `<div class="index-legend-row"><span class="index-legend-swatch" style="background:${color};"></span><span>${binLabel(bins, index)}</span></div>`
            )).join("");
          }

          const control = L.control({ position: "topright" });
          control.onAdd = function () {
            const container = L.DomUtil.create("div", "index-panel leaflet-control");
            L.DomEvent.disableClickPropagation(container);
            L.DomEvent.disableScrollPropagation(container);
            container.innerHTML = `
              <div class="index-panel-title">Pesos del indice</div>
              ${components.map((component) => `
                <div class="index-weight-row">
                  <label for="weight-${component.key}">${component.label}</label>
                  <input id="weight-${component.key}" data-weight="${component.key}" type="range" min="0" max="60" step="1" value="${component.default}">
                  <span class="index-weight-value" data-value="${component.key}">${component.default}</span>
                </div>
              `).join("")}
              <div class="index-summary" data-summary></div>
              <div class="index-summary">
                <div class="index-panel-title">Top 5 recalculado</div>
                <ol class="index-top-list" data-top></ol>
              </div>
              <div class="index-summary">
                <div class="index-panel-title">Leyenda dinamica</div>
                <div data-legend></div>
              </div>
            `;
            components.forEach((component) => {
              container
                .querySelector(`[data-weight="${component.key}"]`)
                .addEventListener("input", () => updateMap(container));
            });
            window.setTimeout(() => updateMap(container), 0);
            return container;
          };
          control.addTo(map);
        })();
        {% endmacro %}
        """
    )

    def __init__(self, index_layer: folium.GeoJson) -> None:
        super().__init__()
        self._name = "WeightedIndexControl"
        self.index_layer_name = index_layer.get_name()
        self.components_json = json.dumps(
            [
                {
                    "key": "rent_score_low_price",
                    "label": "Alquiler bajo",
                    "default": int(WEIGHTS["rent_score_low_price"] * 100),
                },
                {
                    "key": "rent_growth_score",
                    "label": "Subida moderada",
                    "default": int(WEIGHTS["rent_growth_score"] * 100),
                },
                {
                    "key": "availability_score",
                    "label": "Disponibilidad",
                    "default": int(WEIGHTS["availability_score"] * 100),
                },
                {
                    "key": "connectivity_score",
                    "label": "Conectividad",
                    "default": int(WEIGHTS["connectivity_score"] * 100),
                },
                {
                    "key": "climate_score",
                    "label": "Confort climatico",
                    "default": int(WEIGHTS["climate_score"] * 100),
                },
            ],
            ensure_ascii=True,
        )
        self.palette_json = json.dumps(INDEX_PALETTE)


def add_score_layer(
    web_map: folium.Map,
    map_data: gpd.GeoDataFrame,
    name: str,
    score_column: str,
    bins: list[float],
    show: bool = False,
) -> folium.GeoJson:
    tooltip_fields = [
        "province_name",
        "rank_tech",
        "index_class",
        "tech_destination_index",
        "rent_eur_month",
        "rent_growth_annual_label",
        "rental_homes_per_1000_households",
        "coverage_1gbps_2024_pct",
        "climate_comfort_score",
        "recommendation",
    ]
    tooltip_aliases = [
        "Provincia",
        "Ranking",
        "Clase",
        "Indice final",
        "Alquiler mensual",
        "Crecimiento alquiler",
        "Viviendas alquiler / 1.000 hogares",
        "Cobertura 1 Gbps",
        "Confort climatico",
        "Lectura",
    ]
    popup_fields = [
        "province_name",
        "rent_baseline_label",
        "rent_score_low_price",
        "rent_growth_score",
        "availability_score",
        "connectivity_score",
        "climate_score",
        "rent_contribution",
        "growth_contribution",
        "availability_contribution",
        "connectivity_contribution",
        "climate_contribution",
        "tech_destination_index",
    ]
    popup_aliases = [
        "Provincia",
        "Historico alquiler",
        "Score alquiler bajo",
        "Score subida moderada",
        "Score disponibilidad",
        "Score conectividad",
        "Score clima",
        "Aporte alquiler",
        "Aporte evolucion",
        "Aporte disponibilidad",
        "Aporte conectividad",
        "Aporte clima",
        "Indice final",
    ]

    layer = folium.GeoJson(
        map_data,
        name=name,
        show=show,
        style_function=lambda feature, column=score_column, local_bins=bins: {
            "fillColor": color_for_bins(
                feature["properties"].get(column),
                local_bins,
                INDEX_PALETTE,
            ),
            "color": "#4a4a4a",
            "weight": 0.5,
            "fillOpacity": 0.82,
        },
        highlight_function=lambda _: {"weight": 2.0, "color": "#111111", "fillOpacity": 0.92},
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            labels=True,
            sticky=False,
        ),
        popup=folium.GeoJsonPopup(
            fields=popup_fields,
            aliases=popup_aliases,
            localize=True,
            labels=True,
            max_width=380,
        ),
    )
    layer.add_to(web_map)
    return layer


def add_index_legend(web_map: folium.Map, bins: list[float]) -> None:
    labels = build_bin_labels(bins)
    rows = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:6px; margin:3px 0;">
          <span style="width:18px; height:12px; display:inline-block; background:{color};
          border:1px solid rgba(0,0,0,0.35);"></span>
          <span>{label}</span>
        </div>
        """
        for color, label in zip(INDEX_PALETTE, labels)
    )
    html = f"""
    <div style="
      position: fixed; top: 84px; right: 18px; z-index: 9999;
      background: rgba(255,255,255,0.94); padding: 9px 10px;
      border: 1px solid rgba(60,60,60,0.55); border-radius: 4px;
      font-family: Arial, sans-serif; font-size: 11.5px; line-height: 1.25;
      box-shadow: 0 1px 5px rgba(0,0,0,0.22);">
      <div style="font-size:12.5px; font-weight:700; margin-bottom:6px;">Indice final</div>
      {rows}
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(html))


def add_top_labels(web_map: folium.Map, map_data: gpd.GeoDataFrame) -> None:
    label_layer = folium.FeatureGroup(name="Etiquetas top 10", show=True)
    for _, row in map_data.nsmallest(10, "rank_tech").iterrows():
        label_html = f"""
        <div style="
          min-width: 86px; padding: 2px 5px;
          background: rgba(255, 255, 255, 0.90);
          border: 1px solid #444; border-radius: 3px;
          color: #111; font-family: Arial, sans-serif;
          font-size: 10px; font-weight: 700; line-height: 1.15;
          text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.25);">
          #{int(row['rank_tech'])} {row['province_name']}<br>{row['tech_destination_index']:.1f}
        </div>
        """
        folium.Marker(
            location=[row["label_lat"], row["label_lon"]],
            icon=folium.DivIcon(
                html=label_html,
                icon_size=(92, 32),
                icon_anchor=(46, 16),
            ),
            tooltip=f"#{int(row['rank_tech'])} {row['province_name']}",
        ).add_to(label_layer)
    label_layer.add_to(web_map)


def save_interactive_map(
    map_data: gpd.GeoDataFrame,
    current_year: int,
    bins: list[float],
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    web_map = folium.Map(
        location=[40.1, -3.7],
        zoom_start=6,
        tiles=None,
        control_scale=True,
        max_bounds=True,
    )
    folium.TileLayer("CartoDB positron", name="Base clara", control=True).add_to(web_map)
    folium.TileLayer("CartoDB dark_matter", name="Base oscura", control=True).add_to(web_map)
    web_map.fit_bounds([[27.3, -18.8], [43.9, 4.7]])

    final_layer = add_score_layer(
        web_map,
        map_data,
        f"Indice final ({current_year})",
        "tech_destination_index",
        bins,
        show=True,
    )

    WeightedIndexControl(final_layer).add_to(web_map)
    plugins.MiniMap(toggle_display=True, minimized=True).add_to(web_map)
    plugins.Fullscreen(position="topright").add_to(web_map)
    plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(web_map)
    plugins.MousePosition(
        position="bottomleft",
        separator=", ",
        prefix="Coordenadas",
        num_digits=4,
    ).add_to(web_map)
    plugins.Search(
        layer=final_layer,
        geom_type="Polygon",
        placeholder="Buscar provincia",
        collapsed=True,
        search_label="province_name",
        position="topleft",
    ).add_to(web_map)

    web_map.save(OUTPUT_DIR / "mapa6_indice_destino_tech_interactivo.html")


def save_tables(map_data: gpd.GeoDataFrame, current_year: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    columns = [
        "rank_tech",
        "COD_PROVINCIA",
        "province_name",
        "ccaa",
        "recommendation",
        "tech_destination_index",
        "index_class",
        "rent_eur_month",
        "baseline_year",
        "baseline_rent_eur_month",
        "rent_growth_total_pct",
        "rent_growth_annual_pct",
        "has_growth_history",
        "rental_homes",
        "rental_homes_per_1000_households",
        "municipalities",
        "coverage_1gbps_2024_pct",
        "annual_mean_c",
        "climate_comfort_score",
        "rent_score_low_price",
        "rent_growth_score",
        "availability_score",
        "connectivity_score",
        "climate_score",
        "rent_contribution",
        "growth_contribution",
        "availability_contribution",
        "connectivity_contribution",
        "climate_contribution",
        "population",
        "households",
        "label_lat",
        "label_lon",
        "area_km2",
    ]
    table = map_data[columns].sort_values("rank_tech").copy()
    table["year"] = current_year
    table.to_csv(OUTPUT_DIR / "mapa6_indice_destino_tech_datos.csv", index=False)


def main() -> None:
    map_data, current_year, bins = build_dataset()
    save_static_map(map_data, current_year, bins)
    save_interactive_map(map_data, current_year, bins)
    save_tables(map_data, current_year)

    top = map_data.nsmallest(5, "rank_tech")[["rank_tech", "province_name", "tech_destination_index"]]
    print(f"Mapa 6 generado con datos de alquiler {current_year}.")
    print("Top 5 del indice final:")
    for _, row in top.iterrows():
        print(f"  {int(row['rank_tech'])}. {row['province_name']}: {row['tech_destination_index']:.1f}")
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
