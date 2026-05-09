from __future__ import annotations

from calendar import monthrange
from html import escape
from math import ceil
from pathlib import Path
import json
import os
import sys
from time import sleep


BASE_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / ".matplotlib"))

proj_data = Path(sys.prefix) / "share" / "proj"
if proj_data.exists():
    os.environ.setdefault("PROJ_DATA", str(proj_data))
    os.environ.setdefault("PROJ_LIB", str(proj_data))

import branca.colormap as cm
import folium
from folium import plugins
import geopandas as gpd
import mapclassify
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import pandas as pd
import requests
from branca.element import MacroElement, Template


DATA_DIR = BASE_DIR / "datos"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"

NUTS_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson"
POWER_MONTHLY_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"

NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"
SEASONAL_TEMPERATURE_FILE = DATA_DIR / "nasa_power_temperatura_estacional_provincias_1995_2024.csv"
PRECIPITATION_FILE = DATA_DIR / "nasa_power_precipitacion_provincias_1995_2024.csv"

START_YEAR = 1995
END_YEAR = 2024
PRECIPITATION_PARAMETER = "PRECTOTCORR"

SEASONS = {
    "winter_c": {
        "label": "Invierno",
        "months": [12, 1, 2],
        "timestamp": "2024-01-15",
    },
    "spring_c": {
        "label": "Primavera",
        "months": [3, 4, 5],
        "timestamp": "2024-04-15",
    },
    "summer_c": {
        "label": "Verano",
        "months": [6, 7, 8],
        "timestamp": "2024-07-15",
    },
    "autumn_c": {
        "label": "Otono",
        "months": [9, 10, 11],
        "timestamp": "2024-10-15",
    },
}

MONTHS = {
    "jan_c": {"label": "Enero", "month": 1, "timestamp": "2024-01-15"},
    "feb_c": {"label": "Febrero", "month": 2, "timestamp": "2024-02-15"},
    "mar_c": {"label": "Marzo", "month": 3, "timestamp": "2024-03-15"},
    "apr_c": {"label": "Abril", "month": 4, "timestamp": "2024-04-15"},
    "may_c": {"label": "Mayo", "month": 5, "timestamp": "2024-05-15"},
    "jun_c": {"label": "Junio", "month": 6, "timestamp": "2024-06-15"},
    "jul_c": {"label": "Julio", "month": 7, "timestamp": "2024-07-15"},
    "aug_c": {"label": "Agosto", "month": 8, "timestamp": "2024-08-15"},
    "sep_c": {"label": "Septiembre", "month": 9, "timestamp": "2024-09-15"},
    "oct_c": {"label": "Octubre", "month": 10, "timestamp": "2024-10-15"},
    "nov_c": {"label": "Noviembre", "month": 11, "timestamp": "2024-11-15"},
    "dec_c": {"label": "Diciembre", "month": 12, "timestamp": "2024-12-15"},
}

MONTH_ABBREVIATIONS = {
    "jan_c": "Ene",
    "feb_c": "Feb",
    "mar_c": "Mar",
    "apr_c": "Abr",
    "may_c": "May",
    "jun_c": "Jun",
    "jul_c": "Jul",
    "aug_c": "Ago",
    "sep_c": "Sep",
    "oct_c": "Oct",
    "nov_c": "Nov",
    "dec_c": "Dic",
}

PRECIPITATION_MONTH_COLUMNS = {
    month_col: f"{month_col.replace('_c', '')}_precip_mm"
    for month_col in MONTHS
}

PALETTE = ["#2b83ba", "#abdda4", "#ffffbf", "#fdae61", "#d7191c"]
PRECIPITATION_PALETTE = ["#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"]

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

PROVINCE_NAME_BY_CODE = {
    "01": "Araba/Alava",
    "02": "Albacete",
    "03": "Alicante/Alacant",
    "04": "Almeria",
    "05": "Avila",
    "06": "Badajoz",
    "07": "Balears, Illes",
    "08": "Barcelona",
    "09": "Burgos",
    "10": "Caceres",
    "11": "Cadiz",
    "12": "Castellon/Castello",
    "13": "Ciudad Real",
    "14": "Cordoba",
    "15": "Coruna, A",
    "16": "Cuenca",
    "17": "Girona",
    "18": "Granada",
    "19": "Guadalajara",
    "20": "Gipuzkoa",
    "21": "Huelva",
    "22": "Huesca",
    "23": "Jaen",
    "24": "Leon",
    "25": "Lleida",
    "26": "Rioja, La",
    "27": "Lugo",
    "28": "Madrid",
    "29": "Malaga",
    "30": "Murcia",
    "31": "Navarra",
    "32": "Ourense",
    "33": "Asturias",
    "34": "Palencia",
    "35": "Palmas, Las",
    "36": "Pontevedra",
    "37": "Salamanca",
    "38": "Santa Cruz de Tenerife",
    "39": "Cantabria",
    "40": "Segovia",
    "41": "Sevilla",
    "42": "Soria",
    "43": "Tarragona",
    "44": "Teruel",
    "45": "Toledo",
    "46": "Valencia/Valencia",
    "47": "Valladolid",
    "48": "Bizkaia",
    "49": "Zamora",
    "50": "Zaragoza",
    "51": "Ceuta",
    "52": "Melilla",
}


def download_file(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    target.write_bytes(response.content)


def load_province_geometries() -> gpd.GeoDataFrame:
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])

    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    provinces = provinces[["COD_PROVINCIA", "geometry"]].copy()
    provinces["province_name"] = provinces["COD_PROVINCIA"].map(PROVINCE_NAME_BY_CODE)
    return provinces.to_crs("EPSG:4326")


def fetch_monthly_temperature(latitude: float, longitude: float) -> dict[str, float]:
    params = {
        "parameters": "T2M",
        "community": "SB",
        "longitude": round(longitude, 5),
        "latitude": round(latitude, 5),
        "start": START_YEAR,
        "end": END_YEAR,
        "format": "JSON",
    }
    response = requests.get(POWER_MONTHLY_URL, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    return payload["properties"]["parameter"]["T2M"]


def fetch_monthly_precipitation(latitude: float, longitude: float) -> dict[str, float]:
    params = {
        "parameters": PRECIPITATION_PARAMETER,
        "community": "SB",
        "longitude": round(longitude, 5),
        "latitude": round(latitude, 5),
        "start": START_YEAR,
        "end": END_YEAR,
        "format": "JSON",
    }
    response = requests.get(POWER_MONTHLY_URL, params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    return payload["properties"]["parameter"][PRECIPITATION_PARAMETER]


def weighted_mean_for_months(monthly_values: dict[str, float], months: list[int]) -> float:
    weighted_sum = 0.0
    total_days = 0

    for key, value in monthly_values.items():
        if value is None or float(value) <= -900:
            continue

        year = int(str(key)[:4])
        month = int(str(key)[4:6])
        if month not in months:
            continue

        days = monthrange(year, month)[1]
        weighted_sum += float(value) * days
        total_days += days

    if total_days == 0:
        raise ValueError("NASA POWER no devolvio valores mensuales validos.")

    return weighted_sum / total_days


def annual_precipitation_from_monthly(monthly_values: dict[str, float]) -> float:
    annual_totals: dict[int, float] = {}
    annual_days: dict[int, int] = {}

    for key, value in monthly_values.items():
        if value is None or float(value) <= -900:
            continue

        timestamp = str(key)
        if len(timestamp) < 6:
            continue

        year = int(timestamp[:4])
        month = int(timestamp[4:6])
        if month < 1 or month > 12:
            continue

        days = monthrange(year, month)[1]
        annual_totals[year] = annual_totals.get(year, 0.0) + float(value) * days
        annual_days[year] = annual_days.get(year, 0) + days

    complete_years = [
        annual_total
        for year, annual_total in annual_totals.items()
        if annual_days.get(year, 0) >= 365
    ]
    if not complete_years:
        raise ValueError("NASA POWER no devolvio valores mensuales de precipitacion validos.")

    return sum(complete_years) / len(complete_years)


def precipitation_summary_from_monthly(monthly_values: dict[str, float]) -> dict[str, float]:
    month_totals: dict[int, list[float]] = {month["month"]: [] for month in MONTHS.values()}

    for key, value in monthly_values.items():
        if value is None or float(value) <= -900:
            continue

        timestamp = str(key)
        if len(timestamp) < 6:
            continue

        year = int(timestamp[:4])
        month = int(timestamp[4:6])
        if month not in month_totals:
            continue

        days = monthrange(year, month)[1]
        month_totals[month].append(float(value) * days)

    month_values = {}
    for month_col, month in MONTHS.items():
        totals = month_totals[month["month"]]
        if not totals:
            raise ValueError("NASA POWER no devolvio valores mensuales de precipitacion validos.")
        month_values[PRECIPITATION_MONTH_COLUMNS[month_col]] = sum(totals) / len(totals)

    return {
        "precipitation_annual_mm": annual_precipitation_from_monthly(monthly_values),
        **month_values,
    }


def temperature_summary_from_monthly(monthly_values: dict[str, float]) -> dict[str, float]:
    month_values = {
        month_col: weighted_mean_for_months(monthly_values, [month["month"]])
        for month_col, month in MONTHS.items()
    }
    season_values = {
        season_col: weighted_mean_for_months(monthly_values, season["months"])
        for season_col, season in SEASONS.items()
    }
    annual_mean = weighted_mean_for_months(monthly_values, list(range(1, 13)))
    return {
        "annual_mean_c": annual_mean,
        **month_values,
        **season_values,
    }


def load_seasonal_temperature_by_province(provinces: gpd.GeoDataFrame) -> pd.DataFrame:
    required_columns = {"annual_mean_c", *SEASONS.keys(), *MONTHS.keys()}
    if SEASONAL_TEMPERATURE_FILE.exists() and SEASONAL_TEMPERATURE_FILE.stat().st_size > 0:
        cached = pd.read_csv(SEASONAL_TEMPERATURE_FILE, dtype={"COD_PROVINCIA": str})
        if required_columns.issubset(cached.columns):
            return cached

    rows = []
    points = provinces.copy()
    points["point"] = points.geometry.representative_point()

    for _, row in points.sort_values("COD_PROVINCIA").iterrows():
        point = row["point"]
        monthly_values = fetch_monthly_temperature(point.y, point.x)
        temperature_values = temperature_summary_from_monthly(monthly_values)

        rows.append(
            {
                "COD_PROVINCIA": row["COD_PROVINCIA"],
                "province_name": row["province_name"],
                "latitude": point.y,
                "longitude": point.x,
                **temperature_values,
                "start_year": START_YEAR,
                "end_year": END_YEAR,
            }
        )
        sleep(0.15)

    temperature = pd.DataFrame(rows)
    SEASONAL_TEMPERATURE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temperature.to_csv(SEASONAL_TEMPERATURE_FILE, index=False)
    return temperature


def load_precipitation_by_province(provinces: gpd.GeoDataFrame) -> pd.DataFrame:
    required_columns = {
        "precipitation_annual_mm",
        *PRECIPITATION_MONTH_COLUMNS.values(),
        "start_year",
        "end_year",
    }
    if PRECIPITATION_FILE.exists() and PRECIPITATION_FILE.stat().st_size > 0:
        cached = pd.read_csv(PRECIPITATION_FILE, dtype={"COD_PROVINCIA": str})
        if required_columns.issubset(cached.columns):
            return cached

    rows = []
    points = provinces.copy()
    points["point"] = points.geometry.representative_point()

    for _, row in points.sort_values("COD_PROVINCIA").iterrows():
        point = row["point"]
        monthly_values = fetch_monthly_precipitation(point.y, point.x)
        precipitation_values = precipitation_summary_from_monthly(monthly_values)

        rows.append(
            {
                "COD_PROVINCIA": row["COD_PROVINCIA"],
                "province_name": row["province_name"],
                "latitude": point.y,
                "longitude": point.x,
                **precipitation_values,
                "start_year": START_YEAR,
                "end_year": END_YEAR,
            }
        )
        sleep(0.15)

    precipitation = pd.DataFrame(rows)
    PRECIPITATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    precipitation.to_csv(PRECIPITATION_FILE, index=False)
    return precipitation


def add_climate_metrics(map_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    data = map_data.copy()
    projected = data.to_crs("EPSG:3035")
    month_cols = list(MONTHS.keys())
    data["area_km2"] = projected.area / 1_000_000
    data["monthly_std_c"] = data[month_cols].std(axis=1, ddof=0).round(2)
    data["monthly_range_c"] = (data[month_cols].max(axis=1) - data[month_cols].min(axis=1)).round(2)
    data["seasonal_range_c"] = data["summer_c"] - data["winter_c"]
    data["annual_anomaly_c"] = data["annual_mean_c"] - data["annual_mean_c"].mean()

    comfort_target = 17.0
    comfort_gap = (data["annual_mean_c"] - comfort_target).abs()
    data["climate_comfort_score"] = 100 * (1 - comfort_gap / comfort_gap.max())
    data["climate_comfort_score"] = data["climate_comfort_score"].round(1)
    return data


def build_dataset() -> gpd.GeoDataFrame:
    download_file(NUTS_URL, NUTS_FILE)

    provinces = load_province_geometries()
    temperature = load_seasonal_temperature_by_province(provinces)
    precipitation = load_precipitation_by_province(provinces)
    map_data = provinces.merge(
        temperature.drop(columns=["province_name"], errors="ignore"),
        on="COD_PROVINCIA",
        how="left",
    ).merge(
        precipitation.drop(
            columns=["province_name", "latitude", "longitude", "start_year", "end_year"],
            errors="ignore",
        ),
        on="COD_PROVINCIA",
        how="left",
    )

    missing = map_data[map_data["annual_mean_c"].isna() | map_data["precipitation_annual_mm"].isna()]
    if not missing.empty:
        missing_codes = ", ".join(missing["COD_PROVINCIA"].tolist())
        raise ValueError(f"Faltan datos climaticos para estas provincias: {missing_codes}")

    return add_climate_metrics(map_data)


def build_temperature_bins(map_data: gpd.GeoDataFrame) -> list[float]:
    values = pd.concat([map_data[col] for col in [*MONTHS.keys(), "annual_mean_c"]])
    classifier = mapclassify.NaturalBreaks(values, k=5)
    bins = [float(values.min())] + [float(value) for value in classifier.bins]
    bins[0] -= 0.1
    return bins


def build_precipitation_bins(map_data: gpd.GeoDataFrame) -> list[float]:
    values = pd.concat([map_data[col] for col in PRECIPITATION_MONTH_COLUMNS.values()])
    classifier = mapclassify.NaturalBreaks(values, k=5)
    bins = [float(values.min())] + [float(value) for value in classifier.bins]
    bins[0] -= 0.5
    return bins


def color_for_value(value: float, bins: list[float]) -> str:
    for index, upper in enumerate(bins[1:]):
        if value <= upper:
            return PALETTE[index]
    return PALETTE[-1]


def color_for_precipitation(value: float, bins: list[float]) -> str:
    for index, upper in enumerate(bins[1:]):
        if value <= upper:
            return PRECIPITATION_PALETTE[index]
    return PRECIPITATION_PALETTE[-1]


def scaled_radius(
    value: float,
    min_value: float,
    max_value: float,
    min_radius: float = 4.0,
    max_radius: float = 14.0,
) -> float:
    if max_value <= min_value:
        return (min_radius + max_radius) / 2
    return min_radius + (max_radius - min_radius) * (value - min_value) / (max_value - min_value)


def max_monthly_temperature_scale(map_data: gpd.GeoDataFrame) -> float:
    max_value = max(float(map_data[month_col].max()) for month_col in MONTHS)
    return float(max(5, ceil(max_value / 5) * 5))


def max_monthly_precipitation_scale(map_data: gpd.GeoDataFrame) -> float:
    max_value = max(float(map_data[precip_col].max()) for precip_col in PRECIPITATION_MONTH_COLUMNS.values())
    return float(max(25, ceil(max_value / 25) * 25))


def build_monthly_temperature_chart(
    row: pd.Series,
    bins: list[float],
    max_temp_scale: float,
) -> str:
    month_items = [
        (month_col, MONTH_ABBREVIATIONS[month_col], float(row[month_col]))
        for month_col in MONTHS
    ]
    hottest = max(month_items, key=lambda item: item[2])
    coldest = min(month_items, key=lambda item: item[2])

    bars = []
    month_labels = []
    for _, month_label, value in month_items:
        height = min(100.0, max(3.0, (value / max_temp_scale) * 100))
        color = color_for_value(value, bins)
        safe_month = escape(month_label)
        bars.append(
            f"""
            <div class="monthly-chart-bar-cell">
              <div class="monthly-chart-bar"
                   title="{safe_month}: {value:.1f} C"
                   style="height:{height:.1f}%; background:{color};"></div>
            </div>
            """
        )
        month_labels.append(f"<span>{safe_month}</span>")

    province_name = escape(str(row["province_name"]))
    hottest_label = escape(hottest[1])
    coldest_label = escape(coldest[1])

    return f"""
    <div class="monthly-chart-popup">
      <div class="monthly-chart-title">{province_name}</div>
      <div class="monthly-chart-subtitle">Temperatura media mensual {START_YEAR}-{END_YEAR}</div>
      <div class="monthly-chart-grid">
        <div class="monthly-chart-axis">
          <span>{max_temp_scale:.0f} C</span>
          <span>{max_temp_scale / 2:.0f} C</span>
          <span>0 C</span>
        </div>
        <div>
          <div class="monthly-chart-bars">{''.join(bars)}</div>
          <div class="monthly-chart-months">{''.join(month_labels)}</div>
        </div>
      </div>
      <div class="monthly-chart-stats">
        <div class="monthly-chart-stat"><span>Media</span><b>{row['annual_mean_c']:.1f} C</b></div>
        <div class="monthly-chart-stat"><span>Max</span><b>{hottest_label} {hottest[2]:.1f} C</b></div>
        <div class="monthly-chart-stat"><span>Min</span><b>{coldest_label} {coldest[2]:.1f} C</b></div>
        <div class="monthly-chart-stat"><span>Lluvia anual</span><b>{row['precipitation_annual_mm']:.0f} mm</b></div>
      </div>
    </div>
    """


def build_monthly_precipitation_chart(
    row: pd.Series,
    bins: list[float],
    max_precip_scale: float,
) -> str:
    month_items = [
        (
            PRECIPITATION_MONTH_COLUMNS[month_col],
            MONTH_ABBREVIATIONS[month_col],
            float(row[PRECIPITATION_MONTH_COLUMNS[month_col]]),
        )
        for month_col in MONTHS
    ]
    wettest = max(month_items, key=lambda item: item[2])
    driest = min(month_items, key=lambda item: item[2])
    monthly_mean = sum(item[2] for item in month_items) / len(month_items)

    bars = []
    month_labels = []
    for _, month_label, value in month_items:
        height = min(100.0, max(3.0, (value / max_precip_scale) * 100))
        color = color_for_precipitation(value, bins)
        safe_month = escape(month_label)
        bars.append(
            f"""
            <div class="monthly-chart-bar-cell">
              <div class="monthly-chart-bar"
                   title="{safe_month}: {value:.0f} mm"
                   style="height:{height:.1f}%; background:{color};"></div>
            </div>
            """
        )
        month_labels.append(f"<span>{safe_month}</span>")

    province_name = escape(str(row["province_name"]))
    wettest_label = escape(wettest[1])
    driest_label = escape(driest[1])

    return f"""
    <div class="monthly-chart-popup">
      <div class="monthly-chart-title">{province_name}</div>
      <div class="monthly-chart-subtitle">Precipitacion mensual {START_YEAR}-{END_YEAR}</div>
      <div class="monthly-chart-grid">
        <div class="monthly-chart-axis">
          <span>{max_precip_scale:.0f} mm</span>
          <span>{max_precip_scale / 2:.0f} mm</span>
          <span>0 mm</span>
        </div>
        <div>
          <div class="monthly-chart-bars">{''.join(bars)}</div>
          <div class="monthly-chart-months">{''.join(month_labels)}</div>
        </div>
      </div>
      <div class="monthly-chart-stats">
        <div class="monthly-chart-stat"><span>Anual</span><b>{row['precipitation_annual_mm']:.0f} mm</b></div>
        <div class="monthly-chart-stat"><span>Max</span><b>{wettest_label} {wettest[2]:.0f} mm</b></div>
        <div class="monthly-chart-stat"><span>Min</span><b>{driest_label} {driest[2]:.0f} mm</b></div>
        <div class="monthly-chart-stat"><span>Media mes</span><b>{monthly_mean:.0f} mm</b></div>
      </div>
    </div>
    """


def annotate_temperature_label(
    ax: plt.Axes,
    row: pd.Series,
    season_col: str,
    fontsize: float = 6.5,
) -> None:
    point = row.geometry.representative_point()
    label = f"{row['province_name']}\n{row[season_col]:.1f} C"
    text = ax.annotate(
        label,
        xy=(point.x, point.y),
        ha="center",
        va="center",
        fontsize=fontsize,
        color="#111111",
    )
    text.set_path_effects(
        [path_effects.withStroke(linewidth=2.2, foreground="white", alpha=0.95)]
    )


def plot_canary_inset(
    map_ax: plt.Axes,
    map_data: gpd.GeoDataFrame,
    season_col: str,
    bins: list[float],
    selected: gpd.GeoDataFrame,
) -> None:
    canary_codes = ["35", "38"]
    canary_map = map_data[map_data["COD_PROVINCIA"].isin(canary_codes)]
    if canary_map.empty:
        return

    canary_ax = map_ax.inset_axes([0.035, 0.055, 0.24, 0.2])
    canary_map.plot(
        column=season_col,
        ax=canary_ax,
        cmap="Spectral_r",
        scheme="UserDefined",
        classification_kwds={"bins": bins[1:]},
        linewidth=0.42,
        edgecolor="#ffffff",
        legend=False,
    )
    canary_map.boundary.plot(ax=canary_ax, color="#606060", linewidth=0.15, alpha=0.6)

    selected_canary = selected[selected["COD_PROVINCIA"].isin(canary_codes)]
    for _, row in selected_canary.iterrows():
        annotate_temperature_label(canary_ax, row, season_col, fontsize=5.9)

    canary_ax.set_xlim(-18.4, -13.1)
    canary_ax.set_ylim(27.55, 29.65)
    canary_ax.set_title("Canarias", fontsize=7.4, pad=1.8)
    canary_ax.set_xticks([])
    canary_ax.set_yticks([])
    for spine in canary_ax.spines.values():
        spine.set_edgecolor("#8c8c8c")
        spine.set_linewidth(0.75)


def save_static_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    bins = build_temperature_bins(map_data)
    fig = plt.figure(figsize=(16, 10), dpi=180)
    grid = fig.add_gridspec(
        2,
        3,
        width_ratios=[1.25, 1.25, 0.72],
        wspace=0.06,
        hspace=0.18,
    )
    axes = [
        fig.add_subplot(grid[0, 0]),
        fig.add_subplot(grid[0, 1]),
        fig.add_subplot(grid[1, 0]),
        fig.add_subplot(grid[1, 1]),
    ]
    rank_ax = fig.add_subplot(grid[:, 2])

    season_cols = list(SEASONS.keys())
    for ax, season_col in zip(axes, season_cols):
        season = SEASONS[season_col]
        map_data.plot(
            column=season_col,
            ax=ax,
            cmap="Spectral_r",
            scheme="UserDefined",
            classification_kwds={"bins": bins[1:]},
            linewidth=0.35,
            edgecolor="#ffffff",
            legend=False,
        )
        map_data.boundary.plot(ax=ax, color="#606060", linewidth=0.12, alpha=0.55)
        ax.set_title(season["label"], fontsize=12, fontweight="bold", pad=7)
        ax.set_xlim(-10.2, 5.0)
        ax.set_ylim(35.0, 44.5)
        ax.set_axis_off()

        selected = pd.concat([map_data.nlargest(1, season_col), map_data.nsmallest(1, season_col)])
        selected_main = selected[~selected["COD_PROVINCIA"].isin(["35", "38"])]
        for _, row in selected_main.iterrows():
            annotate_temperature_label(ax, row, season_col)
        plot_canary_inset(ax, map_data, season_col, bins, selected)

    ranking = map_data.nlargest(10, "climate_comfort_score").sort_values("climate_comfort_score")
    rank_ax.barh(ranking["province_name"], ranking["climate_comfort_score"], color="#4c956c")
    rank_ax.set_xlim(0, 100)
    rank_ax.set_title("Top confort anual", fontsize=11.5, fontweight="bold", pad=8)
    rank_ax.set_xlabel("Indice 0-100", fontsize=8.5)
    rank_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    rank_ax.tick_params(axis="both", labelsize=7.6)
    for spine in ["top", "right", "left"]:
        rank_ax.spines[spine].set_visible(False)

    fig.suptitle(
        f"Mapa 5. Confort climatico por epoca del ano ({START_YEAR}-{END_YEAR})",
        fontsize=18,
        fontweight="bold",
        y=0.98,
    )
    fig.text(
        0.02,
        0.02,
        "Fuente: NASA POWER T2M mensual y Eurostat/GISCO NUTS3. Coropletas con 5 cortes naturales. Ranking calculado sobre temperatura media anual.",
        fontsize=8,
        color="#555555",
    )

    fig.savefig(OUTPUT_DIR / "mapa5_confort_climatico_estacional.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa5_confort_climatico_estacional.pdf", bbox_inches="tight")
    plt.close(fig)


def timestamp_to_epoch(timestamp: str) -> int:
    return int(pd.Timestamp(timestamp).timestamp())


def build_slider_style(map_data: gpd.GeoDataFrame, bins: list[float]) -> dict[str, dict[str, dict[str, object]]]:
    style_dict: dict[str, dict[str, dict[str, object]]] = {}
    for _, row in map_data.iterrows():
        province_styles = {}
        for month_col, month in MONTHS.items():
            epoch = str(timestamp_to_epoch(month["timestamp"]))
            month_color = color_for_value(float(row[month_col]), bins)
            # TimeSliderChoropleth usa "color" y "opacity" para el relleno dinamico.
            province_styles[epoch] = {
                "color": month_color,
                "opacity": 0.78,
                "weight": 0.65,
                "fillColor": month_color,
                "fillOpacity": 0.78,
            }
        style_dict[row["COD_PROVINCIA"]] = province_styles
    return style_dict


def build_precipitation_slider_style(
    map_data: gpd.GeoDataFrame,
    bins: list[float],
) -> dict[str, dict[str, dict[str, object]]]:
    style_dict: dict[str, dict[str, dict[str, object]]] = {}
    for _, row in map_data.iterrows():
        province_styles = {}
        for month_col, month in MONTHS.items():
            precip_col = PRECIPITATION_MONTH_COLUMNS[month_col]
            epoch = str(timestamp_to_epoch(month["timestamp"]))
            month_color = color_for_precipitation(float(row[precip_col]), bins)
            province_styles[epoch] = {
                "color": month_color,
                "opacity": 0.82,
                "weight": 0.65,
                "fillColor": month_color,
                "fillOpacity": 0.82,
            }
        style_dict[row["COD_PROVINCIA"]] = province_styles
    return style_dict


class SeasonTemperatureLabels(MacroElement):
    _template = Template(
        """
        {% macro header(this, kwargs) %}
        <style>
          #{{ this._parent.get_name() }} .season-temp-label-wrapper {
            background: transparent;
            border: 0;
          }

          #{{ this._parent.get_name() }} .season-temp-label {
            min-width: 34px;
            padding: 1px 4px;
            border-radius: 3px;
            background: rgba(255, 255, 255, 0.88);
            box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.28);
            color: #111111;
            font-family: Arial, sans-serif;
            font-size: 10px;
            font-weight: 700;
            line-height: 1.25;
            text-align: center;
            white-space: nowrap;
          }

          #{{ this._parent.get_name() }}.dark-base-active .season-temp-label {
            background: rgba(28, 28, 28, 0.84);
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.48);
            color: #ffffff;
          }

          #{{ this._parent.get_name() }}.dark-base-active .legend.leaflet-control {
            background: rgba(24, 24, 24, 0.88);
            border-radius: 4px;
            box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.32);
          }

          #{{ this._parent.get_name() }}.dark-base-active .legend.leaflet-control text {
            fill: #ffffff;
          }

          #{{ this._parent.get_name() }}.dark-base-active .legend.leaflet-control path,
          #{{ this._parent.get_name() }}.dark-base-active .legend.leaflet-control line {
            stroke: #ffffff;
          }

          #{{ this._parent.get_name() }}.dark-base-active .legend.leaflet-control .caption {
            fill: #ffffff;
          }
        </style>
        {% endmacro %}

        {% macro script(this, kwargs) %}
        (function () {
          const map = {{ this._parent.get_name() }};
          const labelData = {{ this.label_data|tojson }};
          const timestamps = {{ this.timestamps|tojson }};
          const sliderId = "slider_{{ this.slider_name }}";
          const labels = L.layerGroup().addTo(map);
          const markers = {};

          function labelHtml(value) {
            return '<div class="season-temp-label">' + Number(value).toFixed(1) + ' C</div>';
          }

          function makeIcon(value) {
            return L.divIcon({
              className: "season-temp-label-wrapper",
              html: labelHtml(value),
              iconSize: [42, 18],
              iconAnchor: [21, 36]
            });
          }

          function updateLabels(timestamp) {
            labelData.forEach(function (item) {
              if (markers[item.code] && item.values[timestamp] !== undefined) {
                markers[item.code].setIcon(makeIcon(item.values[timestamp]));
              }
            });
          }

          labelData.forEach(function (item) {
            const firstValue = item.values[timestamps[0]];
            markers[item.code] = L.marker([item.lat, item.lng], {
              icon: makeIcon(firstValue),
              interactive: false,
              keyboard: false,
              zIndexOffset: 900
            }).addTo(labels);
          });

          function bindSlider() {
            const slider = document.querySelector("#" + sliderId + " input");
            if (!slider) {
              window.setTimeout(bindSlider, 150);
              return;
            }

            slider.addEventListener("input", function () {
              updateLabels(timestamps[Number(this.value)]);
            });
            updateLabels(timestamps[Number(slider.value || 0)]);
          }

          map.on("baselayerchange", function (event) {
            map.getContainer().classList.toggle("dark-base-active", event.name === "Base oscura");
          });

          map.on("climatemodechange", function (event) {
            if (event.mode === "temperature") {
              if (!map.hasLayer(labels)) {
                labels.addTo(map);
              }
            } else if (map.hasLayer(labels)) {
              map.removeLayer(labels);
            }
          });

          bindSlider();
        })();
        {% endmacro %}
        """
    )

    def __init__(self, map_data: gpd.GeoDataFrame, slider_name: str):
        super().__init__()
        self._name = "SeasonTemperatureLabels"
        self.slider_name = slider_name
        self.timestamps = [str(timestamp_to_epoch(month["timestamp"])) for month in MONTHS.values()]
        self.label_data = self._build_label_data(map_data)

    def _build_label_data(self, map_data: gpd.GeoDataFrame) -> list[dict[str, object]]:
        rows = []
        for _, row in map_data.iterrows():
            values = {
                str(timestamp_to_epoch(month["timestamp"])): round(float(row[month_col]), 1)
                for month_col, month in MONTHS.items()
            }
            rows.append(
                {
                    "code": row["COD_PROVINCIA"],
                    "lat": float(row["latitude"]),
                    "lng": float(row["longitude"]),
                    "values": values,
                }
            )
        return rows


def add_monthly_chart_styles(web_map: folium.Map) -> None:
    css = """
    <style>
      .monthly-chart-popup {
        width: 360px;
        max-width: calc(100vw - 72px);
        color: #1f2933;
        font-family: Arial, sans-serif;
      }

      .monthly-chart-title {
        color: #111111;
        font-size: 15px;
        font-weight: 700;
        line-height: 1.2;
        margin-bottom: 2px;
      }

      .monthly-chart-subtitle {
        color: #59636e;
        font-size: 11px;
        margin-bottom: 8px;
      }

      .monthly-chart-grid {
        display: grid;
        grid-template-columns: 34px minmax(0, 1fr);
        column-gap: 8px;
        align-items: stretch;
      }

      .monthly-chart-axis {
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 4px 0 18px;
        color: #68727d;
        font-size: 10px;
        text-align: right;
      }

      .monthly-chart-bars {
        height: 140px;
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: 4px;
        align-items: end;
        padding: 4px 3px 0;
        border-left: 1px solid #c8d0d8;
        border-bottom: 1px solid #8d98a3;
        background:
          linear-gradient(to bottom, rgba(141, 152, 163, 0.2) 1px, transparent 1px) 0 4px / 100% 50%;
      }

      .monthly-chart-bar-cell {
        height: 100%;
        min-width: 0;
        display: flex;
        align-items: flex-end;
        justify-content: center;
      }

      .monthly-chart-bar {
        width: 100%;
        max-width: 16px;
        min-height: 3px;
        border: 1px solid rgba(0, 0, 0, 0.18);
        border-radius: 2px 2px 0 0;
        box-sizing: border-box;
      }

      .monthly-chart-months {
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: 4px;
        margin-top: 3px;
        color: #46515c;
        font-size: 9px;
        line-height: 1.1;
        text-align: center;
      }

      .monthly-chart-stats {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 6px;
        margin-top: 9px;
        font-size: 11px;
      }

      .monthly-chart-stat {
        padding: 5px 6px;
        background: #f6f8fa;
        border: 1px solid #d8dee4;
        border-radius: 4px;
      }

      .monthly-chart-stat span {
        display: block;
        color: #59636e;
      }

      .monthly-chart-stat b {
        display: block;
        color: #111111;
        font-size: 12px;
        line-height: 1.2;
        white-space: nowrap;
      }

      .folium-monthly-chart-popup table,
      .folium-monthly-chart-popup tr,
      .folium-monthly-chart-popup td {
        margin: 0;
        padding: 0;
        border: 0;
      }

      .climate-detail-tooltip-wrapper {
        background: rgba(255, 255, 255, 0.96);
        border: 1px solid rgba(31, 41, 51, 0.28);
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.16);
        color: #1f2933;
      }

      .climate-detail-tooltip {
        min-width: 205px;
        font-family: Arial, sans-serif;
        font-size: 11px;
        line-height: 1.25;
      }

      .climate-detail-tooltip-title {
        margin-bottom: 5px;
        font-size: 12px;
        font-weight: 700;
      }

      .climate-detail-tooltip table {
        width: 100%;
        border-collapse: collapse;
      }

      .climate-detail-tooltip td {
        padding: 1px 0;
        white-space: nowrap;
      }

      .climate-detail-tooltip td:last-child {
        padding-left: 10px;
        font-weight: 700;
        text-align: right;
      }

      .rain-weather-wrapper {
        background: transparent;
        border: 0;
      }

      .rain-weather-icon {
        --rain-scale: 1;
        width: 54px;
        min-height: 46px;
        transform: scale(var(--rain-scale));
        transform-origin: center center;
        color: #12365a;
        font-family: Arial, sans-serif;
        pointer-events: none;
        text-align: center;
      }

      .weather-symbol {
        position: relative;
        width: 44px;
        height: 31px;
        margin: 0 auto;
        overflow: visible;
      }

      .weather-sun {
        position: absolute;
        top: 3px;
        left: 50%;
        width: 19px;
        height: 19px;
        transform: translateX(-50%);
        border: 2px solid #f08a24;
        border-radius: 50%;
        background: #ffd34d;
        box-shadow:
          0 0 0 4px rgba(255, 211, 77, 0.35),
          0 1px 3px rgba(0,0,0,0.22);
      }

      .weather-symbol.partly .weather-sun {
        top: 1px;
        left: 6px;
        transform: none;
      }

      .rain-cloud {
        position: relative;
        width: 32px;
        height: 17px;
        margin: 0 auto;
        border-radius: 16px;
        background: #f8fbff;
        border: 2px solid #1f78b4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.24);
      }

      .rain-cloud::before,
      .rain-cloud::after {
        content: "";
        position: absolute;
        bottom: 7px;
        border-radius: 50%;
        background: #f8fbff;
        border: 2px solid #1f78b4;
        border-bottom: 0;
      }

      .rain-cloud::before {
        left: 5px;
        width: 12px;
        height: 12px;
      }

      .rain-cloud::after {
        right: 5px;
        width: 15px;
        height: 15px;
      }

      .weather-symbol.partly .rain-cloud {
        position: absolute;
        top: 13px;
        right: 2px;
        margin: 0;
        transform: scale(0.86);
        transform-origin: center center;
      }

      .weather-symbol.rainy .rain-cloud {
        margin-top: 3px;
      }

      .rain-drops {
        display: flex;
        justify-content: center;
        gap: 3px;
        height: 10px;
        margin-top: 1px;
      }

      .rain-drops span {
        width: 3px;
        height: 9px;
        border-radius: 999px;
        background: #1f78b4;
        transform: rotate(14deg);
      }

      .rain-mm {
        display: inline-block;
        margin-top: 1px;
        padding: 1px 3px;
        border-radius: 3px;
        background: rgba(255,255,255,0.9);
        color: #0f2d4a;
        font-size: 10px;
        font-weight: 700;
        line-height: 1.15;
        box-shadow: 0 0 0 1px rgba(31,120,180,0.25);
        white-space: nowrap;
      }
    </style>
    """
    web_map.get_root().header.add_child(folium.Element(css))


def add_season_panel(web_map: folium.Map) -> None:
    html = """
    <div style="
      position: fixed; bottom: 28px; left: 28px; z-index: 9999;
      background: rgba(255,255,255,0.94); padding: 10px 12px;
      border: 1px solid #999; border-radius: 4px;
      font-family: Arial, sans-serif; font-size: 12px; line-height: 1.35;
      box-shadow: 0 1px 5px rgba(0,0,0,0.25);">
      <b>Slider mensual</b><br>
      Recorre enero-diciembre.<br>
      Numeros: mes activo.<br>
      Click provincia: grafico mensual.<br>
      Switch: temperatura o lluvia.<br>
      Puntos: tamano = dispersion mensual.
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(html))


def add_dispersion_legend(web_map: folium.Map, map_data: gpd.GeoDataFrame) -> None:
    min_std = float(map_data["monthly_std_c"].min())
    median_std = float(map_data["monthly_std_c"].median())
    max_std = float(map_data["monthly_std_c"].max())
    legend_values = [
        ("Baja", min_std),
        ("Media", median_std),
        ("Alta", max_std),
    ]
    rows = []
    for label, value in legend_values:
        radius = scaled_radius(value, min_std, max_std)
        diameter = radius * 2
        rows.append(
            f"""
            <div style="display:flex; align-items:center; gap:8px; margin:4px 0;">
              <span style="
                width:{diameter:.1f}px; height:{diameter:.1f}px;
                border-radius:50%; display:inline-block;
                background:rgba(45, 123, 182, 0.42);
                border:1.5px solid #ffffff;
                box-shadow:0 0 0 1px rgba(0,0,0,0.35);"></span>
              <span>{label}: {value:.1f} C</span>
            </div>
            """
        )

    html = f"""
    <div style="
      position: fixed; bottom: 130px; left: 28px; z-index: 9999;
      background: rgba(255,255,255,0.94); padding: 10px 12px;
      border: 1px solid #999; border-radius: 4px;
      font-family: Arial, sans-serif; font-size: 12px; line-height: 1.35;
      box-shadow: 0 1px 5px rgba(0,0,0,0.25);">
      <b>Dispersion mensual</b><br>
      Desviacion tipica de los 12 meses.<br>
      {''.join(rows)}
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(html))


class RainWeatherIcons(MacroElement):
    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function () {
          const map = {{ this._parent.get_name() }};
          const iconData = {{ this.icon_data|tojson }};
          const timestamps = {{ this.timestamps|tojson }};
          const sliderId = "slider_{{ this.slider_name }}";
          const minValue = {{ this.min_value }};
          const maxValue = {{ this.max_value }};
          const icons = L.layerGroup();
          const markers = {};

          function ratio(value) {
            if (maxValue <= minValue) {
              return 0.5;
            }
            return Math.max(0, Math.min(1, (value - minValue) / (maxValue - minValue)));
          }

          function dropCount(value) {
            return Math.max(1, Math.min(4, Math.floor(ratio(value) * 4) + 1));
          }

          function rainHtml(value) {
            const numericValue = Number(value);
            const valueRatio = ratio(numericValue);
            const scale = 0.72 + (1.18 - 0.72) * valueRatio;
            let symbol = "";

            if (numericValue < 20) {
              symbol = `
                <div class="weather-symbol sunny">
                  <div class="weather-sun"></div>
                </div>
              `;
            } else if (numericValue < 50) {
              symbol = `
                <div class="weather-symbol partly">
                  <div class="weather-sun"></div>
                  <div class="rain-cloud"></div>
                </div>
              `;
            } else {
              let drops = "";
              for (let index = 0; index < dropCount(numericValue); index += 1) {
                drops += "<span></span>";
              }
              symbol = `
                <div class="weather-symbol rainy">
                  <div class="rain-cloud"></div>
                  <div class="rain-drops">${drops}</div>
                </div>
              `;
            }

            return `
              <div class="rain-weather-icon" style="--rain-scale:${scale.toFixed(2)};">
                ${symbol}
                <div class="rain-mm">${numericValue.toFixed(0)} mm</div>
              </div>
            `;
          }

          function makeIcon(value) {
            return L.divIcon({
              className: "rain-weather-wrapper",
              html: rainHtml(value),
              iconSize: [54, 46],
              iconAnchor: [27, 23]
            });
          }

          function updateIcons(timestamp) {
            iconData.forEach(function (item) {
              if (markers[item.code] && item.values[timestamp] !== undefined) {
                markers[item.code].setIcon(makeIcon(item.values[timestamp]));
              }
            });
          }

          iconData.forEach(function (item) {
            const firstValue = item.values[timestamps[0]];
            markers[item.code] = L.marker([item.lat, item.lng], {
              icon: makeIcon(firstValue),
              interactive: false,
              keyboard: false,
              zIndexOffset: 950
            }).addTo(icons);
          });

          function bindSlider() {
            const slider = document.querySelector("#" + sliderId + " input");
            if (!slider) {
              window.setTimeout(bindSlider, 150);
              return;
            }

            if (slider.dataset.rainIconsBound !== "1") {
              slider.addEventListener("input", function () {
                updateIcons(timestamps[Number(this.value)]);
              });
              slider.dataset.rainIconsBound = "1";
            }
            updateIcons(timestamps[Number(slider.value || 0)]);
          }

          map.on("climatemodechange", function (event) {
            if (event.mode === "precipitation") {
              if (!map.hasLayer(icons)) {
                icons.addTo(map);
              }
              bindSlider();
            } else if (map.hasLayer(icons)) {
              map.removeLayer(icons);
            }
          });
        })();
        {% endmacro %}
        """
    )

    def __init__(self, map_data: gpd.GeoDataFrame, slider_name: str):
        super().__init__()
        self._name = "RainWeatherIcons"
        self.slider_name = slider_name
        self.timestamps = [str(timestamp_to_epoch(month["timestamp"])) for month in MONTHS.values()]
        monthly_values = pd.concat(
            [map_data[col] for col in PRECIPITATION_MONTH_COLUMNS.values()]
        )
        self.min_value = float(monthly_values.min())
        self.max_value = float(monthly_values.max())
        self.icon_data = self._build_icon_data(map_data)

    def _build_icon_data(self, map_data: gpd.GeoDataFrame) -> list[dict[str, object]]:
        rows = []
        for _, row in map_data.iterrows():
            values = {
                str(timestamp_to_epoch(month["timestamp"])): round(
                    float(row[PRECIPITATION_MONTH_COLUMNS[month_col]]),
                    1,
                )
                for month_col, month in MONTHS.items()
            }
            rows.append(
                {
                    "code": row["COD_PROVINCIA"],
                    "lat": float(row["latitude"]),
                    "lng": float(row["longitude"]),
                    "values": values,
                }
            )
        return rows


class ClimateDetailContent(MacroElement):
    _template = Template(
        """
        {% macro script(this, kwargs) %}
        (function () {
          const map = {{ this._parent.get_name() }};
          const detailLayer = {{ this.detail_layer_name }};
          const temperatureRows = {{ this.temperature_rows|tojson }};
          const precipitationRows = {{ this.precipitation_rows|tojson }};
          let currentMode = "temperature";

          function escapeHtml(value) {
            return String(value)
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
          }

          function formatNumber(value, decimals) {
            const number = Number(value);
            if (!Number.isFinite(number)) {
              return "sin dato";
            }
            return number.toLocaleString("es-ES", {
              minimumFractionDigits: decimals,
              maximumFractionDigits: decimals
            });
          }

          function buildRows(properties, rows) {
            return rows.map(function (row) {
              const value = formatNumber(properties[row.field], row.decimals) + row.unit;
              return `<tr><td>${escapeHtml(row.label)}</td><td>${escapeHtml(value)}</td></tr>`;
            }).join("");
          }

          function buildTooltip(properties) {
            const rows = currentMode === "precipitation" ? precipitationRows : temperatureRows;
            return `
              <div class="climate-detail-tooltip">
                <div class="climate-detail-tooltip-title">${escapeHtml(properties.province_name)}</div>
                <table><tbody>${buildRows(properties, rows)}</tbody></table>
              </div>
            `;
          }

          function buildPopup(layer) {
            const properties = layer.feature.properties;
            if (currentMode === "precipitation") {
              return properties.monthly_precipitation_chart_html;
            }
            return properties.monthly_chart_html;
          }

          detailLayer.eachLayer(function (layer) {
            layer.unbindTooltip();
            layer.unbindPopup();
            layer.bindTooltip(function (activeLayer) {
              return buildTooltip(activeLayer.feature.properties);
            }, {
              sticky: false,
              direction: "auto",
              opacity: 0.96,
              className: "climate-detail-tooltip-wrapper"
            });
            layer.bindPopup(function (activeLayer) {
              return buildPopup(activeLayer);
            }, {
              maxWidth: 390,
              className: "folium-monthly-chart-popup"
            });
          });

          map.on("climatemodechange", function (event) {
            currentMode = event.mode === "precipitation" ? "precipitation" : "temperature";
            map.closePopup();
          });
        })();
        {% endmacro %}
        """
    )

    def __init__(self, detail_layer_name: str):
        super().__init__()
        self._name = "ClimateDetailContent"
        self.detail_layer_name = detail_layer_name
        self.temperature_rows = [
            {"label": "Media anual", "field": "annual_mean_c", "decimals": 1, "unit": " C"},
            {"label": "Dispersion mensual", "field": "monthly_std_c", "decimals": 1, "unit": " C"},
            *[
                {"label": month["label"], "field": month_col, "decimals": 1, "unit": " C"}
                for month_col, month in MONTHS.items()
            ],
        ]
        self.precipitation_rows = [
            {"label": "Precipitacion anual", "field": "precipitation_annual_mm", "decimals": 0, "unit": " mm"},
            *[
                {
                    "label": month["label"],
                    "field": PRECIPITATION_MONTH_COLUMNS[month_col],
                    "decimals": 0,
                    "unit": " mm",
                }
                for month_col, month in MONTHS.items()
            ],
        ]


class ClimateModeSwitch(MacroElement):
    _template = Template(
        """
        {% macro header(this, kwargs) %}
        <style>
          #{{ this.panel_id }} {
            position: fixed;
            top: 50%;
            right: 18px;
            transform: translateY(-50%);
            z-index: 9999;
            width: 210px;
            background: rgba(255,255,255,0.94);
            border: 1px solid #999;
            border-radius: 4px;
            box-shadow: 0 1px 5px rgba(0,0,0,0.25);
            color: #1f2933;
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.35;
            padding: 10px 12px;
          }

          #{{ this.panel_id }} .mode-title {
            font-weight: 700;
            margin-bottom: 7px;
          }

          #{{ this.panel_id }} .mode-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4px;
          }

          #{{ this.panel_id }} .mode-button {
            cursor: pointer;
            border: 1px solid #9aa7b2;
            border-radius: 4px;
            background: #f6f8fa;
            color: #1f2933;
            font: inherit;
            font-weight: 700;
            padding: 5px 6px;
          }

          #{{ this.panel_id }} .mode-button.active {
            background: #1f78b4;
            border-color: #155f91;
            color: #ffffff;
          }

          #{{ this.panel_id }} .precip-legend {
            display: none;
            margin-top: 9px;
          }

          #{{ this.panel_id }} .precip-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 5px;
          }

          #{{ this.panel_id }} .precip-swatch {
            width: 34px;
            height: 12px;
            border: 1px solid rgba(0,0,0,0.25);
            border-radius: 2px;
            display: inline-block;
          }

          #{{ this.panel_id }} .precip-note {
            color: #59636e;
            font-size: 11px;
            margin-top: 6px;
          }
        </style>
        {% endmacro %}

        {% macro html(this, kwargs) %}
        <div id="{{ this.panel_id }}">
          <div class="mode-title">Pintar por</div>
          <div class="mode-buttons">
            <button type="button" class="mode-button active" data-mode="temperature">Temperatura</button>
            <button type="button" class="mode-button" data-mode="precipitation">Lluvia</button>
          </div>
          <div class="precip-legend">
            <b>Precipitacion mensual</b>
            {{ this.rows|safe }}
            <div class="precip-note">Iconos: mm del mes activo, media {{ this.start_year }}-{{ this.end_year }}.</div>
          </div>
        </div>
        {% endmacro %}

        {% macro script(this, kwargs) %}
        (function () {
          const map = {{ this._parent.get_name() }};
          const panel = document.getElementById("{{ this.panel_id }}");
          const temperatureLayer = {{ this.temperature_layer_name }};
          const precipitationLayer = {{ this.precipitation_layer_name }};
          const annualLayer = {{ this.annual_layer_name }};
          const detailLayer = {{ this.detail_layer_name }};
          const buttons = panel.querySelectorAll(".mode-button");
          const precipLegend = panel.querySelector(".precip-legend");

          function setLayer(layer, visible) {
            if (visible && !map.hasLayer(layer)) {
              layer.addTo(map);
            } else if (!visible && map.hasLayer(layer)) {
              map.removeLayer(layer);
            }
          }

          function keepDetailLayerVisible() {
            if (!map.hasLayer(detailLayer)) {
              detailLayer.addTo(map);
            }
            if (typeof detailLayer.bringToFront === "function") {
              detailLayer.bringToFront();
            }
          }

          function setTemperatureLegend(visible) {
            document.querySelectorAll(".legend.leaflet-control").forEach(function (legend) {
              legend.style.display = visible ? "" : "none";
            });
          }

          function setMode(mode) {
            const precipitationMode = mode === "precipitation";
            setLayer(temperatureLayer, !precipitationMode);
            setLayer(annualLayer, !precipitationMode);
            setLayer(precipitationLayer, precipitationMode);
            keepDetailLayerVisible();
            setTemperatureLegend(!precipitationMode);
            precipLegend.style.display = precipitationMode ? "block" : "none";

            buttons.forEach(function (button) {
              button.classList.toggle("active", button.dataset.mode === mode);
            });

            map.fire("climatemodechange", {mode: mode});
          }

          buttons.forEach(function (button) {
            button.addEventListener("click", function () {
              setMode(button.dataset.mode);
            });
          });

          setMode("temperature");
        })();
        {% endmacro %}
        """
    )

    def __init__(
        self,
        temperature_layer_name: str,
        precipitation_layer_name: str,
        annual_layer_name: str,
        detail_layer_name: str,
        bins: list[float],
    ):
        super().__init__()
        self._name = "ClimateModeSwitch"
        self.panel_id = "climate-mode-switch"
        self.temperature_layer_name = temperature_layer_name
        self.precipitation_layer_name = precipitation_layer_name
        self.annual_layer_name = annual_layer_name
        self.detail_layer_name = detail_layer_name
        self.start_year = START_YEAR
        self.end_year = END_YEAR
        self.rows = self._build_rows(bins)

    def _build_rows(self, bins: list[float]) -> str:
        rows = []
        labels = [f"{bins[index]:.0f}-{bins[index + 1]:.0f} mm" for index in range(len(bins) - 1)]
        for label, color in zip(labels, PRECIPITATION_PALETTE):
            rows.append(
                f"""
                <div class="precip-row">
                  <span class="precip-swatch" style="background:{color};"></span>
                  <span>{label}</span>
                </div>
                """
            )
        return "".join(rows)


def save_interactive_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    bins = build_temperature_bins(map_data)
    precipitation_bins = build_precipitation_bins(map_data)
    geojson = map_data.set_index("COD_PROVINCIA").to_json()
    style_dict = build_slider_style(map_data, bins)
    precipitation_style_dict = build_precipitation_slider_style(map_data, precipitation_bins)
    max_temp_scale = max_monthly_temperature_scale(map_data)
    max_precip_scale = max_monthly_precipitation_scale(map_data)
    chart_data = map_data.copy()
    chart_data["monthly_chart_html"] = [
        build_monthly_temperature_chart(row, bins, max_temp_scale)
        for _, row in chart_data.iterrows()
    ]
    chart_data["monthly_precipitation_chart_html"] = [
        build_monthly_precipitation_chart(row, precipitation_bins, max_precip_scale)
        for _, row in chart_data.iterrows()
    ]
    chart_html_by_code = dict(zip(chart_data["COD_PROVINCIA"], chart_data["monthly_chart_html"]))

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

    slider_layer = plugins.TimeSliderChoropleth(
        data=geojson,
        styledict=style_dict,
        date_options="MMM",
        highlight=True,
        name="Temperatura media mensual",
        overlay=True,
        control=False,
        show=True,
        init_timestamp=0,
        stroke_color="#555555",
        stroke_width=0.6,
        stroke_opacity=0.55,
    )
    slider_layer.add_to(web_map)

    precipitation_slider_layer = plugins.TimeSliderChoropleth(
        data=geojson,
        styledict=precipitation_style_dict,
        date_options="MMM",
        highlight=True,
        name="Precipitacion mensual",
        overlay=True,
        control=False,
        show=False,
        init_timestamp=0,
        stroke_color="#26506f",
        stroke_width=0.6,
        stroke_opacity=0.65,
    )
    precipitation_slider_layer.add_to(web_map)

    step = cm.StepColormap(
        PALETTE,
        index=bins,
        vmin=bins[0],
        vmax=bins[-1],
        caption="Temperatura media mensual (C), cortes naturales",
    )
    step.add_to(web_map)
    add_monthly_chart_styles(web_map)

    detail_layer = folium.GeoJson(
        chart_data,
        name="Detalle provincial",
        control=False,
        style_function=lambda _: {"fillOpacity": 0, "color": "#222222", "weight": 0.25},
        highlight_function=lambda _: {"weight": 2.0, "color": "#111111", "fillOpacity": 0.06},
    ).add_to(web_map)

    annual_layer = folium.FeatureGroup(name="Puntos dispersion mensual", show=True)
    min_std = float(map_data["monthly_std_c"].min())
    max_std = float(map_data["monthly_std_c"].max())
    for _, row in map_data.iterrows():
        radius = scaled_radius(float(row["monthly_std_c"]), min_std, max_std)
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=radius,
            color="#ffffff",
            weight=0.9,
            fill=True,
            fill_color=color_for_value(float(row["annual_mean_c"]), bins),
            fill_opacity=0.9,
            tooltip=(
                f"{row['province_name']}: dispersion mensual {row['monthly_std_c']:.1f} C; "
                f"media anual {row['annual_mean_c']:.1f} C; "
                f"precipitacion {row['precipitation_annual_mm']:.0f} mm/ano"
            ),
            popup=folium.Popup(
                chart_html_by_code[row["COD_PROVINCIA"]],
                max_width=390,
                class_name="folium-monthly-chart-popup",
            ),
        ).add_to(annual_layer)
    annual_layer.add_to(web_map)

    SeasonTemperatureLabels(map_data, slider_layer.get_name()).add_to(web_map)
    RainWeatherIcons(map_data, precipitation_slider_layer.get_name()).add_to(web_map)
    ClimateDetailContent(detail_layer.get_name()).add_to(web_map)
    ClimateModeSwitch(
        slider_layer.get_name(),
        precipitation_slider_layer.get_name(),
        annual_layer.get_name(),
        detail_layer.get_name(),
        precipitation_bins,
    ).add_to(web_map)
    add_season_panel(web_map)
    add_dispersion_legend(web_map, map_data)
    plugins.MiniMap(toggle_display=True, minimized=True).add_to(web_map)
    plugins.Fullscreen(position="topright").add_to(web_map)
    plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(web_map)
    plugins.Search(
        layer=detail_layer,
        geom_type="Polygon",
        placeholder="Buscar provincia",
        collapsed=True,
        search_label="province_name",
        position="topleft",
    ).add_to(web_map)
    folium.LayerControl(collapsed=False).add_to(web_map)

    web_map.save(OUTPUT_DIR / "mapa5_confort_climatico_estacional_interactivo.html")


def save_tables(map_data: gpd.GeoDataFrame) -> None:
    columns = [
        "COD_PROVINCIA",
        "province_name",
        *MONTHS.keys(),
        "winter_c",
        "spring_c",
        "summer_c",
        "autumn_c",
        "annual_mean_c",
        "monthly_std_c",
        "monthly_range_c",
        "precipitation_annual_mm",
        *PRECIPITATION_MONTH_COLUMNS.values(),
        "seasonal_range_c",
        "annual_anomaly_c",
        "climate_comfort_score",
        "area_km2",
        "latitude",
        "longitude",
        "start_year",
        "end_year",
    ]
    table = map_data[columns].sort_values("climate_comfort_score", ascending=False).copy()
    table.to_csv(OUTPUT_DIR / "mapa5_confort_climatico_estacional_datos.csv", index=False)


def main() -> None:
    map_data = build_dataset()
    save_static_map(map_data)
    save_interactive_map(map_data)
    save_tables(map_data)

    print(
        f"Mapa 5 generado con temperaturas mensuales, estaciones y precipitacion {START_YEAR}-{END_YEAR}."
    )
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
