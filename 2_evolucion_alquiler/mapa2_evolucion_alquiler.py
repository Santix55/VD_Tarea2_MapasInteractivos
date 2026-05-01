from __future__ import annotations

from pathlib import Path
import argparse
import html
import math
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


DATA_DIR = BASE_DIR / "datos"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"

MIVAU_URL = "https://cdn.mivau.gob.es/portal-web-mivau/Datos_MIVAU/CSV/VDP001_01.csv"
NUTS_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson"

RENT_FILE = DATA_DIR / "mivau_alquiler_municipios.csv"
NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"

DEFAULT_START_YEAR = 2019
GROWTH_PALETTE = ["#2166ac", "#67a9cf", "#f7f7f7", "#fdae61", "#b2182b"]
NO_DATA_COLOR = "#d9d9d9"
RECENT_START_YEAR = 2021
PRE_START_YEAR = 2011
PRE_END_YEAR = 2019

TRAJECTORY_STYLES = {
    "Subida extrema": {
        "marker": "^",
        "color": "#8c1d18",
        "fill": "#c8192e",
        "letter": "E",
        "description": "Subida total en el quintil superior.",
    },
    "Aceleracion reciente": {
        "marker": "P",
        "color": "#7a3b00",
        "fill": "#f28e2b",
        "letter": "A",
        "description": "El ritmo 2021-final supera claramente el tramo 2011-2019.",
    },
    "Rebote post-2021": {
        "marker": "D",
        "color": "#6b3a90",
        "fill": "#a05eb5",
        "letter": "R",
        "description": "Venia de caidas o estancamiento y repunta desde 2021.",
    },
    "Subida sostenida": {
        "marker": "o",
        "color": "#116466",
        "fill": "#2a9d8f",
        "letter": "S",
        "description": "Crecimiento antes de 2019 y tambien en el tramo reciente.",
    },
    "Crecimiento contenido": {
        "marker": "s",
        "color": "#264653",
        "fill": "#6c8ead",
        "letter": "C",
        "description": "Subida comparable, pero sin senales fuertes de tension.",
    },
    "Sin historico comparable": {
        "marker": "X",
        "color": "#555555",
        "fill": NO_DATA_COLOR,
        "letter": "H",
        "description": "No tiene ano inicial comparable antes del ano final.",
    },
}

TRAJECTORY_ORDER = [
    "Subida extrema",
    "Aceleracion reciente",
    "Rebote post-2021",
    "Subida sostenida",
    "Crecimiento contenido",
    "Sin historico comparable",
]

TEMPORAL_PALETTE = ["#f7fbff", "#c6dbef", "#6baed6", "#fdae6b", "#cb181d"]

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


def download_file(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=90, headers={"User-Agent": "VD-map-project/1.0"})
    response.raise_for_status()
    target.write_bytes(response.content)


def clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def find_year_column(columns: pd.Index) -> str:
    for column in columns:
        normalized = str(column).strip().lower()
        if normalized in {"ano", "anio"} or normalized.startswith("a"):
            return str(column)
    raise ValueError("No se encontro la columna de ano en el CSV de MIVAU.")


def format_eur(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):,.0f} EUR".replace(",", ".")


def format_pct(value: float | int | None, signed: bool = True) -> str:
    if pd.isna(value):
        return "sin dato"
    sign = "+" if signed and float(value) > 0 else ""
    return f"{sign}{float(value):.1f}%"


def format_pp(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    sign = "+" if float(value) > 0 else ""
    return f"{sign}{float(value):.1f} pp/ano"


def format_int(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):,.0f}".replace(",", ".")


def safe_cagr(start_value: float | int | None, end_value: float | int | None, years: float | int) -> float:
    if pd.isna(start_value) or pd.isna(end_value) or pd.isna(years):
        return math.nan
    if float(start_value) <= 0 or float(end_value) <= 0 or float(years) <= 0:
        return math.nan
    return ((float(end_value) / float(start_value)) ** (1 / float(years)) - 1) * 100


def growth_pct(start_value: float | int | None, end_value: float | int | None) -> float:
    if pd.isna(start_value) or pd.isna(end_value) or float(start_value) <= 0:
        return math.nan
    return (float(end_value) / float(start_value) - 1) * 100


def format_year(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return str(int(value))


def short_province_name(value: str) -> str:
    text = str(value)
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = normalized.strip().lower()
    replacements = {
        "balears, illes": "Balears",
        "valencia/valencia": "Valencia",
        "coruna, a": "A Coruna",
        "araba/alava": "Alava",
        "palmas, las": "Las Palmas",
        "rioja, la": "La Rioja",
    }
    return replacements.get(normalized, text)


def load_mivau() -> pd.DataFrame:
    rent = pd.read_csv(
        RENT_FILE,
        sep=";",
        encoding="utf-8-sig",
        dtype={"COD_PROVINCIA": str, "COD_POSTAL": str},
    )
    year_column = find_year_column(rent.columns)
    rent["COD_PROVINCIA"] = rent["COD_PROVINCIA"].str.zfill(2)
    rent["COD_POSTAL"] = rent["COD_POSTAL"].str.zfill(5)
    rent["year"] = rent[year_column].astype(int)
    rent["VALOR"] = clean_numeric(rent["VALOR"])
    return rent


def build_yearly_province_rent(rent: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "COD_PROVINCIA",
        "PROVINCIA",
        "COD_POSTAL",
        "NOMBRE_MUNICIPIO",
        "TIPO_VIVIENDA",
        "year",
    ]

    prices = rent[
        rent["ELEMENTO"].eq("PRECIO") & rent["TIPO_MEDIDA"].eq("MEDIANA")
    ][keys + ["VALOR"]].rename(columns={"VALOR": "median_rent_eur"})

    weights = rent[
        rent["ELEMENTO"].eq("VIVIENDA") & rent["TIPO_MEDIDA"].eq("RECUENTO")
    ][keys + ["VALOR"]].rename(columns={"VALOR": "rental_homes"})

    by_type = prices.merge(weights, on=keys, how="left")
    by_type = by_type.dropna(subset=["median_rent_eur", "rental_homes"])
    by_type = by_type[by_type["rental_homes"].gt(0)].copy()
    by_type["weighted_price"] = by_type["median_rent_eur"] * by_type["rental_homes"]

    municipal = (
        by_type.groupby(
            ["COD_PROVINCIA", "PROVINCIA", "COD_POSTAL", "NOMBRE_MUNICIPIO", "year"],
            as_index=False,
        )
        .agg(
            weighted_price=("weighted_price", "sum"),
            rental_homes=("rental_homes", "sum"),
            dwelling_types=("TIPO_VIVIENDA", "nunique"),
        )
    )
    municipal["municipal_rent_eur"] = municipal["weighted_price"] / municipal["rental_homes"]
    municipal["weighted_price"] = municipal["municipal_rent_eur"] * municipal["rental_homes"]

    yearly = (
        municipal.groupby(["COD_PROVINCIA", "PROVINCIA", "year"], as_index=False)
        .agg(
            total_weighted_price=("weighted_price", "sum"),
            rental_homes=("rental_homes", "sum"),
            municipalities=("COD_POSTAL", "nunique"),
            municipal_rent_q25=("municipal_rent_eur", lambda values: values.quantile(0.25)),
            municipal_rent_q75=("municipal_rent_eur", lambda values: values.quantile(0.75)),
        )
    )
    yearly["rent_eur_month"] = yearly["total_weighted_price"] / yearly["rental_homes"]
    yearly["municipal_spread_eur"] = yearly["municipal_rent_q75"] - yearly["municipal_rent_q25"]
    yearly = yearly.drop(columns=["total_weighted_price"])
    yearly = yearly.sort_values(["COD_PROVINCIA", "year"]).reset_index(drop=True)
    return yearly


def load_province_geometries() -> gpd.GeoDataFrame:
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])

    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    provinces = provinces[["COD_PROVINCIA", "geometry"]].copy()
    return provinces.to_crs("EPSG:4326")


def build_growth_table(
    yearly: pd.DataFrame,
    start_year: int = DEFAULT_START_YEAR,
    end_year: int | None = None,
    allow_first_available: bool = True,
) -> tuple[pd.DataFrame, int]:
    current_year = int(yearly["year"].max() if end_year is None else end_year)
    if start_year >= current_year:
        raise ValueError("El ano inicial debe ser anterior al ano final.")

    current = yearly[yearly["year"].eq(current_year)].copy()
    current = current.rename(
        columns={
            "PROVINCIA": "province_name",
            "rent_eur_month": "current_rent_eur_month",
            "rental_homes": "current_rental_homes",
            "municipalities": "current_municipalities",
            "municipal_spread_eur": "current_municipal_spread_eur",
        }
    )

    if allow_first_available:
        baseline = (
            yearly[yearly["year"].ge(start_year) & yearly["year"].lt(current_year)]
            .sort_values(["COD_PROVINCIA", "year"])
            .groupby("COD_PROVINCIA", as_index=False)
            .first()
        )
    else:
        baseline = yearly[yearly["year"].eq(start_year)].copy()

    baseline = baseline.rename(
        columns={
            "rent_eur_month": "baseline_rent_eur_month",
            "year": "baseline_year",
            "rental_homes": "baseline_rental_homes",
            "municipalities": "baseline_municipalities",
            "municipal_spread_eur": "baseline_municipal_spread_eur",
        }
    )

    result = current.merge(
        baseline[
            [
                "COD_PROVINCIA",
                "baseline_year",
                "baseline_rent_eur_month",
                "baseline_rental_homes",
                "baseline_municipalities",
                "baseline_municipal_spread_eur",
            ]
        ],
        on="COD_PROVINCIA",
        how="left",
    )

    years_between = current_year - result["baseline_year"]
    result["rent_change_eur_month"] = (
        result["current_rent_eur_month"] - result["baseline_rent_eur_month"]
    )
    result["rent_growth_total_pct"] = (
        result["current_rent_eur_month"] / result["baseline_rent_eur_month"] - 1
    ) * 100
    result["rent_growth_annual_pct"] = (
        (result["current_rent_eur_month"] / result["baseline_rent_eur_month"])
        ** (1 / years_between)
        - 1
    ) * 100
    invalid = years_between.le(0) | result["baseline_rent_eur_month"].isna()
    result.loc[
        invalid,
        ["rent_change_eur_month", "rent_growth_total_pct", "rent_growth_annual_pct"],
    ] = pd.NA
    result["has_growth_history"] = result["rent_growth_total_pct"].notna()
    result["current_year"] = current_year
    result = add_trajectory_metrics(result, yearly, current_year)
    return result, current_year


def add_trajectory_metrics(
    growth: pd.DataFrame,
    yearly: pd.DataFrame,
    current_year: int,
) -> pd.DataFrame:
    result = growth.copy()
    lookup = yearly.set_index(["COD_PROVINCIA", "year"])["rent_eur_month"].to_dict()
    year_counts = yearly.groupby("COD_PROVINCIA")["year"].agg(
        first_year="min",
        years_available="nunique",
    )
    pre_counts = (
        yearly[yearly["year"].between(PRE_START_YEAR, PRE_END_YEAR)]
        .groupby("COD_PROVINCIA")["year"]
        .nunique()
    )

    recent_start = RECENT_START_YEAR if current_year > RECENT_START_YEAR else max(
        int(result["baseline_year"].dropna().min()) if result["baseline_year"].notna().any() else PRE_START_YEAR,
        current_year - 1,
    )
    pre_years = PRE_END_YEAR - PRE_START_YEAR
    recent_years = current_year - recent_start

    result["growth_total_pct"] = result["rent_growth_total_pct"]
    result["growth_annual_pct"] = result["rent_growth_annual_pct"]
    result["recent_start_year"] = recent_start
    result["pre_start_year"] = PRE_START_YEAR
    result["pre_end_year"] = PRE_END_YEAR

    result["recent_start_rent_eur_month"] = result["COD_PROVINCIA"].map(
        lambda code: lookup.get((code, recent_start), math.nan)
    )
    result["pre_start_rent_eur_month"] = result["COD_PROVINCIA"].map(
        lambda code: lookup.get((code, PRE_START_YEAR), math.nan)
    )
    result["pre_end_rent_eur_month"] = result["COD_PROVINCIA"].map(
        lambda code: lookup.get((code, PRE_END_YEAR), math.nan)
    )
    result["first_year_available"] = result["COD_PROVINCIA"].map(year_counts["first_year"])
    result["years_available"] = result["COD_PROVINCIA"].map(year_counts["years_available"]).fillna(0)
    result["series_complete_2011_2019"] = (
        result["COD_PROVINCIA"].map(pre_counts).fillna(0).eq(pre_years + 1)
    )

    result["growth_recent_pct"] = result.apply(
        lambda row: growth_pct(row["recent_start_rent_eur_month"], row["current_rent_eur_month"]),
        axis=1,
    )
    result["growth_recent_annual_pct"] = result.apply(
        lambda row: safe_cagr(
            row["recent_start_rent_eur_month"],
            row["current_rent_eur_month"],
            recent_years,
        ),
        axis=1,
    )
    result["growth_pre_pct"] = result.apply(
        lambda row: growth_pct(row["pre_start_rent_eur_month"], row["pre_end_rent_eur_month"]),
        axis=1,
    )
    result["growth_pre_annual_pct"] = result.apply(
        lambda row: safe_cagr(
            row["pre_start_rent_eur_month"],
            row["pre_end_rent_eur_month"],
            pre_years,
        ),
        axis=1,
    )
    result["acceleration_pp_year"] = (
        result["growth_recent_annual_pct"] - result["growth_pre_annual_pct"]
    )
    result["trajectory_class"] = classify_trajectories(result)
    result["trajectory_description"] = result["trajectory_class"].map(
        lambda value: TRAJECTORY_STYLES[value]["description"]
    )
    return result


def classify_trajectories(data: pd.DataFrame) -> pd.Series:
    valid = data[data["has_growth_history"]].copy()
    if valid.empty:
        return pd.Series("Sin historico comparable", index=data.index)

    total_extreme = valid["growth_total_pct"].quantile(0.8)
    recent_median = valid["growth_recent_pct"].median()
    acceleration_high = valid["acceleration_pp_year"].dropna().quantile(0.65)
    pre_annual_median = valid["growth_pre_annual_pct"].dropna().median()
    recent_annual_median = valid["growth_recent_annual_pct"].dropna().median()

    def classify(row: pd.Series) -> str:
        if not bool(row["has_growth_history"]):
            return "Sin historico comparable"
        if (
            pd.notna(row["growth_pre_pct"])
            and row["growth_pre_pct"] <= 0
            and pd.notna(row["growth_recent_pct"])
            and row["growth_recent_pct"] >= recent_median
        ):
            return "Rebote post-2021"
        if pd.notna(row["growth_total_pct"]) and row["growth_total_pct"] >= total_extreme:
            return "Subida extrema"
        if (
            pd.notna(row["acceleration_pp_year"])
            and row["acceleration_pp_year"] >= acceleration_high
            and pd.notna(row["growth_recent_pct"])
            and row["growth_recent_pct"] >= recent_median
        ):
            return "Aceleracion reciente"
        if (
            pd.notna(row["growth_pre_annual_pct"])
            and pd.notna(row["growth_recent_annual_pct"])
            and row["growth_pre_annual_pct"] >= max(0, pre_annual_median)
            and row["growth_recent_annual_pct"] >= recent_annual_median
        ):
            return "Subida sostenida"
        return "Crecimiento contenido"

    return data.apply(classify, axis=1)


def add_geographic_metrics(map_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    data = map_data.copy()
    projected = data.to_crs("EPSG:3035")
    points = gpd.GeoSeries(projected.geometry.representative_point(), crs=projected.crs)
    points_wgs84 = points.to_crs("EPSG:4326")
    data["label_lon"] = points_wgs84.x
    data["label_lat"] = points_wgs84.y
    data["area_km2"] = (projected.area / 1_000_000).round(1)
    return data


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
        return NO_DATA_COLOR

    numeric_value = float(value)
    for index, upper in enumerate(bins[1:]):
        is_last = index == len(colors) - 1
        if numeric_value <= upper or is_last:
            return colors[index]
    return colors[-1]


def label_for_bins(value: float | int | None, bins: list[float]) -> str:
    if value is None or pd.isna(value):
        return "Sin historico comparable"

    labels = [
        "Crecimiento muy bajo",
        "Crecimiento bajo",
        "Crecimiento medio",
        "Crecimiento alto",
        "Crecimiento muy alto",
    ]
    numeric_value = float(value)
    for index, upper in enumerate(bins[1:]):
        is_last = index == len(labels) - 1
        if numeric_value <= upper or is_last:
            return labels[index]
    return labels[-1]


def build_bin_labels(bins: list[float]) -> list[str]:
    labels = []
    for index in range(len(bins) - 1):
        lower = bins[index]
        upper = bins[index + 1]
        if index == 0:
            labels.append(f"<= {upper:.1f}%")
        elif index == len(bins) - 2:
            labels.append(f"> {lower:.1f}%")
        else:
            labels.append(f"{lower:.1f}% - {upper:.1f}%")
    return labels


def add_labels(map_data: gpd.GeoDataFrame, bins: list[float], start_year: int) -> gpd.GeoDataFrame:
    labelled = map_data.copy()
    labelled["province_short"] = labelled["province_name"].map(short_province_name)
    labelled["growth_color"] = labelled["rent_growth_total_pct"].map(
        lambda value: color_for_bins(value, bins, GROWTH_PALETTE)
    )
    labelled["growth_class"] = labelled["rent_growth_total_pct"].map(
        lambda value: label_for_bins(value, bins)
    )
    labelled["analysis_window"] = labelled.apply(
        lambda row: "sin historico"
        if pd.isna(row["baseline_year"])
        else f"{int(row['baseline_year'])}-{int(row['current_year'])}",
        axis=1,
    )
    labelled["baseline_note"] = labelled.apply(
        lambda row: "Primer ano comparable"
        if pd.notna(row["baseline_year"]) and int(row["baseline_year"]) > start_year
        else ("Comparacion exacta" if pd.notna(row["baseline_year"]) else "Sin historico"),
        axis=1,
    )
    labelled["growth_total_label"] = labelled["rent_growth_total_pct"].map(format_pct)
    labelled["growth_annual_label"] = labelled["rent_growth_annual_pct"].map(format_pct)
    labelled["growth_recent_label"] = labelled["growth_recent_pct"].map(format_pct)
    labelled["growth_recent_annual_label"] = labelled["growth_recent_annual_pct"].map(format_pct)
    labelled["growth_pre_label"] = labelled["growth_pre_pct"].map(format_pct)
    labelled["growth_pre_annual_label"] = labelled["growth_pre_annual_pct"].map(format_pct)
    labelled["acceleration_label"] = labelled["acceleration_pp_year"].map(format_pp)
    labelled["recent_start_year_label"] = labelled["recent_start_year"].map(format_year)
    labelled["pre_window_label"] = labelled.apply(
        lambda row: "2011-2019" if row["series_complete_2011_2019"] else "sin serie completa",
        axis=1,
    )
    labelled["trajectory_letter"] = labelled["trajectory_class"].map(
        lambda value: TRAJECTORY_STYLES[value]["letter"]
    )
    labelled["trajectory_color"] = labelled["trajectory_class"].map(
        lambda value: TRAJECTORY_STYLES[value]["color"]
    )
    labelled["trajectory_fill"] = labelled["trajectory_class"].map(
        lambda value: TRAJECTORY_STYLES[value]["fill"]
    )
    labelled["trajectory_marker"] = labelled["trajectory_class"].map(
        lambda value: TRAJECTORY_STYLES[value]["marker"]
    )
    labelled["rent_change_label"] = labelled["rent_change_eur_month"].map(
        lambda value: format_eur(value) if pd.isna(value) or value <= 0 else f"+{format_eur(value)}"
    )
    labelled["baseline_rent_label"] = labelled["baseline_rent_eur_month"].map(format_eur)
    labelled["current_rent_label"] = labelled["current_rent_eur_month"].map(format_eur)
    labelled["current_homes_label"] = labelled["current_rental_homes"].map(format_int)
    labelled["current_municipalities_label"] = labelled["current_municipalities"].map(format_int)

    numeric_columns = [
        "current_rent_eur_month",
        "baseline_rent_eur_month",
        "rent_change_eur_month",
        "rent_growth_total_pct",
        "rent_growth_annual_pct",
        "current_rental_homes",
        "current_municipalities",
        "baseline_rental_homes",
        "baseline_municipalities",
        "current_municipal_spread_eur",
        "baseline_municipal_spread_eur",
        "recent_start_rent_eur_month",
        "pre_start_rent_eur_month",
        "pre_end_rent_eur_month",
        "growth_recent_pct",
        "growth_recent_annual_pct",
        "growth_pre_pct",
        "growth_pre_annual_pct",
        "acceleration_pp_year",
        "growth_total_pct",
        "growth_annual_pct",
        "first_year_available",
        "years_available",
        "area_km2",
    ]
    labelled[numeric_columns] = labelled[numeric_columns].round(2)
    return labelled


def build_dataset(
    start_year: int = DEFAULT_START_YEAR,
    end_year: int | None = None,
    allow_first_available: bool = True,
) -> tuple[gpd.GeoDataFrame, pd.DataFrame, int, list[float]]:
    download_file(MIVAU_URL, RENT_FILE)
    download_file(NUTS_URL, NUTS_FILE)

    rent = load_mivau()
    yearly = build_yearly_province_rent(rent)
    growth, current_year = build_growth_table(
        yearly,
        start_year=start_year,
        end_year=end_year,
        allow_first_available=allow_first_available,
    )
    provinces = load_province_geometries()

    map_data = provinces.merge(growth, on="COD_PROVINCIA", how="left")
    missing_current = map_data[map_data["current_rent_eur_month"].isna()]
    if not missing_current.empty:
        missing_codes = ", ".join(missing_current["COD_PROVINCIA"].tolist())
        raise ValueError(f"Faltan datos de alquiler actual para estas provincias: {missing_codes}")

    map_data = add_geographic_metrics(map_data)
    bins = build_quantile_bins(map_data["rent_growth_total_pct"], k=5)
    map_data = add_labels(map_data, bins, start_year)
    return map_data, yearly, current_year, bins


def build_indexed_series(
    yearly: pd.DataFrame,
    provinces: pd.DataFrame,
    current_year: int,
) -> pd.DataFrame:
    selected = provinces.dropna(subset=["baseline_year"]).copy()
    rows = []
    for _, province in selected.iterrows():
        code = province["COD_PROVINCIA"]
        start = int(province["baseline_year"])
        baseline_value = float(province["baseline_rent_eur_month"])
        subset = yearly[
            yearly["COD_PROVINCIA"].eq(code)
            & yearly["year"].between(start, current_year)
        ].copy()
        subset["province_name"] = province["province_short"]
        subset["baseline_year"] = start
        subset["rent_index"] = subset["rent_eur_month"] / baseline_value * 100
        rows.append(subset)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def select_trajectory_highlights(map_data: gpd.GeoDataFrame, limit: int = 6) -> gpd.GeoDataFrame:
    valid = map_data[map_data["has_growth_history"]].copy()
    if valid.empty:
        return valid

    priority_frames = [
        valid.nlargest(2, "growth_total_pct"),
        valid.nlargest(2, "acceleration_pp_year"),
        valid[valid["trajectory_class"].eq("Rebote post-2021")].nlargest(1, "growth_recent_pct"),
        valid[valid["trajectory_class"].eq("Subida sostenida")].nlargest(1, "growth_pre_pct"),
        valid.nsmallest(1, "growth_total_pct"),
    ]
    selected = pd.concat(priority_frames, ignore_index=False)
    selected = selected[~selected.index.duplicated(keep="first")]
    if len(selected) < limit:
        selected = pd.concat(
            [selected, valid.nlargest(limit, "growth_total_pct")],
            ignore_index=False,
        )
        selected = selected[~selected.index.duplicated(keep="first")]
    return selected.head(limit)


def plot_trajectory_markers(ax: plt.Axes, data: pd.DataFrame, size: float = 42, zorder: int = 4) -> None:
    for trajectory in TRAJECTORY_ORDER:
        subset = data[data["trajectory_class"].eq(trajectory)]
        if subset.empty:
            continue
        style = TRAJECTORY_STYLES[trajectory]
        ax.scatter(
            subset["label_lon"],
            subset["label_lat"],
            s=size,
            marker=style["marker"],
            facecolor=style["fill"],
            edgecolor=style["color"],
            linewidth=0.8,
            alpha=0.92,
            zorder=zorder,
        )


def trajectory_legend_handles() -> list[plt.Line2D]:
    handles = []
    for trajectory in TRAJECTORY_ORDER:
        style = TRAJECTORY_STYLES[trajectory]
        handles.append(
            plt.Line2D(
                [0],
                [0],
                marker=style["marker"],
                color="none",
                label=trajectory,
                markerfacecolor=style["fill"],
                markeredgecolor=style["color"],
                markeredgewidth=0.8,
                markersize=7,
            )
        )
    return handles


def color_for_temporal_index(value: float | int | None, bins: list[float]) -> str:
    if value is None or pd.isna(value):
        return NO_DATA_COLOR
    numeric = float(value)
    for index, upper in enumerate(bins[1:]):
        if numeric <= upper or index == len(TEMPORAL_PALETTE) - 1:
            return TEMPORAL_PALETTE[index]
    return TEMPORAL_PALETTE[-1]


def sparkline_svg(values: pd.DataFrame, width: int = 220, height: int = 46) -> str:
    clean = values.dropna(subset=["rent_eur_month"]).sort_values("year")
    if clean.empty:
        return ""
    x_values = clean["year"].astype(float)
    y_values = clean["rent_eur_month"].astype(float)
    x_min, x_max = x_values.min(), x_values.max()
    y_min, y_max = y_values.min(), y_values.max()
    x_span = max(1.0, x_max - x_min)
    y_span = max(1.0, y_max - y_min)
    points = []
    for year, rent in zip(x_values, y_values):
        x = 8 + (year - x_min) / x_span * (width - 16)
        y = height - 8 - (rent - y_min) / y_span * (height - 16)
        points.append(f"{x:.1f},{y:.1f}")
    return f"""
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"
      style="display:block; margin:6px 0 2px 0; background:#f8f8f8; border:1px solid #ddd;">
      <line x1="8" y1="{height - 8}" x2="{width - 8}" y2="{height - 8}" stroke="#cccccc" stroke-width="1"/>
      <polyline points="{' '.join(points)}" fill="none" stroke="#b2182b" stroke-width="2"/>
      <circle cx="{points[-1].split(',')[0]}" cy="{points[-1].split(',')[1]}" r="2.8" fill="#b2182b"/>
    </svg>
    """


def build_weighted_average_series(yearly: pd.DataFrame | None) -> pd.DataFrame:
    if yearly is None or yearly.empty:
        return pd.DataFrame(columns=["year", "rent_eur_month"])

    clean = yearly.dropna(subset=["rent_eur_month", "rental_homes"]).copy()
    clean = clean[clean["rental_homes"].gt(0)]
    if clean.empty:
        return pd.DataFrame(columns=["year", "rent_eur_month"])

    clean["weighted_rent"] = clean["rent_eur_month"] * clean["rental_homes"]
    average = (
        clean.groupby("year", as_index=False)
        .agg(weighted_rent=("weighted_rent", "sum"), rental_homes=("rental_homes", "sum"))
    )
    average["rent_eur_month"] = average["weighted_rent"] / average["rental_homes"]
    return average[["year", "rent_eur_month"]].sort_values("year")


def evolution_chart_svg(
    values: pd.DataFrame,
    reference: pd.DataFrame | None = None,
    width: int = 312,
    height: int = 132,
) -> str:
    clean = values.dropna(subset=["rent_eur_month"]).sort_values("year")
    if clean.empty:
        return """
        <div style="margin:7px 0; padding:8px; background:#f8f8f8; border:1px solid #dddddd;
        color:#666666; font-size:11px;">Sin serie anual disponible.</div>
        """

    reference_clean = pd.DataFrame(columns=["year", "rent_eur_month"])
    if reference is not None and not reference.empty:
        reference_clean = reference.dropna(subset=["rent_eur_month"]).sort_values("year")

    years = clean["year"].astype(int).tolist()
    rents = clean["rent_eur_month"].astype(float).tolist()
    reference_years = reference_clean["year"].astype(int).tolist()
    reference_rents = reference_clean["rent_eur_month"].astype(float).tolist()
    all_years = years + reference_years
    all_rents = rents + reference_rents
    x_min, x_max = min(all_years), max(all_years)
    y_min_raw, y_max_raw = min(all_rents), max(all_rents)
    y_padding = max((y_max_raw - y_min_raw) * 0.08, y_max_raw * 0.025, 8)
    y_min = max(0.0, y_min_raw - y_padding)
    y_max = y_max_raw + y_padding

    left, right, top, bottom = 42, 10, 12, 26
    plot_width = width - left - right
    plot_height = height - top - bottom
    x_span = max(1, x_max - x_min)
    y_span = max(1.0, y_max - y_min)

    def x_pos(year: int) -> float:
        if x_min == x_max:
            return left + plot_width / 2
        return left + (year - x_min) / x_span * plot_width

    def y_pos(rent: float) -> float:
        return top + (y_max - rent) / y_span * plot_height

    points = [(x_pos(year), y_pos(rent), year, rent) for year, rent in zip(years, rents)]
    reference_points = [
        (x_pos(year), y_pos(rent), year, rent)
        for year, rent in zip(reference_years, reference_rents)
    ]
    points_text = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in points)
    reference_points_text = " ".join(
        f"{x:.1f},{y:.1f}" for x, y, _, _ in reference_points
    )
    first_x, first_y, first_year, first_rent = points[0]
    last_x, last_y, last_year, last_rent = points[-1]
    reference_line = ""
    reference_label = ""
    if reference_points:
        reference_last_x, reference_last_y, _, reference_last_rent = reference_points[-1]
        reference_line = f"""
      <polyline points="{reference_points_text}" fill="none" stroke="#2f6f9f" stroke-width="2"
      stroke-dasharray="4 3" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="{reference_last_x:.1f}" cy="{reference_last_y:.1f}" r="3" fill="#2f6f9f"/>
        """
        reference_label = f"""
      <text x="{width - right}" y="{top + 24}" text-anchor="end" fill="#2f6f9f"
      font-size="10" font-weight="700">Media: {format_eur(reference_last_rent)}</text>
        """
    tick_values = [y_min, (y_min + y_max) / 2, y_max]
    grid = "\n".join(
        f"""
        <line x1="{left}" y1="{y_pos(value):.1f}" x2="{width - right}" y2="{y_pos(value):.1f}"
        stroke="#e3e3e3" stroke-width="1"/>
        <text x="{left - 5}" y="{y_pos(value) + 3:.1f}" text-anchor="end"
        fill="#666666" font-size="9">{format_eur(value)}</text>
        """
        for value in tick_values
    )
    circles = "\n".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="#ffffff" stroke="#b2182b" stroke-width="1.4"/>'
        for x, y, _, _ in points
    )

    return f"""
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img"
      aria-label="Evolucion anual del alquiler"
      style="display:block; margin:6px 0 7px 0; background:#ffffff; border:1px solid #d8d8d8;">
      <rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>
      {grid}
      <line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}"
      stroke="#b7b7b7" stroke-width="1"/>
      {reference_line}
      <polyline points="{points_text}" fill="none" stroke="#b2182b" stroke-width="2.4"
      stroke-linecap="round" stroke-linejoin="round"/>
      {circles}
      <circle cx="{first_x:.1f}" cy="{first_y:.1f}" r="3" fill="#777777"/>
      <circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3.5" fill="#b2182b"/>
      <text x="{left}" y="{height - 8}" fill="#555555" font-size="10">{first_year}</text>
      <text x="{width - right}" y="{height - 8}" text-anchor="end" fill="#555555" font-size="10">{last_year}</text>
      <text x="{width - right}" y="{top + 10}" text-anchor="end" fill="#b2182b"
      font-size="10" font-weight="700">Provincia: {format_eur(last_rent)}</text>
      {reference_label}
      <text x="{left}" y="{top + 10}" fill="#555555" font-size="10">{format_eur(first_rent)}</text>
      <line x1="{left}" y1="7" x2="{left + 16}" y2="7" stroke="#b2182b" stroke-width="2.4"/>
      <text x="{left + 20}" y="10" fill="#555555" font-size="9">Provincia</text>
      <line x1="{left + 78}" y1="7" x2="{left + 94}" y2="7" stroke="#2f6f9f" stroke-width="2"
      stroke-dasharray="4 3"/>
      <text x="{left + 98}" y="10" fill="#555555" font-size="9">Media estatal</text>
    </svg>
    """


def save_static_map(
    map_data: gpd.GeoDataFrame,
    yearly: pd.DataFrame,
    current_year: int,
    bins: list[float],
    start_year: int,
    allow_first_available: bool,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(16, 9.4), dpi=180)
    grid = fig.add_gridspec(
        3,
        2,
        width_ratios=[1.48, 0.92],
        height_ratios=[0.44, 1, 1],
        wspace=0.13,
        hspace=0.36,
    )
    map_ax = fig.add_subplot(grid[:, 0])
    summary_ax = fig.add_subplot(grid[0, 1])
    matrix_ax = fig.add_subplot(grid[1, 1])
    line_ax = fig.add_subplot(grid[2, 1])

    map_data.plot(
        ax=map_ax,
        color=map_data["growth_color"],
        linewidth=0.44,
        edgecolor="#ffffff",
    )
    map_data.boundary.plot(ax=map_ax, color="#555555", linewidth=0.13, alpha=0.55)
    plot_trajectory_markers(map_ax, map_data, size=38)
    map_ax.set_xlim(-10.2, 5.0)
    map_ax.set_ylim(35.0, 44.5)

    canary_codes = ["35", "38"]
    canary_ax = map_ax.inset_axes([0.035, 0.055, 0.22, 0.2])
    canary_map = map_data[map_data["COD_PROVINCIA"].isin(canary_codes)]
    canary_map.plot(
        ax=canary_ax,
        color=canary_map["growth_color"],
        linewidth=0.45,
        edgecolor="#ffffff",
    )
    canary_map.boundary.plot(ax=canary_ax, color="#555555", linewidth=0.16, alpha=0.65)
    plot_trajectory_markers(canary_ax, canary_map, size=34)
    canary_ax.set_xlim(-18.4, -13.1)
    canary_ax.set_ylim(27.55, 29.65)
    canary_ax.set_title("Canarias", fontsize=8.2, pad=2)
    canary_ax.set_xticks([])
    canary_ax.set_yticks([])
    for spine in canary_ax.spines.values():
        spine.set_edgecolor("#8c8c8c")
        spine.set_linewidth(0.8)

    top_labels = select_trajectory_highlights(map_data, limit=6)
    for _, row in top_labels.iterrows():
        label = f"{row['province_short']}\n{row['trajectory_letter']} · {row['rent_growth_total_pct']:+.1f}%"
        text = map_ax.annotate(
            label,
            xy=(row["label_lon"], row["label_lat"]),
            xytext=(7, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=6.8,
            color="#111111",
            zorder=5,
        )
        text.set_path_effects(
            [path_effects.withStroke(linewidth=2.5, foreground="white", alpha=0.96)]
        )

    legend_handles = [
        mpatches.Patch(facecolor=color, edgecolor="#666666", label=label)
        for color, label in zip(GROWTH_PALETTE, build_bin_labels(bins))
    ]
    if int((~map_data["has_growth_history"]).sum()):
        legend_handles.append(
            mpatches.Patch(
                facecolor=NO_DATA_COLOR,
                edgecolor="#777777",
                label="Sin historico comparable",
            )
        )
    color_legend = map_ax.legend(
        handles=legend_handles,
        title="Variacion total",
        loc="lower left",
        bbox_to_anchor=(0.0, 0.28),
        fontsize=7.6,
        title_fontsize=8.8,
        frameon=True,
        framealpha=0.96,
    )
    map_ax.add_artist(color_legend)
    symbol_legend = map_ax.legend(
        handles=trajectory_legend_handles(),
        title="Trayectoria",
        loc="lower right",
        fontsize=6.7,
        title_fontsize=7.8,
        frameon=True,
        framealpha=0.96,
    )
    map_ax.add_artist(symbol_legend)
    map_ax.set_title(
        "Trayectorias del alquiler: color = subida, simbolo = patron temporal",
        fontsize=14,
        fontweight="bold",
        pad=9,
    )
    window_text = (
        f"Comparacion exacta {start_year}-{current_year}"
        if not allow_first_available
        else f"Primer ano disponible desde {start_year} frente a {current_year}"
    )
    map_ax.text(
        0.01,
        0.94,
        window_text + ". Aceleracion = ritmo reciente menos ritmo 2011-2019.",
        transform=map_ax.transAxes,
        fontsize=8.5,
        color="#333333",
        ha="left",
    )
    map_ax.set_axis_off()

    summary_ax.set_axis_off()
    valid = map_data[map_data["has_growth_history"]].copy()
    leader = valid.nlargest(1, "rent_growth_total_pct").iloc[0]
    accelerator = valid.nlargest(1, "acceleration_pp_year").iloc[0]
    complete_pre = int(map_data["series_complete_2011_2019"].sum())
    no_history = int((~map_data["has_growth_history"]).sum())
    summary_ax.text(0.0, 0.98, "Lectura rapida", fontsize=11, fontweight="bold", va="top")
    summary_ax.text(
        0.0,
        0.58,
        f"{leader['province_short']} {leader['rent_growth_total_pct']:+.1f}%",
        fontsize=17,
        fontweight="bold",
    )
    summary_ax.text(
        0.0,
        0.35,
        f"Mayor subida acumulada ({leader['trajectory_class']}). Aceleracion maxima: "
        f"{accelerator['province_short']} {accelerator['acceleration_pp_year']:+.1f} pp/ano.",
        fontsize=8.8,
        color="#333333",
        wrap=True,
    )
    summary_ax.text(
        0.0,
        0.08,
        f"Series completas 2011-2019: {complete_pre}. Provincias sin historico comparable: {no_history}.",
        fontsize=8.1,
        color="#444444",
        wrap=True,
    )

    matrix_data = valid.dropna(subset=["acceleration_pp_year"]).copy()
    for trajectory in TRAJECTORY_ORDER:
        subset = matrix_data[matrix_data["trajectory_class"].eq(trajectory)]
        if subset.empty:
            continue
        style = TRAJECTORY_STYLES[trajectory]
        matrix_ax.scatter(
            subset["growth_total_pct"],
            subset["acceleration_pp_year"],
            s=42,
            marker=style["marker"],
            facecolor=style["fill"],
            edgecolor=style["color"],
            linewidth=0.8,
            alpha=0.88,
            label=trajectory,
        )
    matrix_ax.axhline(0, color="#666666", linewidth=0.8, linestyle="--")
    matrix_ax.axvline(valid["growth_total_pct"].median(), color="#999999", linewidth=0.8, linestyle=":")
    for _, row in top_labels.dropna(subset=["acceleration_pp_year"]).iterrows():
        matrix_ax.annotate(
            row["province_short"],
            xy=(row["growth_total_pct"], row["acceleration_pp_year"]),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=6.8,
            color="#222222",
        )
    matrix_ax.set_title("Matriz: subida total vs aceleracion", fontsize=11, fontweight="bold")
    matrix_ax.set_xlabel("Subida total (%)", fontsize=8.5)
    matrix_ax.set_ylabel("Aceleracion (pp/ano)", fontsize=8.5)
    matrix_ax.grid(color="#dddddd", linewidth=0.6)
    matrix_ax.tick_params(axis="both", labelsize=8)

    indexed = build_indexed_series(yearly, top_labels, current_year)
    if not indexed.empty:
        for province_name, subset in indexed.groupby("province_name"):
            line_ax.plot(
                subset["year"],
                subset["rent_index"],
                marker="o",
                linewidth=1.4,
                markersize=3.2,
                label=province_name,
            )
        line_ax.axhline(100, color="#555555", linewidth=0.8, linestyle="--")
        line_ax.set_title("Mini-series de trayectorias destacadas", fontsize=11, fontweight="bold")
        line_ax.set_ylabel("Indice, baseline = 100", fontsize=8.5)
        line_ax.set_xlabel("Ano", fontsize=8.5)
        line_ax.legend(loc="upper left", fontsize=6.8, frameon=False, ncol=2)
    else:
        line_ax.text(0.5, 0.5, "Sin series comparables", ha="center", va="center")
    line_ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    line_ax.tick_params(axis="both", labelsize=8)

    for side_ax in [matrix_ax, line_ax]:
        for spine in ["top", "right", "left"]:
            side_ax.spines[spine].set_visible(False)

    fig.suptitle(
        f"Mapa 2. Evolucion del alquiler provincial hasta {current_year}",
        fontsize=20,
        fontweight="bold",
        x=0.43,
        y=0.985,
    )
    fig.text(
        0.02,
        0.012,
        "Fuente: MIVAU, Sistema Estatal de Referencia del Precio del Alquiler; cartografia Eurostat/GISCO NUTS 2024.",
        fontsize=8.2,
        color="#4a4a4a",
    )
    fig.savefig(OUTPUT_DIR / "mapa2_evolucion_alquiler.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa2_evolucion_alquiler.pdf", bbox_inches="tight")
    plt.close(fig)


def province_popup_html(
    row: pd.Series,
    yearly: pd.DataFrame | None,
    average_series: pd.DataFrame | None,
    start_year: int,
) -> str:
    province = html.escape(str(row["province_name"]))
    note = html.escape(str(row["baseline_note"]))
    requested_window = f"desde {start_year}"
    if not row["has_growth_history"]:
        requested_window = "sin historico"

    chart = ""
    if yearly is not None and not yearly.empty:
        series = yearly[yearly["COD_PROVINCIA"].eq(row["COD_PROVINCIA"])]
        chart = evolution_chart_svg(series, average_series)

    return f"""
    <div class="evolution-popup-card" style="font-family: Arial, sans-serif; font-size: 12px;
      line-height: 1.35; min-width: 322px;">
      <strong style="font-size: 13px;">{province}</strong><br>
      <span>{row['analysis_window']} · {note}</span>
      <hr style="margin: 6px 0;">
      <div style="font-size:11px; font-weight:700; color:#333333;">Evolucion anual vs media estatal</div>
      {chart}
      <table>
        <tr><td>Alquiler inicial</td><td style="text-align:right; padding-left:12px;">{row['baseline_rent_label']}</td></tr>
        <tr><td>Alquiler final</td><td style="text-align:right; padding-left:12px;"><b>{row['current_rent_label']}</b></td></tr>
        <tr><td>Cambio absoluto</td><td style="text-align:right; padding-left:12px;">{row['rent_change_label']}</td></tr>
        <tr><td>Subida total</td><td style="text-align:right; padding-left:12px;"><b>{row['growth_total_label']}</b></td></tr>
        <tr><td>2021-final</td><td style="text-align:right; padding-left:12px;">{row['growth_recent_label']}</td></tr>
        <tr><td>Subida anualizada</td><td style="text-align:right; padding-left:12px;">{row['growth_annual_label']}</td></tr>
        <tr><td>Trayectoria</td><td style="text-align:right; padding-left:12px;">{row['trajectory_class']}</td></tr>
        <tr><td>Viviendas observadas final</td><td style="text-align:right; padding-left:12px;">{row['current_homes_label']}</td></tr>
        <tr><td>Municipios con dato final</td><td style="text-align:right; padding-left:12px;">{row['current_municipalities_label']}</td></tr>
      </table>
      <div style="margin-top:6px; color:#555;">Ventana solicitada: {requested_window}</div>
    </div>
    """


def add_growth_legend(web_map: folium.Map, bins: list[float], current_year: int) -> None:
    rows = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:6px; margin:3px 0;">
          <span style="width:18px; height:12px; display:inline-block; background:{color};
          border:1px solid rgba(0,0,0,0.35);"></span>
          <span>{label}</span>
        </div>
        """
        for color, label in zip(GROWTH_PALETTE, build_bin_labels(bins))
    )
    rows += f"""
        <div style="display:flex; align-items:center; gap:6px; margin:3px 0;">
          <span style="width:18px; height:12px; display:inline-block; background:{NO_DATA_COLOR};
          border:1px solid rgba(0,0,0,0.35);"></span>
          <span>Sin historico</span>
        </div>
    """
    legend_html = f"""
    <div style="
      position: fixed; top: 16px; right: 16px; z-index: 9999;
      background: rgba(255,255,255,0.94); padding: 9px 10px;
      border: 1px solid rgba(60,60,60,0.55); border-radius: 4px;
      font-family: Arial, sans-serif; font-size: 11.5px; line-height: 1.25;
      box-shadow: 0 1px 5px rgba(0,0,0,0.22);">
      <div style="font-size:12.5px; font-weight:700; margin-bottom:6px;">Subida total hasta {current_year}</div>
      {rows}
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(legend_html))


def add_trajectory_legend(web_map: folium.Map) -> None:
    rows = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:6px; margin:3px 0;">
          <span style="
            width:18px; height:18px; display:inline-flex; align-items:center; justify-content:center;
            color:white; font-weight:700; font-size:10px; background:{style['fill']};
            border:2px solid {style['color']}; border-radius:50%;">{style['letter']}</span>
          <span>{trajectory}</span>
        </div>
        """
        for trajectory, style in TRAJECTORY_STYLES.items()
    )
    legend_html = f"""
    <div style="
      position: fixed; top: 224px; right: 16px; z-index: 9999;
      background: rgba(255,255,255,0.94); padding: 9px 10px;
      border: 1px solid rgba(60,60,60,0.55); border-radius: 4px;
      font-family: Arial, sans-serif; font-size: 11.5px; line-height: 1.25;
      box-shadow: 0 1px 5px rgba(0,0,0,0.22);">
      <div style="font-size:12.5px; font-weight:700; margin-bottom:6px;">Patron temporal</div>
      {rows}
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(legend_html))


def build_temporal_styledict(
    map_data: gpd.GeoDataFrame,
    yearly: pd.DataFrame,
) -> dict[str, dict[str, dict[str, float | str]]]:
    if yearly.empty:
        return {}

    selected_codes = set(map_data["COD_PROVINCIA"])
    work = yearly[yearly["COD_PROVINCIA"].isin(selected_codes)].copy()
    first_values = work.sort_values("year").groupby("COD_PROVINCIA")["rent_eur_month"].first()
    work["first_rent"] = work["COD_PROVINCIA"].map(first_values)
    work["rent_index_first_year"] = work["rent_eur_month"] / work["first_rent"] * 100
    temporal_bins = [0, 100, 110, 120, 130, math.inf]

    styledict: dict[str, dict[str, dict[str, float | str]]] = {}
    for _, row in work.iterrows():
        timestamp = str(int(pd.Timestamp(year=int(row["year"]), month=1, day=1).timestamp()))
        styledict.setdefault(str(row["COD_PROVINCIA"]), {})[timestamp] = {
            "color": color_for_temporal_index(row["rent_index_first_year"], temporal_bins),
            "opacity": 0.68,
        }
    return styledict


def add_temporal_choropleth(
    web_map: folium.Map,
    map_data: gpd.GeoDataFrame,
    yearly: pd.DataFrame | None,
) -> None:
    if yearly is None or yearly.empty:
        return

    styledict = build_temporal_styledict(map_data, yearly)
    if not styledict:
        return

    geo_data = map_data.set_index("COD_PROVINCIA")[["geometry"]].to_json()
    plugins.TimeSliderChoropleth(
        data=geo_data,
        styledict=styledict,
        date_options="YYYY",
        name="Slider anual: indice desde primer ano",
        overlay=True,
        control=True,
        show=False,
        init_timestamp=-1,
        stroke_color="#777777",
        stroke_width=0.35,
        stroke_opacity=0.75,
    ).add_to(web_map)


def trajectory_popup_html(row: pd.Series, yearly: pd.DataFrame | None, start_year: int) -> str:
    province = html.escape(str(row["province_name"]))
    style = TRAJECTORY_STYLES[row["trajectory_class"]]
    sparkline = ""
    if yearly is not None and not yearly.empty:
        series = yearly[yearly["COD_PROVINCIA"].eq(row["COD_PROVINCIA"])]
        sparkline = sparkline_svg(series)

    return f"""
    <div style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.35; min-width: 260px;">
      <div style="display:flex; align-items:center; gap:7px;">
        <span style="
          width:22px; height:22px; display:inline-flex; align-items:center; justify-content:center;
          color:white; font-weight:700; font-size:11px; background:{style['fill']};
          border:2px solid {style['color']}; border-radius:50%;">{style['letter']}</span>
        <strong style="font-size: 13px;">{province}</strong>
      </div>
      <div style="margin-top:4px;">{row['trajectory_class']}</div>
      {sparkline}
      <table>
        <tr><td>Periodo</td><td style="text-align:right; padding-left:12px;">{row['analysis_window']}</td></tr>
        <tr><td>Subida total</td><td style="text-align:right; padding-left:12px;"><b>{row['growth_total_label']}</b></td></tr>
        <tr><td>2021-final</td><td style="text-align:right; padding-left:12px;">{row['growth_recent_label']}</td></tr>
        <tr><td>2011-2019</td><td style="text-align:right; padding-left:12px;">{row['growth_pre_label']}</td></tr>
        <tr><td>Aceleracion</td><td style="text-align:right; padding-left:12px;">{row['acceleration_label']}</td></tr>
        <tr><td>Alquiler final</td><td style="text-align:right; padding-left:12px;">{row['current_rent_label']}</td></tr>
      </table>
      <div style="margin-top:6px; color:#555;">Baseline solicitado: desde {start_year}. {row['trajectory_description']}</div>
    </div>
    """


def add_interactive_css(web_map: folium.Map) -> None:
    css = """
    <style>
      .trajectory-label-icon {
        background: transparent !important;
        border: 0 !important;
        pointer-events: none !important;
      }
      .trajectory-marker-icon {
        background: transparent !important;
        border: 0 !important;
      }
      .evolution-popup {
        margin: 0;
      }
      .evolution-popup .leaflet-popup-content {
        margin: 10px 12px;
      }
      .evolution-popup .leaflet-popup-content > div > table {
        margin: 0;
        width: auto;
      }
      .evolution-popup .leaflet-popup-content > div > table > tbody > tr > td {
        padding: 0;
      }
      .evolution-popup-card table {
        border-collapse: collapse;
        width: 100%;
      }
      .evolution-popup-card td {
        padding: 2px 0;
        vertical-align: top;
      }
    </style>
    """
    web_map.get_root().html.add_child(folium.Element(css))


def build_web_map(
    map_data: gpd.GeoDataFrame,
    bins: list[float],
    current_year: int,
    start_year: int,
    yearly: pd.DataFrame | None = None,
    top_n: int = 10,
) -> folium.Map:
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
    add_interactive_css(web_map)

    average_series = build_weighted_average_series(yearly)
    web_data = map_data.copy()
    web_data["popup_html"] = web_data.apply(
        lambda row: province_popup_html(row, yearly, average_series, start_year),
        axis=1,
    )

    growth_layer = folium.GeoJson(
        web_data,
        name="Variacion total del alquiler",
        style_function=lambda feature: {
            "fillColor": feature["properties"].get("growth_color", NO_DATA_COLOR),
            "color": "#575757",
            "weight": 0.45,
            "fillOpacity": 0.34
            if not feature["properties"].get("has_growth_history", False)
            else 0.84,
        },
        highlight_function=lambda _: {"weight": 2.1, "color": "#111111", "fillOpacity": 0.94},
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "province_name",
                "analysis_window",
                "growth_total_label",
                "growth_recent_label",
                "acceleration_label",
                "growth_annual_label",
                "current_rent_label",
                "trajectory_class",
            ],
            aliases=[
                "Provincia",
                "Periodo",
                "Subida total",
                "2021-final",
                "Aceleracion",
                "Subida anualizada",
                "Alquiler final",
                "Trayectoria",
            ],
            localize=True,
            labels=True,
            sticky=False,
        ),
        popup=folium.GeoJsonPopup(
            fields=["popup_html"],
            labels=False,
            localize=False,
            class_name="evolution-popup",
            max_width=380,
        ),
    ).add_to(web_map)

    label_layer = folium.FeatureGroup(name=f"Etiquetas top {top_n} trayectoria", show=True)
    top_rows = select_trajectory_highlights(map_data, limit=top_n)
    for _, row in top_rows.iterrows():
        label_html = f"""
        <div style="
          width: 104px; padding: 2px 5px;
          background: rgba(255, 255, 255, 0.90);
          border: 1px solid #444; border-radius: 3px;
          color: #111; font-family: Arial, sans-serif;
          font-size: 10px; font-weight: 700; line-height: 1.15;
          text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.25);
          pointer-events: none;">
          {html.escape(str(row['province_short']))}<br>{row['trajectory_letter']} · {row['rent_growth_total_pct']:+.1f}%
        </div>
        """
        folium.Marker(
            location=[row["label_lat"], row["label_lon"]],
            icon=folium.DivIcon(
                html=label_html,
                icon_size=(116, 32),
                icon_anchor=(-10, 16),
                class_name="trajectory-label-icon",
            ),
            interactive=False,
            z_index_offset=-500,
        ).add_to(label_layer)
    label_layer.add_to(web_map)

    trajectory_layer = folium.FeatureGroup(name="Simbolos de trayectoria", show=True)
    for _, row in map_data.iterrows():
        style = TRAJECTORY_STYLES[row["trajectory_class"]]
        marker_html = f"""
        <div style="
          width:22px; height:22px; display:flex; align-items:center; justify-content:center;
          color:white; font-family:Arial, sans-serif; font-size:11px; font-weight:700;
          background:{style['fill']}; border:2px solid {style['color']};
          border-radius:50%; box-shadow:0 1px 4px rgba(0,0,0,0.35);">
          {style['letter']}
        </div>
        """
        folium.Marker(
            location=[row["label_lat"], row["label_lon"]],
            icon=folium.DivIcon(
                html=marker_html,
                icon_size=(24, 24),
                icon_anchor=(12, 12),
                class_name="trajectory-marker-icon",
            ),
            tooltip=f"{row['province_name']}: {row['trajectory_class']} ({row['growth_total_label']})",
            popup=folium.Popup(trajectory_popup_html(row, yearly, start_year), max_width=360),
            z_index_offset=500,
        ).add_to(trajectory_layer)
    trajectory_layer.add_to(web_map)
    add_temporal_choropleth(web_map, map_data, yearly)

    no_history = int((~map_data["has_growth_history"]).sum())
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
      <strong>Mapa 2 · evolucion del alquiler</strong><br>
      Final: {current_year}; baseline desde {start_year}<br>
      Color = subida total; simbolo = trayectoria<br>
      Sin historico comparable: {no_history}
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(summary_html))
    add_growth_legend(web_map, bins, current_year)
    add_trajectory_legend(web_map)

    plugins.Search(
        layer=growth_layer,
        geom_type="Polygon",
        placeholder="Buscar provincia",
        collapsed=True,
        search_label="province_name",
        position="topleft",
    ).add_to(web_map)
    plugins.Fullscreen(position="topleft").add_to(web_map)
    plugins.MiniMap(toggle_display=True, minimized=True, position="bottomright").add_to(web_map)
    plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(web_map)
    folium.LayerControl(collapsed=True, position="bottomleft").add_to(web_map)
    return web_map


def save_interactive_map(
    map_data: gpd.GeoDataFrame,
    yearly: pd.DataFrame,
    current_year: int,
    bins: list[float],
    start_year: int,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    web_map = build_web_map(map_data, bins, current_year, start_year, yearly=yearly)
    web_map.save(OUTPUT_DIR / "mapa2_evolucion_alquiler_interactivo.html")


def save_tables(map_data: gpd.GeoDataFrame, yearly: pd.DataFrame, current_year: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    province_columns = [
        "COD_PROVINCIA",
        "province_name",
        "analysis_window",
        "baseline_note",
        "baseline_year",
        "current_year",
        "baseline_rent_eur_month",
        "current_rent_eur_month",
        "rent_change_eur_month",
        "rent_growth_total_pct",
        "rent_growth_annual_pct",
        "growth_total_pct",
        "growth_annual_pct",
        "recent_start_year",
        "recent_start_rent_eur_month",
        "growth_recent_pct",
        "growth_recent_annual_pct",
        "pre_start_year",
        "pre_end_year",
        "pre_start_rent_eur_month",
        "pre_end_rent_eur_month",
        "growth_pre_pct",
        "growth_pre_annual_pct",
        "acceleration_pp_year",
        "trajectory_class",
        "trajectory_description",
        "series_complete_2011_2019",
        "first_year_available",
        "years_available",
        "baseline_rental_homes",
        "current_rental_homes",
        "baseline_municipalities",
        "current_municipalities",
        "baseline_municipal_spread_eur",
        "current_municipal_spread_eur",
        "growth_class",
        "has_growth_history",
    ]
    map_data[province_columns].sort_values(
        "rent_growth_total_pct",
        ascending=False,
        na_position="last",
    ).to_csv(OUTPUT_DIR / "mapa2_evolucion_alquiler_datos.csv", index=False)

    yearly.sort_values(["COD_PROVINCIA", "year"]).to_csv(
        OUTPUT_DIR / "mapa2_evolucion_alquiler_serie_anual.csv",
        index=False,
    )

    indexed = build_indexed_series(
        yearly,
        map_data[map_data["has_growth_history"]],
        current_year,
    )
    indexed.to_csv(OUTPUT_DIR / "mapa2_evolucion_alquiler_serie_indexada.csv", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Genera el mapa 2 de evolucion del alquiler.")
    parser.add_argument(
        "--start-year",
        type=int,
        default=DEFAULT_START_YEAR,
        help="Ano inicial solicitado para la comparacion.",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help="Ano final. Si se omite, usa el ultimo disponible.",
    )
    parser.add_argument(
        "--exact-start",
        action="store_true",
        help="Usa solo provincias con dato exacto en start-year, sin fallback al primer ano posterior.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    allow_first_available = not args.exact_start
    map_data, yearly, current_year, bins = build_dataset(
        start_year=args.start_year,
        end_year=args.end_year,
        allow_first_available=allow_first_available,
    )
    save_static_map(
        map_data,
        yearly,
        current_year,
        bins,
        start_year=args.start_year,
        allow_first_available=allow_first_available,
    )
    save_interactive_map(map_data, yearly, current_year, bins, start_year=args.start_year)
    save_tables(map_data, yearly, current_year)

    valid = int(map_data["has_growth_history"].sum())
    no_history = int((~map_data["has_growth_history"]).sum())
    print(f"Mapa 2 generado con datos hasta {current_year}.")
    print(f"Provincias con historico comparable: {valid}.")
    print(f"Provincias sin historico comparable: {no_history}.")
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
