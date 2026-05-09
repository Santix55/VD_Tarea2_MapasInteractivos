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

START_YEAR = 1995
END_YEAR = 2024

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

PALETTE = ["#2b83ba", "#abdda4", "#ffffbf", "#fdae61", "#d7191c"]

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
    map_data = provinces.merge(
        temperature.drop(columns=["province_name"], errors="ignore"),
        on="COD_PROVINCIA",
        how="left",
    )

    missing = map_data[map_data["annual_mean_c"].isna()]
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


def color_for_value(value: float, bins: list[float]) -> str:
    for index, upper in enumerate(bins[1:]):
        if value <= upper:
            return PALETTE[index]
    return PALETTE[-1]


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
        width: 334px;
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
        grid-template-columns: repeat(3, minmax(0, 1fr));
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


def save_interactive_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    bins = build_temperature_bins(map_data)
    geojson = map_data.set_index("COD_PROVINCIA").to_json()
    style_dict = build_slider_style(map_data, bins)
    max_temp_scale = max_monthly_temperature_scale(map_data)
    chart_data = map_data.copy()
    chart_data["monthly_chart_html"] = [
        build_monthly_temperature_chart(row, bins, max_temp_scale)
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
        show=True,
        init_timestamp=0,
        stroke_color="#555555",
        stroke_width=0.6,
        stroke_opacity=0.55,
    )
    slider_layer.add_to(web_map)

    step = cm.StepColormap(
        PALETTE,
        index=bins,
        vmin=bins[0],
        vmax=bins[-1],
        caption="Temperatura media mensual (C), cortes naturales",
    )
    step.add_to(web_map)
    add_monthly_chart_styles(web_map)

    tooltip_fields = [
        "province_name",
        *MONTHS.keys(),
        "annual_mean_c",
        "monthly_std_c",
        "monthly_range_c",
        "seasonal_range_c",
        "climate_comfort_score",
    ]
    tooltip_aliases = [
        "Provincia",
        *[month["label"] for month in MONTHS.values()],
        "Media anual",
        "Dispersion mensual",
        "Amplitud anual",
        "Amplitud estacional",
        "Indice confort",
    ]
    detail_layer = folium.GeoJson(
        chart_data,
        name="Detalle provincial",
        style_function=lambda _: {"fillOpacity": 0, "color": "#222222", "weight": 0.25},
        highlight_function=lambda _: {"weight": 2.0, "color": "#111111", "fillOpacity": 0.06},
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            labels=True,
            sticky=False,
        ),
        popup=folium.GeoJsonPopup(
            fields=["monthly_chart_html"],
            labels=False,
            localize=False,
            max_width=390,
            class_name="folium-monthly-chart-popup",
            style="margin:0;",
        ),
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
                f"media anual {row['annual_mean_c']:.1f} C"
            ),
            popup=folium.Popup(
                chart_html_by_code[row["COD_PROVINCIA"]],
                max_width=390,
                class_name="folium-monthly-chart-popup",
            ),
        ).add_to(annual_layer)
    annual_layer.add_to(web_map)

    SeasonTemperatureLabels(map_data, slider_layer.get_name()).add_to(web_map)
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

    print(f"Mapa 5 generado con temperaturas mensuales y estacionales {START_YEAR}-{END_YEAR}.")
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
