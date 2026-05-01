from __future__ import annotations

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
from branca.element import MacroElement, Template
import geopandas as gpd
import mapclassify
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd
import requests


DATA_DIR = BASE_DIR / "datos"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"

BROADBAND_URL = (
    "https://digital.gob.es/content/dam/portal-mtdfp/avance-digital/"
    "telecomunicacion-e-infraestructuras-digitales/areas_interes/banda-ancha/"
    "cobertura/documents/cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx"
)
NUTS_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson"

BROADBAND_FILE = DATA_DIR / "cobertura_ba_espana_2021_2024.xlsx"
NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"

SHEET_NAME = "Provincia_%hogar"
COVERAGE_COLUMN_2023 = "Cob. 1Gbps descarga condiciones maxima demanda\n(junio 2023)"
COVERAGE_COLUMN_2024 = "Cob. 1Gbps descarga condiciones maxima demanda\n(junio 2024)"

READINESS_BINS = [0, 80, 85, 90, 95, 100]
READINESS_LABELS = [
    "Nivel 1 - Riesgo alto (<80%)",
    "Nivel 2 - Riesgo medio (80-85%)",
    "Nivel 3 - Revisar (85-90%)",
    "Nivel 4 - Apto (90-95%)",
    "Nivel 5 - Muy apto (>=95%)",
]
READINESS_RECOMMENDATIONS = [
    "No usar como destino tech sin revisar zona concreta.",
    "Valido solo con comprobacion previa de direccion.",
    "Aceptable, pero conviene revisar municipios concretos.",
    "Apto para teletrabajo en la mayor parte de hogares.",
    "Muy apto para teletrabajo e IA.",
]
READINESS_COLORS = ["#8c1d40", "#d95f02", "#f6c85f", "#4eb3d3", "#2ca25f"]
CHANGE_BINS = [-10, 0, 2.5, 5, 10, 45]
CHANGE_COLORS = ["#6b6b6b", "#d0e1f2", "#73bfe2", "#2b8cbe", "#f28e2b"]
GAP_PALETTE = ["#fff7ec", "#fee8c8", "#fdbb84", "#e34a33", "#7f0000"]
ALERT_THRESHOLD = 85.0

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


def format_axis_int(value: float, _: int) -> str:
    return format_int(value)


def coverage_class_index(value: float) -> int:
    value = float(value)
    for index, upper in enumerate(READINESS_BINS[1:]):
        is_last = index == len(READINESS_COLORS) - 1
        if value < upper or (is_last and value <= upper):
            return index
    return len(READINESS_COLORS) - 1


def readiness_label(value: float) -> str:
    return READINESS_LABELS[coverage_class_index(value)]


def readiness_recommendation(value: float) -> str:
    return READINESS_RECOMMENDATIONS[coverage_class_index(value)]


def readiness_color(value: float) -> str:
    return READINESS_COLORS[coverage_class_index(value)]


def color_for_bins(value: float, bins: list[float], colors: list[str]) -> str:
    for index, upper in enumerate(bins[1:]):
        is_last = index == len(colors) - 1
        if value < upper or (is_last and value <= upper):
            return colors[index]
    return colors[-1]


def weighted_coverage(map_data: pd.DataFrame) -> float:
    return (
        map_data["coverage_1gbps_2024_pct"].mul(map_data["households"]).sum()
        / map_data["households"].sum()
    )


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
            COVERAGE_COLUMN_2023,
            COVERAGE_COLUMN_2024,
        ]
    ].rename(
        columns={
            "Comunidad Autonoma": "ccaa",
            "Provincia": "province_name",
            "Habitantes": "population",
            "Hogares": "households",
            COVERAGE_COLUMN_2023: "coverage_1gbps_2023_pct",
            COVERAGE_COLUMN_2024: "coverage_1gbps_2024_pct",
        }
    )
    summary["population"] = pd.to_numeric(summary["population"], errors="coerce")
    summary["households"] = pd.to_numeric(summary["households"], errors="coerce")
    summary["coverage_1gbps_2023_pct"] = to_percent(summary["coverage_1gbps_2023_pct"])
    summary["coverage_1gbps_2024_pct"] = to_percent(summary["coverage_1gbps_2024_pct"])
    summary["coverage_change_pp"] = (
        summary["coverage_1gbps_2024_pct"] - summary["coverage_1gbps_2023_pct"]
    )
    summary["connected_households_2024"] = (
        summary["households"] * summary["coverage_1gbps_2024_pct"] / 100
    )
    summary["uncovered_households_2024"] = (
        summary["households"] - summary["connected_households_2024"]
    )

    numeric_columns = [
        "coverage_1gbps_2023_pct",
        "coverage_1gbps_2024_pct",
        "coverage_change_pp",
        "connected_households_2024",
        "uncovered_households_2024",
    ]
    summary[numeric_columns] = summary[numeric_columns].round(2)
    return summary


def load_province_geometries() -> gpd.GeoDataFrame:
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])

    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    provinces = provinces[["COD_PROVINCIA", "geometry"]].copy()
    return provinces.to_crs("EPSG:4326")


def add_geographic_metrics(map_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    data = map_data.copy()
    projected = data.to_crs("EPSG:3035")
    data["area_km2"] = (projected.area / 1_000_000).round(1)

    points = gpd.GeoSeries(projected.geometry.representative_point(), crs=projected.crs)
    points_wgs84 = points.to_crs("EPSG:4326")
    data["label_lon"] = points_wgs84.x
    data["label_lat"] = points_wgs84.y
    data["readiness_class"] = data["coverage_1gbps_2024_pct"].map(readiness_label)
    data["readiness_recommendation"] = data["coverage_1gbps_2024_pct"].map(
        readiness_recommendation
    )
    data["readiness_color"] = data["coverage_1gbps_2024_pct"].map(readiness_color)
    data["alert_tech_gap"] = data["coverage_1gbps_2024_pct"].lt(ALERT_THRESHOLD)
    data["coverage_gap_pct"] = (100 - data["coverage_1gbps_2024_pct"]).round(2)
    return data


def build_dataset() -> gpd.GeoDataFrame:
    download_file(BROADBAND_URL, BROADBAND_FILE)
    download_file(NUTS_URL, NUTS_FILE)

    coverage = load_broadband_by_province()
    provinces = load_province_geometries()
    map_data = provinces.merge(coverage, on="COD_PROVINCIA", how="left")

    missing = map_data[map_data["coverage_1gbps_2024_pct"].isna()]
    if not missing.empty:
        missing_codes = ", ".join(missing["COD_PROVINCIA"].tolist())
        raise ValueError(f"Faltan datos de cobertura para estas provincias: {missing_codes}")

    return add_geographic_metrics(map_data)


def build_quantile_bins(values: pd.Series, k: int = 5) -> list[float]:
    clean = values.dropna().astype(float)
    classifier = mapclassify.Quantiles(clean, k=k)
    bins = [float(clean.min())] + [float(value) for value in classifier.bins]
    bins[0] = max(0.0, bins[0] - 0.1)

    for index in range(1, len(bins)):
        if bins[index] <= bins[index - 1]:
            bins[index] = bins[index - 1] + 0.01
    return bins


def plot_canary_inset(map_ax: plt.Axes, map_data: gpd.GeoDataFrame) -> None:
    canary_codes = ["35", "38"]
    canary_map = map_data[map_data["COD_PROVINCIA"].isin(canary_codes)]
    if canary_map.empty:
        return

    canary_ax = map_ax.inset_axes([0.035, 0.055, 0.22, 0.19])
    canary_map.plot(
        ax=canary_ax,
        color=canary_map["readiness_color"],
        linewidth=0.45,
        edgecolor="#ffffff",
    )
    canary_map.boundary.plot(ax=canary_ax, color="#4f4f4f", linewidth=0.18, alpha=0.6)

    alert = canary_map[canary_map["alert_tech_gap"]].copy()
    if not alert.empty:
        alert.plot(
            ax=canary_ax,
            facecolor="none",
            edgecolor="#222222",
            linewidth=0.0,
            hatch="////",
            zorder=3,
        )

    canary_ax.set_xlim(-18.4, -13.1)
    canary_ax.set_ylim(27.55, 29.65)
    canary_ax.set_title("Canarias", fontsize=8.2, pad=2)
    canary_ax.set_xticks([])
    canary_ax.set_yticks([])
    for spine in canary_ax.spines.values():
        spine.set_edgecolor("#8c8c8c")
        spine.set_linewidth(0.8)


def save_static_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(16, 9.8), dpi=180)
    grid = fig.add_gridspec(
        3,
        3,
        width_ratios=[1.25, 1.25, 0.95],
        height_ratios=[0.52, 1, 1],
        wspace=0.18,
        hspace=0.36,
    )
    map_ax = fig.add_subplot(grid[:, :2])
    summary_ax = fig.add_subplot(grid[0, 2])
    gap_ax = fig.add_subplot(grid[1, 2])
    slope_ax = fig.add_subplot(grid[2, 2])

    map_data.plot(
        ax=map_ax,
        color=map_data["readiness_color"],
        linewidth=0.42,
        edgecolor="#ffffff",
    )
    map_data.boundary.plot(ax=map_ax, color="#4f4f4f", linewidth=0.15, alpha=0.55)

    alert = map_data[map_data["alert_tech_gap"]].copy()
    if not alert.empty:
        alert.plot(
            ax=map_ax,
            facecolor="none",
            edgecolor="#222222",
            linewidth=0.0,
            hatch="////",
            zorder=3,
        )

    weakest = map_data.nsmallest(7, "coverage_1gbps_2024_pct")
    for _, row in weakest.iterrows():
        text = map_ax.annotate(
            f"{row['province_name']}\n{row['coverage_1gbps_2024_pct']:.1f}%",
            xy=(row["label_lon"], row["label_lat"]),
            ha="center",
            va="center",
            fontsize=7,
            color="#111111",
            zorder=5,
        )
        text.set_path_effects(
            [path_effects.withStroke(linewidth=2.5, foreground="white", alpha=0.96)]
        )

    map_ax.set_xlim(-10.2, 5.0)
    map_ax.set_ylim(35.0, 44.5)
    map_ax.set_title(
        "Semaforo provincial de aptitud para teletrabajo",
        fontsize=16.2,
        fontweight="bold",
        pad=12,
    )
    map_ax.set_axis_off()
    plot_canary_inset(map_ax, map_data)

    legend_handles = [
        mpatches.Patch(facecolor=color, edgecolor="#666666", label=label)
        for color, label in zip(READINESS_COLORS, READINESS_LABELS)
    ]
    legend_handles.append(
        mpatches.Patch(
            facecolor="white",
            edgecolor="#222222",
            hatch="////",
            label="Alerta: <85%",
        )
    )
    map_ax.legend(
        handles=legend_handles,
        title="Cobertura 1 Gbps",
        loc="lower right",
        fontsize=7.6,
        title_fontsize=8.7,
        frameon=True,
        framealpha=0.96,
    )

    summary_ax.set_axis_off()
    avg_coverage = weighted_coverage(map_data)
    alert_count = int(map_data["alert_tech_gap"].sum())
    uncovered_total = float(map_data["uncovered_households_2024"].sum())
    summary_ax.text(0.0, 0.96, "Filtro tecnologico", fontsize=11, fontweight="bold", va="top")
    summary_ax.text(0.0, 0.62, f"{avg_coverage:.1f}%", fontsize=24, fontweight="bold")
    summary_ax.text(0.0, 0.44, "cobertura ponderada por hogares", fontsize=8.5, color="#444444")
    summary_ax.text(
        0.0,
        0.18,
        f"{alert_count} provincias en riesgo  |  {format_int(uncovered_total)} hogares sin 1 Gbps",
        fontsize=8.4,
        color="#222222",
    )

    gap = map_data.nlargest(10, "uncovered_households_2024").sort_values(
        "uncovered_households_2024"
    )
    gap_ax.barh(
        gap["province_name"],
        gap["uncovered_households_2024"],
        color="#8c1d40",
    )
    gap_ax.set_title("Donde quedan mas hogares sin 1 Gbps", fontsize=11, fontweight="bold")
    gap_ax.set_xlabel("Hogares estimados sin 1 Gbps", fontsize=8.5)
    gap_ax.xaxis.set_major_formatter(FuncFormatter(format_axis_int))
    gap_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    gap_ax.tick_params(axis="both", labelsize=8)

    movers = (
        map_data.assign(abs_change=map_data["coverage_change_pp"].abs())
        .nlargest(10, "abs_change")
        .sort_values("coverage_change_pp")
    )
    for y_pos, (_, row) in enumerate(movers.iterrows()):
        color = "#2b8cbe" if row["coverage_change_pp"] >= 0 else "#6b6b6b"
        slope_ax.plot(
            [row["coverage_1gbps_2023_pct"], row["coverage_1gbps_2024_pct"]],
            [y_pos, y_pos],
            color=color,
            linewidth=1.8,
            alpha=0.85,
        )
        slope_ax.scatter(
            [row["coverage_1gbps_2023_pct"]],
            [y_pos],
            s=18,
            color="#ffffff",
            edgecolor=color,
            linewidth=1.1,
            zorder=3,
        )
        slope_ax.scatter(
            [row["coverage_1gbps_2024_pct"]],
            [y_pos],
            s=22,
            color=color,
            edgecolor="#ffffff",
            linewidth=0.7,
            zorder=4,
        )
        slope_ax.text(
            100.7,
            y_pos,
            f"{row['coverage_change_pp']:+.1f} pp",
            va="center",
            fontsize=7.3,
            color="#333333",
        )
    slope_ax.set_yticks(range(len(movers)))
    slope_ax.set_yticklabels(movers["province_name"], fontsize=8)
    slope_ax.set_xlim(55, 105)
    slope_ax.set_xlabel("% hogares con 1 Gbps", fontsize=8.5)
    slope_ax.set_title("Cambio 2023 -> 2024", fontsize=11, fontweight="bold")
    slope_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    slope_ax.tick_params(axis="x", labelsize=8)

    for side_ax in [gap_ax, slope_ax]:
        for spine in ["top", "right", "left"]:
            side_ax.spines[spine].set_visible(False)

    fig.suptitle(
        "Mapa 4. Conectividad para teletrabajo e IA",
        fontsize=20,
        fontweight="bold",
        x=0.44,
        y=0.985,
    )
    fig.text(
        0.02,
        0.02,
        "Fuente: SETELECO/Ministerio para la Transformacion Digital y Eurostat/GISCO NUTS3. "
        "Coropleta provincial con 5 umbrales operativos; cobertura sobre hogares en junio de 2024.",
        fontsize=8,
        color="#555555",
    )

    fig.savefig(OUTPUT_DIR / "mapa4_conectividad_teletrabajo.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa4_conectividad_teletrabajo.pdf", bbox_inches="tight")
    plt.close(fig)


class DetailExplanationControl(MacroElement):
    _template = Template(
        """
        {% macro header(this, kwargs) %}
        <style>
          #{{ this._parent.get_name() }} .tech-detail-explanation {
            width: 270px;
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

          #{{ this._parent.get_name() }} .tech-detail-title {
            margin-bottom: 5px;
            font-size: 12.5px;
            font-weight: 700;
          }

          #{{ this._parent.get_name() }} .tech-detail-body {
            margin: 0;
          }
        </style>
        {% endmacro %}

        {% macro script(this, kwargs) %}
        (function () {
          const map = {{ this._parent.get_name() }};
          const explanations = {{ this.explanations|tojson }};
          const defaultLayer = {{ this.default_layer|tojson }};
          const control = L.control({ position: "bottomright" });

          function escapeHtml(value) {
            return String(value)
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
          }

          control.onAdd = function () {
            this._container = L.DomUtil.create("div", "tech-detail-explanation leaflet-control");
            L.DomEvent.disableClickPropagation(this._container);
            L.DomEvent.disableScrollPropagation(this._container);
            this.update(defaultLayer);
            return this._container;
          };

          control.update = function (layerName) {
            const item = explanations[layerName] || explanations[defaultLayer];
            this._container.innerHTML =
              '<div class="tech-detail-title">' + escapeHtml(item.title) + '</div>' +
              '<p class="tech-detail-body">' + escapeHtml(item.body) + '</p>';
          };

          control.addTo(map);
          map.on("baselayerchange", function (event) {
            control.update(event.name);
          });
        })();
        {% endmacro %}
        """
    )

    def __init__(self) -> None:
        super().__init__()
        self._name = "DetailExplanationControl"
        self.default_layer = "1. Aptitud actual para teletrabajo"
        self.explanations = {
            "1. Aptitud actual para teletrabajo": {
                "title": "Vista 1: aptitud actual",
                "body": (
                    "Clasifica cada provincia por el porcentaje de hogares con 1 Gbps en 2024. "
                    "Verde y azul indican destinos aptos; amarillo pide revisar municipio; "
                    "naranja y granate senalan riesgo tecnologico."
                ),
            },
            "2. Evolucion 2023-2024": {
                "title": "Vista 2: evolucion reciente",
                "body": (
                    "Muestra cuantos puntos porcentuales cambio la cobertura 1 Gbps desde 2023. "
                    "Sirve para detectar provincias que mejoran rapido o retroceden respecto al ano anterior."
                ),
            },
            "3. Hogares sin 1 Gbps": {
                "title": "Vista 3: brecha pendiente",
                "body": (
                    "Colorea por numero estimado de hogares que todavia no tienen 1 Gbps. "
                    "Una provincia poblada puede salir oscura aunque su porcentaje de cobertura sea alto."
                ),
            },
        }


class DynamicLegendControl(MacroElement):
    _template = Template(
        """
        {% macro header(this, kwargs) %}
        <style>
          #{{ this._parent.get_name() }} .tech-dynamic-legend {
            width: 238px;
            max-width: calc(100vw - 34px);
            padding: 9px 10px;
            border: 1px solid rgba(60, 60, 60, 0.55);
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.22);
            color: #1f1f1f;
            font-family: Arial, sans-serif;
            font-size: 11.5px;
            line-height: 1.25;
          }

          #{{ this._parent.get_name() }} .tech-legend-title {
            margin-bottom: 6px;
            font-size: 12.5px;
            font-weight: 700;
          }

          #{{ this._parent.get_name() }} .tech-legend-row {
            display: flex;
            align-items: center;
            gap: 6px;
            margin: 3px 0;
          }

          #{{ this._parent.get_name() }} .tech-legend-swatch {
            width: 18px;
            height: 12px;
            flex: 0 0 18px;
            border: 1px solid rgba(0, 0, 0, 0.35);
          }
        </style>
        {% endmacro %}

        {% macro script(this, kwargs) %}
        (function () {
          const map = {{ this._parent.get_name() }};
          const legends = {{ this.legends|tojson }};
          const defaultLayer = {{ this.default_layer|tojson }};
          const control = L.control({ position: "topright" });

          function escapeHtml(value) {
            return String(value)
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
          }

          function renderLegend(item) {
            const rows = item.items.map(function (entry) {
              return '<div class="tech-legend-row">' +
                '<span class="tech-legend-swatch" style="background:' + escapeHtml(entry.color) + '"></span>' +
                '<span>' + escapeHtml(entry.label) + '</span>' +
              '</div>';
            }).join("");

            return '<div class="tech-legend-title">' + escapeHtml(item.title) + '</div>' + rows;
          }

          control.onAdd = function () {
            this._container = L.DomUtil.create("div", "tech-dynamic-legend leaflet-control");
            L.DomEvent.disableClickPropagation(this._container);
            L.DomEvent.disableScrollPropagation(this._container);
            this.update(defaultLayer);
            return this._container;
          };

          control.update = function (layerName) {
            this._container.innerHTML = renderLegend(legends[layerName] || legends[defaultLayer]);
          };

          control.addTo(map);
          map.on("baselayerchange", function (event) {
            control.update(event.name);
          });
        })();
        {% endmacro %}
        """
    )

    def __init__(self, gap_bins: list[float]) -> None:
        super().__init__()
        self._name = "DynamicLegendControl"
        self.default_layer = "1. Aptitud actual para teletrabajo"
        self.legends = {
            "1. Aptitud actual para teletrabajo": {
                "title": "Cobertura 1 Gbps",
                "items": [
                    {"color": color, "label": label}
                    for color, label in zip(READINESS_COLORS, READINESS_LABELS)
                ],
            },
            "2. Evolucion 2023-2024": {
                "title": "Cambio 2023-2024",
                "items": [
                    {"color": CHANGE_COLORS[0], "label": "Retroceso (<0 pp)"},
                    {"color": CHANGE_COLORS[1], "label": "0 a 2,5 pp"},
                    {"color": CHANGE_COLORS[2], "label": "2,5 a 5 pp"},
                    {"color": CHANGE_COLORS[3], "label": "5 a 10 pp"},
                    {"color": CHANGE_COLORS[4], "label": "10 pp o mas"},
                ],
            },
            "3. Hogares sin 1 Gbps": {
                "title": "Hogares sin 1 Gbps",
                "items": [
                    {
                        "color": color,
                        "label": f"{format_int(gap_bins[index])} a {format_int(gap_bins[index + 1])}",
                    }
                    for index, color in enumerate(GAP_PALETTE)
                ],
            },
        }


def save_interactive_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    gap_bins = build_quantile_bins(map_data["uncovered_households_2024"], k=5)

    web_map = folium.Map(
        location=[40.1, -3.7],
        zoom_start=6,
        tiles=None,
        control_scale=True,
        max_bounds=True,
    )
    web_map.fit_bounds([[27.3, -18.8], [43.9, 4.7]])

    tooltip_fields = [
        "province_name",
        "ccaa",
        "readiness_class",
        "readiness_recommendation",
        "coverage_1gbps_2024_pct",
        "coverage_gap_pct",
        "coverage_change_pp",
        "uncovered_households_2024",
        "households",
        "population",
    ]
    tooltip_aliases = [
        "Provincia",
        "CCAA",
        "Lectura rapida",
        "Recomendacion",
        "Cobertura 2024",
        "Hogares sin cobertura (%)",
        "Mejora 2023-2024 (pp)",
        "Hogares sin 1 Gbps",
        "Hogares",
        "Habitantes",
    ]

    coverage_group = folium.FeatureGroup(
        name="1. Aptitud actual para teletrabajo",
        overlay=False,
        control=True,
        show=True,
    )
    folium.TileLayer("CartoDB positron", control=False).add_to(coverage_group)
    coverage_layer = folium.GeoJson(
        map_data,
        name="Aptitud actual",
        show=True,
        style_function=lambda feature: {
            "fillColor": feature["properties"]["readiness_color"],
            "color": "#222222" if feature["properties"]["alert_tech_gap"] else "#555555",
            "weight": 1.25 if feature["properties"]["alert_tech_gap"] else 0.45,
            "fillOpacity": 0.84,
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
            fields=[
                "province_name",
                "coverage_1gbps_2023_pct",
                "coverage_1gbps_2024_pct",
                "readiness_class",
                "readiness_recommendation",
                "coverage_change_pp",
                "connected_households_2024",
                "uncovered_households_2024",
            ],
            aliases=[
                "Provincia",
                "Cobertura 2023 (%)",
                "Cobertura 2024 (%)",
                "Lectura rapida",
                "Recomendacion",
                "Mejora (pp)",
                "Hogares cubiertos 2024",
                "Hogares no cubiertos 2024",
            ],
            localize=True,
            labels=True,
            max_width=360,
        ),
    ).add_to(coverage_group)
    coverage_group.add_to(web_map)

    evolution_group = folium.FeatureGroup(
        name="2. Evolucion 2023-2024",
        overlay=False,
        control=True,
        show=False,
    )
    folium.TileLayer("CartoDB positron", control=False).add_to(evolution_group)
    folium.GeoJson(
        map_data,
        name="Evolucion",
        show=True,
        style_function=lambda feature: {
            "fillColor": color_for_bins(
                float(feature["properties"]["coverage_change_pp"]),
                CHANGE_BINS,
                CHANGE_COLORS,
            ),
            "color": "#444444",
            "weight": 0.5,
            "fillOpacity": 0.82,
        },
        highlight_function=lambda _: {"weight": 2.0, "color": "#111111", "fillOpacity": 0.9},
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            labels=True,
            sticky=False,
        ),
        popup=folium.GeoJsonPopup(
            fields=[
                "province_name",
                "coverage_1gbps_2023_pct",
                "coverage_1gbps_2024_pct",
                "coverage_change_pp",
            ],
            aliases=[
                "Provincia",
                "Cobertura 2023 (%)",
                "Cobertura 2024 (%)",
                "Mejora (pp)",
            ],
            localize=True,
            labels=True,
            max_width=320,
        ),
    ).add_to(evolution_group)
    evolution_group.add_to(web_map)

    gap_group = folium.FeatureGroup(
        name="3. Hogares sin 1 Gbps",
        overlay=False,
        control=True,
        show=False,
    )
    folium.TileLayer("CartoDB positron", control=False).add_to(gap_group)
    folium.GeoJson(
        map_data,
        name="Hogares sin 1 Gbps",
        show=True,
        style_function=lambda feature: {
            "fillColor": color_for_bins(
                float(feature["properties"]["uncovered_households_2024"]),
                gap_bins,
                GAP_PALETTE,
            ),
            "color": "#444444",
            "weight": 0.5,
            "fillOpacity": 0.82,
        },
        highlight_function=lambda _: {"weight": 2.0, "color": "#111111", "fillOpacity": 0.9},
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            labels=True,
            sticky=False,
        ),
        popup=folium.GeoJsonPopup(
            fields=[
                "province_name",
                "uncovered_households_2024",
                "connected_households_2024",
                "households",
                "coverage_1gbps_2024_pct",
            ],
            aliases=[
                "Provincia",
                "Hogares sin 1 Gbps",
                "Hogares cubiertos",
                "Hogares totales",
                "Cobertura 2024 (%)",
            ],
            localize=True,
            labels=True,
            max_width=320,
        ),
    ).add_to(gap_group)
    gap_group.add_to(web_map)

    review_markers = plugins.MarkerCluster(
        name="Marcadores: provincias a revisar (<90%)",
        show=True,
    )
    for _, row in map_data[map_data["coverage_1gbps_2024_pct"].lt(90)].iterrows():
        marker_color = "red" if row["coverage_1gbps_2024_pct"] < 85 else "orange"
        popup = (
            f"<b>{row['province_name']}</b><br>"
            f"{row['readiness_class']}<br>"
            f"{row['readiness_recommendation']}<br>"
            f"Cobertura 2024: {row['coverage_1gbps_2024_pct']:.1f}%<br>"
            f"Hogares sin 1 Gbps: {format_int(row['uncovered_households_2024'])}"
        )
        folium.Marker(
            location=[row["label_lat"], row["label_lon"]],
            tooltip=f"{row['province_name']}: {row['readiness_class']}",
            popup=folium.Popup(popup, max_width=300),
            icon=folium.Icon(color=marker_color, icon="info-sign"),
        ).add_to(review_markers)
    review_markers.add_to(web_map)

    risk_label_layer = folium.FeatureGroup(name="Etiquetas: riesgo alto/medio (<85%)", show=False)
    for _, row in map_data[map_data["alert_tech_gap"]].iterrows():
        label_html = f"""
        <div style="
          min-width: 92px; padding: 2px 5px;
          background: rgba(255, 255, 255, 0.90);
          border: 1px solid #444; border-radius: 3px;
          color: #111; font-family: Arial, sans-serif;
          font-size: 10px; font-weight: 700; line-height: 1.15;
          text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.25);">
          {row['province_name']}<br>{row['coverage_1gbps_2024_pct']:.1f}%
        </div>
        """
        folium.Marker(
            location=[row["label_lat"], row["label_lon"]],
            icon=folium.DivIcon(
                html=label_html,
                icon_size=(96, 30),
                icon_anchor=(48, 15),
            ),
            tooltip=f"{row['province_name']}: {row['readiness_recommendation']}",
        ).add_to(risk_label_layer)
    risk_label_layer.add_to(web_map)

    DynamicLegendControl(gap_bins).add_to(web_map)
    DetailExplanationControl().add_to(web_map)
    plugins.MousePosition(
        position="bottomleft",
        separator=", ",
        prefix="Coordenadas",
        num_digits=4,
    ).add_to(web_map)
    plugins.Search(
        layer=coverage_layer,
        geom_type="Polygon",
        placeholder="Buscar provincia",
        collapsed=True,
        search_label="province_name",
        position="topleft",
    ).add_to(web_map)
    folium.LayerControl(collapsed=False).add_to(web_map)

    web_map.save(OUTPUT_DIR / "mapa4_conectividad_teletrabajo_interactivo.html")


def save_tables(map_data: gpd.GeoDataFrame) -> None:
    columns = [
        "COD_PROVINCIA",
        "province_name",
        "ccaa",
        "population",
        "households",
        "coverage_1gbps_2023_pct",
        "coverage_1gbps_2024_pct",
        "coverage_change_pp",
        "coverage_gap_pct",
        "readiness_class",
        "readiness_recommendation",
        "alert_tech_gap",
        "connected_households_2024",
        "uncovered_households_2024",
        "area_km2",
        "label_lat",
        "label_lon",
    ]
    table = map_data[columns].sort_values("coverage_1gbps_2024_pct", ascending=False).copy()
    table["year"] = 2024
    table.to_csv(OUTPUT_DIR / "mapa4_conectividad_teletrabajo_datos.csv", index=False)


def main() -> None:
    map_data = build_dataset()
    save_static_map(map_data)
    save_interactive_map(map_data)
    save_tables(map_data)

    print("Mapa 4 generado con cobertura 1 Gbps en hogares, junio de 2024.")
    print("Variable secundaria: mejora de cobertura 2023-2024.")
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
