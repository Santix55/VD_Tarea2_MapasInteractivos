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
import matplotlib.patches as mpatches
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
LAU_URL = "https://gisco-services.ec.europa.eu/distribution/v2/lau/geojson/LAU_RG_01M_2024_4326.geojson"

BROADBAND_FILE = DATA_DIR / "cobertura_ba_espana_2021_2024.xlsx"
LAU_FILE = DATA_DIR / "lau_2024_01m.geojson"

MUNICIPAL_SHEET = "Municipio_%hogar"
DEFAULT_TECH_KEY = "fixed_100"
DEFAULT_THRESHOLD = 90
HTML_SIMPLIFY_TOLERANCE_M = 1800
STATIC_TECH_KEY = "fixed_100"
STATIC_THRESHOLD = 90

TECH_DEFINITIONS = [
    {
        "key": "fixed_30",
        "label": "Fijo >=30 Mbps",
        "short": "30 Mbps",
        "column_2023": "Cob. 30Mbps condiciones maxima demanda\n(junio 2023) ",
        "column_2024": "Cob. 30Mbps condiciones maxima demanda\n(junio 2024) ",
        "kind": "fijo",
    },
    {
        "key": "fixed_100",
        "label": "Fijo >=100 Mbps",
        "short": "100 Mbps",
        "column_2023": "Cob. 100Mbps condiciones maxima demanda\n(junio 2023)",
        "column_2024": "Cob. 100Mbps condiciones maxima demanda\n(junio 2024)",
        "kind": "fijo",
    },
    {
        "key": "fixed_1gbps",
        "label": "Fijo >=1 Gbps",
        "short": "1 Gbps",
        "column_2023": "Cob. 1Gbps descarga condiciones maxima demanda\n(junio 2023)",
        "column_2024": "Cob. 1Gbps descarga condiciones maxima demanda\n(junio 2024)",
        "kind": "fijo",
    },
    {
        "key": "mobile_4g",
        "label": "Movil 4G",
        "short": "4G",
        "column_2023": "4G\n(junio 2023)",
        "column_2024": "4G\n(junio 2024)",
        "kind": "movil",
    },
    {
        "key": "mobile_5g",
        "label": "Movil 5G",
        "short": "5G",
        "column_2023": "5G\n(junio 2023)",
        "column_2024": "5G\n(junio 2024)",
        "kind": "movil",
    },
    {
        "key": "mobile_5g_35",
        "label": "Movil 5G banda 3,5 GHz",
        "short": "5G 3,5 GHz",
        "column_2023": "5G-Banda 3,5GHz\n(junio 2023)",
        "column_2024": "5G-Banda 3,5GHz\n(junio 2024)",
        "kind": "movil",
    },
]

PASS_COLORS = ["#f6c85f", "#99d8c9", "#2ca25f"]
FAIL_COLORS = ["#fee8c8", "#fdae6b", "#e6550d", "#8c1d40"]
SATELLITE_BANDS = [
    [[34.8, -10.8], [35.9, -11.3], [44.8, 4.6], [43.7, 5.1]],
    [[36.8, -10.9], [37.9, -11.4], [46.2, 3.8], [45.1, 4.3]],
    [[27.1, -18.7], [27.8, -19.1], [30.1, -13.2], [29.4, -12.8]],
    [[34.9, -7.6], [35.5, -8.0], [37.0, -1.8], [36.4, -1.5]],
]


def download_file(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    target.write_bytes(response.content)


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
    return f"{int(round(float(value))):,}".replace(",", ".")


def format_axis_int(value: float, _: int) -> str:
    return format_int(value)


def tech_by_key(key: str) -> dict[str, str]:
    return next(tech for tech in TECH_DEFINITIONS if tech["key"] == key)


def load_municipal_broadband() -> pd.DataFrame:
    broadband = pd.read_excel(BROADBAND_FILE, sheet_name=MUNICIPAL_SHEET)
    broadband = broadband.rename(columns=normalize_columns(broadband.columns))

    required_columns = [
        "Comunidad Autonoma",
        "Provincia",
        "CMUN",
        "Municipio",
        "Habitantes",
        "Hogares",
    ]
    for tech in TECH_DEFINITIONS:
        required_columns.extend([tech["column_2023"], tech["column_2024"]])

    missing = [column for column in required_columns if column not in broadband.columns]
    if missing:
        raise ValueError(f"Faltan columnas municipales de cobertura: {missing}")

    data = broadband[required_columns].rename(
        columns={
            "Comunidad Autonoma": "ccaa",
            "Provincia": "province_name",
            "CMUN": "CMUN",
            "Municipio": "municipality_name",
            "Habitantes": "population",
            "Hogares": "households",
        }
    )
    data["CMUN"] = pd.to_numeric(data["CMUN"], errors="coerce").astype("Int64").astype(str)
    data["CMUN"] = data["CMUN"].str.zfill(5)
    data["COD_PROVINCIA"] = data["CMUN"].str[:2]
    data["population"] = pd.to_numeric(data["population"], errors="coerce").fillna(0)
    data["households"] = pd.to_numeric(data["households"], errors="coerce").fillna(0)

    for tech in TECH_DEFINITIONS:
        data[f"{tech['key']}_2023_pct"] = to_percent(data[tech["column_2023"]])
        data[f"{tech['key']}_2024_pct"] = to_percent(data[tech["column_2024"]])
        data[f"{tech['key']}_change_pp"] = (
            data[f"{tech['key']}_2024_pct"] - data[f"{tech['key']}_2023_pct"]
        )
        data[f"{tech['key']}_uncovered_households_2024"] = (
            data["households"] * (100 - data[f"{tech['key']}_2024_pct"]) / 100
        )

    output_columns = [
        "CMUN",
        "COD_PROVINCIA",
        "municipality_name",
        "province_name",
        "ccaa",
        "population",
        "households",
    ]
    for tech in TECH_DEFINITIONS:
        output_columns.extend(
            [
                f"{tech['key']}_2023_pct",
                f"{tech['key']}_2024_pct",
                f"{tech['key']}_change_pp",
                f"{tech['key']}_uncovered_households_2024",
            ]
        )

    numeric_columns = [column for column in output_columns if column not in {"CMUN", "COD_PROVINCIA", "municipality_name", "province_name", "ccaa"}]
    data[numeric_columns] = data[numeric_columns].round(2)
    return data[output_columns]


def load_municipal_geometries() -> gpd.GeoDataFrame:
    lau = gpd.read_file(LAU_FILE, where="CNTR_CODE = 'ES'")
    lau["CMUN"] = lau["GISCO_ID"].str.replace("ES_", "", regex=False)
    return lau[["CMUN", "geometry"]].to_crs("EPSG:4326")


def add_geographic_metrics(map_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    data = map_data.copy()
    projected = data.to_crs("EPSG:3035")
    data["area_km2"] = (projected.area / 1_000_000).round(2)

    points = gpd.GeoSeries(projected.geometry.representative_point(), crs=projected.crs)
    points_wgs84 = points.to_crs("EPSG:4326")
    data["label_lon"] = points_wgs84.x
    data["label_lat"] = points_wgs84.y

    default_column = f"{DEFAULT_TECH_KEY}_2024_pct"
    data["default_gap_pct"] = (100 - data[default_column]).round(2)
    data["default_uncovered_households_2024"] = (
        data["households"] * data["default_gap_pct"] / 100
    ).round(2)
    data["default_status"] = data[default_column].ge(DEFAULT_THRESHOLD).map(
        {True: "Cumple umbral inicial", False: "Necesita revisar/respaldo"}
    )
    return data


def simplify_for_html(map_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    data = map_data.copy()
    simplified = (
        data.to_crs("EPSG:3035")
        .geometry.simplify(HTML_SIMPLIFY_TOLERANCE_M, preserve_topology=True)
        .to_crs("EPSG:4326")
    )
    data["geometry"] = simplified
    return data


def build_dataset() -> tuple[gpd.GeoDataFrame, dict[str, int]]:
    download_file(BROADBAND_URL, BROADBAND_FILE)
    download_file(LAU_URL, LAU_FILE)

    coverage = load_municipal_broadband()
    municipalities = load_municipal_geometries()
    map_data = municipalities.merge(coverage, on="CMUN", how="left")

    stats = {
        "municipal_geometries": int(len(municipalities)),
        "municipal_rows": int(len(coverage)),
        "matched_municipalities": int(map_data["municipality_name"].notna().sum()),
        "geometries_without_data": int(map_data["municipality_name"].isna().sum()),
        "data_without_geometry": int(coverage[~coverage["CMUN"].isin(municipalities["CMUN"])].shape[0]),
    }

    map_data = map_data.dropna(subset=["municipality_name"]).copy()
    return add_geographic_metrics(map_data), stats


def weighted_coverage(map_data: pd.DataFrame, tech_key: str) -> float:
    coverage_column = f"{tech_key}_2024_pct"
    return (
        map_data[coverage_column].mul(map_data["households"]).sum()
        / map_data["households"].sum()
    )


def style_color(value: float, threshold: float) -> str:
    if value >= threshold + 5:
        return PASS_COLORS[2]
    if value >= threshold:
        return PASS_COLORS[1]
    gap = threshold - value
    if gap < 5:
        return FAIL_COLORS[0]
    if gap < 15:
        return FAIL_COLORS[1]
    if gap < 30:
        return FAIL_COLORS[2]
    return FAIL_COLORS[3]


def coverage_color(value: float) -> str:
    if value >= 90:
        return "#2ca25f"
    if value >= 70:
        return "#f6c85f"
    if value >= 50:
        return "#fdae6b"
    return "#8c1d40"


def save_static_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tech = tech_by_key(STATIC_TECH_KEY)
    value_column = f"{STATIC_TECH_KEY}_2024_pct"
    uncovered_column = f"{STATIC_TECH_KEY}_uncovered_households_2024"

    plot_data = map_data.copy()
    plot_data["static_color"] = plot_data[value_column].map(
        lambda value: style_color(float(value), STATIC_THRESHOLD)
    )

    fig = plt.figure(figsize=(16, 9.5), dpi=180)
    grid = fig.add_gridspec(
        3,
        3,
        width_ratios=[1.32, 1.32, 0.96],
        height_ratios=[0.54, 1, 1],
        wspace=0.18,
        hspace=0.36,
    )
    map_ax = fig.add_subplot(grid[:, :2])
    summary_ax = fig.add_subplot(grid[0, 2])
    gap_ax = fig.add_subplot(grid[1, 2])
    tech_ax = fig.add_subplot(grid[2, 2])

    plot_data.plot(
        ax=map_ax,
        color=plot_data["static_color"],
        linewidth=0.06,
        edgecolor="#f8f8f8",
    )
    fallback = plot_data[plot_data[value_column].lt(STATIC_THRESHOLD)]
    if not fallback.empty:
        fallback.plot(
            ax=map_ax,
            facecolor="none",
            edgecolor="#4b2e83",
            linewidth=0.0,
            hatch="////",
            zorder=3,
        )

    weakest = plot_data.nsmallest(12, value_column)
    map_ax.scatter(
        weakest["label_lon"],
        weakest["label_lat"],
        s=22,
        color="#111111",
        edgecolor="#ffffff",
        linewidth=0.4,
        zorder=4,
    )

    map_ax.set_xlim(-18.8, 4.7)
    map_ax.set_ylim(27.3, 44.3)
    map_ax.set_title(
        f"Municipios segun cobertura {tech['short']} y respaldo satelital",
        fontsize=15.5,
        fontweight="bold",
        pad=12,
    )
    map_ax.set_axis_off()

    legend_handles = [
        mpatches.Patch(facecolor=PASS_COLORS[2], edgecolor="#666666", label=f">= {STATIC_THRESHOLD + 5}%"),
        mpatches.Patch(facecolor=PASS_COLORS[1], edgecolor="#666666", label=f"{STATIC_THRESHOLD}-{STATIC_THRESHOLD + 5}%"),
        mpatches.Patch(facecolor=FAIL_COLORS[1], edgecolor="#666666", label=f"No cumple {STATIC_THRESHOLD}%"),
        mpatches.Patch(facecolor="white", edgecolor="#4b2e83", hatch="////", label="Candidato a respaldo satelital"),
    ]
    map_ax.legend(
        handles=legend_handles,
        title=f"Cobertura {tech['short']}",
        loc="lower left",
        fontsize=7.5,
        title_fontsize=8.5,
        frameon=True,
        framealpha=0.96,
    )

    summary_ax.set_axis_off()
    avg_coverage = weighted_coverage(plot_data, STATIC_TECH_KEY)
    failing_count = int(plot_data[value_column].lt(STATIC_THRESHOLD).sum())
    affected_homes = float(
        plot_data.loc[plot_data[value_column].lt(STATIC_THRESHOLD), uncovered_column].sum()
    )
    summary_ax.text(0.0, 0.96, "Filtro municipal configurable", fontsize=11, fontweight="bold", va="top")
    summary_ax.text(0.0, 0.62, f"{avg_coverage:.1f}%", fontsize=23, fontweight="bold")
    summary_ax.text(0.0, 0.44, f"cobertura ponderada {tech['short']}", fontsize=8.5, color="#444444")
    summary_ax.text(
        0.0,
        0.18,
        f"{failing_count} municipios bajo {STATIC_THRESHOLD}%  |  {format_int(affected_homes)} hogares sin cobertura",
        fontsize=8.3,
        color="#222222",
    )

    gap = plot_data.nlargest(12, uncovered_column).sort_values(uncovered_column)
    gap_ax.barh(gap["municipality_name"], gap[uncovered_column], color="#8c1d40")
    gap_ax.set_title(f"Mas hogares sin {tech['short']}", fontsize=10.5, fontweight="bold")
    gap_ax.set_xlabel("Hogares estimados", fontsize=8.3)
    gap_ax.xaxis.set_major_formatter(FuncFormatter(format_axis_int))
    gap_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    gap_ax.tick_params(axis="both", labelsize=7.4)

    tech_values = [
        weighted_coverage(plot_data, item["key"]) for item in TECH_DEFINITIONS
    ]
    tech_labels = [item["short"] for item in TECH_DEFINITIONS]
    tech_ax.barh(tech_labels, tech_values, color=["#4eb3d3", "#2ca25f", "#238b45", "#807dba", "#6a51a3", "#54278f"])
    tech_ax.axvline(STATIC_THRESHOLD, color="#111111", linewidth=1, linestyle="--")
    tech_ax.set_xlim(0, 100)
    tech_ax.set_title("Cobertura ponderada por tecnologia", fontsize=10.5, fontweight="bold")
    tech_ax.set_xlabel("% hogares cubiertos", fontsize=8.3)
    tech_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    tech_ax.tick_params(axis="both", labelsize=8)

    for side_ax in [gap_ax, tech_ax]:
        for spine in ["top", "right", "left"]:
            side_ax.spines[spine].set_visible(False)

    fig.suptitle(
        "Mapa 4. Conectividad multitecnologia para teletrabajo",
        fontsize=19,
        fontweight="bold",
        x=0.43,
        y=0.985,
    )
    fig.text(
        0.02,
        0.02,
        "Fuente: SETELECO/Ministerio para la Transformacion Digital y Eurostat/GISCO LAU 2024. "
        "El respaldo satelital se representa de forma conceptual como complemento para zonas sin cobertura terrestre suficiente.",
        fontsize=8,
        color="#555555",
    )

    fig.savefig(OUTPUT_DIR / "mapa4_conectividad_teletrabajo.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa4_conectividad_teletrabajo.pdf", bbox_inches="tight")
    plt.close(fig)


def build_popup_preview(row: pd.Series) -> str:
    bars = []
    for tech in TECH_DEFINITIONS:
        value = float(row[f"{tech['key']}_2024_pct"])
        bars.append(
            f"""
            <div class="tech-popup-row">
              <span>{tech['short']}</span>
              <div class="tech-popup-bar"><i style="width:{max(0, min(100, value)):.1f}%"></i></div>
              <b>{value:.1f}%</b>
            </div>
            """
        )
    return "".join(bars)


class MultiTechControl(MacroElement):
    _template = Template(
        """
        {% macro header(this, kwargs) %}
        <style>
          #{{ this._parent.get_name() }} .multi-tech-control,
          #{{ this._parent.get_name() }} .multi-tech-legend {
            width: 306px;
            max-width: calc(100vw - 34px);
            padding: 10px 12px;
            border: 1px solid rgba(45, 45, 45, 0.55);
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 1px 5px rgba(0, 0, 0, 0.22);
            color: #1f1f1f;
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.3;
          }

          #{{ this._parent.get_name() }} .multi-tech-title {
            margin-bottom: 7px;
            font-size: 13px;
            font-weight: 700;
          }

          #{{ this._parent.get_name() }} .multi-tech-control label {
            display: block;
            margin-top: 7px;
            font-weight: 700;
          }

          #{{ this._parent.get_name() }} .multi-tech-control select,
          #{{ this._parent.get_name() }} .multi-tech-control input[type="range"] {
            width: 100%;
            margin-top: 4px;
          }

          #{{ this._parent.get_name() }} .multi-tech-speed-labels {
            display: flex;
            justify-content: space-between;
            margin-top: 2px;
            color: #555555;
            font-size: 10.5px;
          }

          #{{ this._parent.get_name() }} .multi-tech-check {
            display: flex;
            gap: 7px;
            align-items: center;
            margin-top: 8px;
            font-weight: 400;
          }

          #{{ this._parent.get_name() }} .multi-tech-stats {
            margin-top: 8px;
            padding-top: 7px;
            border-top: 1px solid #d5d5d5;
          }

          #{{ this._parent.get_name() }} .multi-tech-legend-row {
            display: flex;
            gap: 7px;
            align-items: center;
            margin: 4px 0;
          }

          #{{ this._parent.get_name() }} .multi-tech-swatch {
            width: 20px;
            height: 12px;
            border: 1px solid rgba(0,0,0,0.35);
            flex: 0 0 20px;
          }

          #{{ this._parent.get_name() }} .tech-popup {
            width: 270px;
            font-family: Arial, sans-serif;
            font-size: 12px;
            color: #1f1f1f;
          }

          #{{ this._parent.get_name() }} .tech-popup-title {
            margin-bottom: 6px;
            font-size: 14px;
            font-weight: 700;
          }

          #{{ this._parent.get_name() }} .tech-popup-meta {
            margin-bottom: 7px;
            color: #444;
            line-height: 1.25;
          }

          #{{ this._parent.get_name() }} .tech-popup-row {
            display: grid;
            grid-template-columns: 66px 1fr 46px;
            gap: 6px;
            align-items: center;
            margin: 4px 0;
          }

          #{{ this._parent.get_name() }} .tech-popup-bar {
            height: 8px;
            border-radius: 2px;
            background: #e6e6e6;
            overflow: hidden;
          }

          #{{ this._parent.get_name() }} .tech-popup-bar i {
            display: block;
            height: 100%;
            background: #2ca25f;
          }

          #{{ this._parent.get_name() }} .multi-tech-note {
            margin-top: 7px;
            color: #555555;
            font-size: 11px;
          }
        </style>
        {% endmacro %}

        {% macro script(this, kwargs) %}
        (function () {
          const map = {{ this._parent.get_name() }};
          const municipalLayer = {{ this.layer_name }};
          const satelliteBands = {{ this.satellite_bands|tojson }};
          const fixedOptions = [
            {key: "fixed_30", label: "30 Mbps", longLabel: "WiFi/fijo >=30 Mbps"},
            {key: "fixed_100", label: "100 Mbps", longLabel: "WiFi/fijo >=100 Mbps"},
            {key: "fixed_1gbps", label: "1 Gbps", longLabel: "WiFi/fijo >=1 Gbps"}
          ];
          const mobileOptions = {
            mobile_4g: {key: "mobile_4g", label: "4G", longLabel: "Cobertura movil 4G"},
            mobile_5g: {key: "mobile_5g", label: "5G", longLabel: "Cobertura movil 5G"}
          };

          let connectionMode = "fixed";
          let fixedIndex = 1;
          let satelliteEnabled = false;

          const satelliteLayer = L.layerGroup();
          satelliteBands.forEach(function (band) {
            L.polygon(band, {
              color: "#c40000",
              weight: 2.2,
              fillColor: "#e31a1c",
              fillOpacity: 0.14,
              opacity: 0.82,
              interactive: false
            }).addTo(satelliteLayer);
          });

          function escapeHtml(value) {
            return String(value ?? "")
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
          }

          function fmtNumber(value) {
            return Math.round(Number(value || 0)).toLocaleString("es-ES");
          }

          function getActiveTech() {
            if (connectionMode === "fixed") return fixedOptions[fixedIndex];
            return mobileOptions[connectionMode] || fixedOptions[fixedIndex];
          }

          function coverage(props, tech) {
            return Number(props[tech.key + "_2024_pct"] || 0);
          }

          function change(props, tech) {
            return Number(props[tech.key + "_change_pp"] || 0);
          }

          function colorFor(value) {
            if (value >= 90) return "#2ca25f";
            if (value >= 70) return "#f6c85f";
            if (value >= 50) return "#fdae6b";
            return "#8c1d40";
          }

          function styleFeature(props) {
            const tech = getActiveTech();
            const value = coverage(props, tech);
            return {
              fillColor: colorFor(value),
              fillOpacity: 0.74,
              color: "#555555",
              weight: 0.24,
              opacity: 0.52
            };
          }

          function renderBars(props) {
            const rows = [
              fixedOptions[fixedIndex],
              mobileOptions.mobile_4g,
              mobileOptions.mobile_5g
            ];
            return rows.map(function (tech) {
              const value = coverage(props, tech);
              return '<div class="tech-popup-row">' +
                '<span>' + escapeHtml(tech.label) + '</span>' +
                '<div class="tech-popup-bar"><i style="width:' + Math.max(0, Math.min(100, value)).toFixed(1) + '%"></i></div>' +
                '<b>' + value.toFixed(1) + '%</b>' +
              '</div>';
            }).join("");
          }

          function renderPopup(props) {
            const tech = getActiveTech();
            const value = coverage(props, tech);
            const status = value >= 90 ? "Cobertura alta" : value >= 70 ? "Cobertura media" : value >= 50 ? "Cobertura limitada" : "Cobertura baja";
            return '<div class="tech-popup">' +
              '<div class="tech-popup-title">' + escapeHtml(props.municipality_name) + '</div>' +
              '<div class="tech-popup-meta">' +
                escapeHtml(props.province_name) + '<br>' +
                'Conexion activa: <b>' + escapeHtml(tech.longLabel) + '</b><br>' +
                'Cobertura: <b>' + value.toFixed(1) + '%</b><br>' +
                'Cambio 2023-2024: <b>' + change(props, tech).toFixed(1) + ' pp</b><br>' +
                '<b>' + escapeHtml(status) + '</b>' +
              '</div>' +
              renderBars(props) +
            '</div>';
          }

          function updateMunicipalLayer() {
            const tech = getActiveTech();
            let weightedSum = 0;
            let householdSum = 0;
            let highCoverage = 0;
            let lowCoverage = 0;

            municipalLayer.eachLayer(function (layer) {
              const props = layer.feature.properties;
              const value = coverage(props, tech);
              const households = Number(props.households || 0);
              weightedSum += value * households;
              householdSum += households;
              if (value >= 90) highCoverage += 1;
              if (value < 50) lowCoverage += 1;
              layer.setStyle(styleFeature(props));
              layer.bindPopup(renderPopup(props), {maxWidth: 320});
            });

            updateStats(tech, highCoverage, lowCoverage, householdSum ? weightedSum / householdSum : 0);
          }

          function updateStats(tech, highCoverage, lowCoverage, weightedCoverage) {
            const statsNode = document.getElementById("multi-tech-stats-{{ this.get_name() }}");
            if (!statsNode) return;
            statsNode.innerHTML =
              '<b>' + escapeHtml(tech.longLabel) + '</b><br>' +
              'Cobertura ponderada: <b>' + weightedCoverage.toFixed(1) + '%</b><br>' +
              'Municipios con cobertura alta: <b>' + fmtNumber(highCoverage) + '</b><br>' +
              'Municipios con cobertura baja: <b>' + fmtNumber(lowCoverage) + '</b>';
          }

          function updateSpeedVisibility() {
            const speedBlock = document.getElementById("speed-block-{{ this.get_name() }}");
            if (speedBlock) speedBlock.style.display = connectionMode === "fixed" ? "block" : "none";
          }

          const control = L.control({position: "topleft"});
          control.onAdd = function () {
            this._container = L.DomUtil.create("div", "multi-tech-control leaflet-control");
            L.DomEvent.disableClickPropagation(this._container);
            L.DomEvent.disableScrollPropagation(this._container);

            this._container.innerHTML =
              '<div class="multi-tech-title">Conexion terrestre + satelite</div>' +
              '<label for="connection-select-{{ this.get_name() }}">Conexion terrestre</label>' +
              '<select id="connection-select-{{ this.get_name() }}">' +
                '<option value="fixed" selected>WiFi/fijo</option>' +
                '<option value="mobile_4g">4G</option>' +
                '<option value="mobile_5g">5G</option>' +
              '</select>' +
              '<div id="speed-block-{{ this.get_name() }}">' +
                '<label for="speed-slider-{{ this.get_name() }}">Velocidad fija: <span id="speed-value-{{ this.get_name() }}">100 Mbps</span></label>' +
                '<input id="speed-slider-{{ this.get_name() }}" type="range" min="0" max="2" step="1" value="1">' +
                '<div class="multi-tech-speed-labels"><span>30</span><span>100</span><span>1000 Mbps</span></div>' +
              '</div>' +
              '<label class="multi-tech-check"><input id="satellite-check-{{ this.get_name() }}" type="checkbox"> Mostrar conexion satelital</label>' +
              '<div class="multi-tech-note">La capa satelital es general y conceptual, no una huella orbital exacta.</div>' +
              '<div class="multi-tech-stats" id="multi-tech-stats-{{ this.get_name() }}"></div>';
            return this._container;
          };
          control.addTo(map);

          const legend = L.control({position: "bottomright"});
          legend.onAdd = function () {
            this._container = L.DomUtil.create("div", "multi-tech-legend leaflet-control");
            L.DomEvent.disableClickPropagation(this._container);
            this._container.innerHTML =
              '<div class="multi-tech-title">Lectura del color</div>' +
              '<div class="multi-tech-legend-row"><span class="multi-tech-swatch" style="background:#2ca25f"></span><span>Cobertura alta (>=90%)</span></div>' +
              '<div class="multi-tech-legend-row"><span class="multi-tech-swatch" style="background:#f6c85f"></span><span>Cobertura media (70-90%)</span></div>' +
              '<div class="multi-tech-legend-row"><span class="multi-tech-swatch" style="background:#fdae6b"></span><span>Cobertura limitada (50-70%)</span></div>' +
              '<div class="multi-tech-legend-row"><span class="multi-tech-swatch" style="background:#8c1d40"></span><span>Cobertura baja (<50%)</span></div>' +
              '<div class="multi-tech-legend-row"><span class="multi-tech-swatch" style="background:#e31a1c"></span><span>Conexion satelital general</span></div>';
            return this._container;
          };
          legend.addTo(map);

          setTimeout(function () {
            const connectionSelect = document.getElementById("connection-select-{{ this.get_name() }}");
            const speedSlider = document.getElementById("speed-slider-{{ this.get_name() }}");
            const speedValue = document.getElementById("speed-value-{{ this.get_name() }}");
            const satelliteCheck = document.getElementById("satellite-check-{{ this.get_name() }}");

            connectionSelect.addEventListener("change", function (event) {
              connectionMode = event.target.value;
              updateSpeedVisibility();
              updateMunicipalLayer();
            });

            speedSlider.addEventListener("input", function (event) {
              fixedIndex = Number(event.target.value);
              speedValue.textContent = fixedOptions[fixedIndex].label;
              updateMunicipalLayer();
            });

            satelliteCheck.addEventListener("change", function (event) {
              satelliteEnabled = event.target.checked;
              if (satelliteEnabled) {
                satelliteLayer.addTo(map);
              } else {
                map.removeLayer(satelliteLayer);
              }
            });
            updateSpeedVisibility();
          }, 0);

          updateMunicipalLayer();
        })();
        {% endmacro %}
        """
    )

    def __init__(
        self,
        layer_name: str,
    ) -> None:
        super().__init__()
        self._name = "MultiTechControl"
        self.layer_name = layer_name
        self.satellite_bands = SATELLITE_BANDS


def save_interactive_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html_data = simplify_for_html(map_data)

    property_columns = [
        "CMUN",
        "COD_PROVINCIA",
        "municipality_name",
        "province_name",
        "ccaa",
        "population",
        "households",
        "default_status",
        "default_gap_pct",
        "label_lat",
        "label_lon",
    ]
    for tech in TECH_DEFINITIONS:
        property_columns.extend(
            [
                f"{tech['key']}_2023_pct",
                f"{tech['key']}_2024_pct",
                f"{tech['key']}_change_pp",
                f"{tech['key']}_uncovered_households_2024",
            ]
        )

    html_data = html_data[property_columns + ["geometry"]].copy()

    web_map = folium.Map(
        location=[40.1, -3.7],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True,
        max_bounds=True,
        prefer_canvas=True,
    )
    web_map.fit_bounds([[35.4, -10.0], [43.9, 4.7]])

    default_column = f"{DEFAULT_TECH_KEY}_2024_pct"
    municipal_layer = folium.GeoJson(
        html_data,
        name="Municipios: conectividad multitecnologia",
        show=True,
        style_function=lambda feature: {
            "fillColor": coverage_color(float(feature["properties"][default_column])),
            "color": "#555555",
            "weight": 0.24,
            "fillOpacity": 0.74,
        },
        highlight_function=lambda _: {"weight": 1.4, "color": "#111111", "fillOpacity": 0.9},
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "municipality_name",
                "province_name",
                f"{DEFAULT_TECH_KEY}_2024_pct",
                "default_status",
                "households",
            ],
            aliases=[
                "Municipio",
                "Provincia",
                f"{tech_by_key(DEFAULT_TECH_KEY)['short']} 2024",
                "Lectura inicial",
                "Hogares",
            ],
            localize=True,
            labels=True,
            sticky=False,
        ),
    ).add_to(web_map)

    MultiTechControl(layer_name=municipal_layer.get_name()).add_to(web_map)

    plugins.Search(
        layer=municipal_layer,
        geom_type="Polygon",
        placeholder="Buscar municipio",
        collapsed=True,
        search_label="municipality_name",
        position="topleft",
    ).add_to(web_map)
    plugins.MiniMap(toggle_display=True, minimized=True, position="bottomright").add_to(web_map)
    plugins.Fullscreen(position="topright").add_to(web_map)
    plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(web_map)
    plugins.MousePosition(
        position="bottomleft",
        separator=", ",
        prefix="Coordenadas",
        num_digits=4,
    ).add_to(web_map)
    folium.LayerControl(collapsed=False).add_to(web_map)

    web_map.save(OUTPUT_DIR / "mapa4_conectividad_teletrabajo_interactivo.html")


def save_tables(map_data: gpd.GeoDataFrame, stats: dict[str, int]) -> None:
    columns = [
        "CMUN",
        "COD_PROVINCIA",
        "municipality_name",
        "province_name",
        "ccaa",
        "population",
        "households",
        "area_km2",
        "label_lat",
        "label_lon",
        "default_status",
        "default_gap_pct",
        "default_uncovered_households_2024",
    ]
    for tech in TECH_DEFINITIONS:
        columns.extend(
            [
                f"{tech['key']}_2023_pct",
                f"{tech['key']}_2024_pct",
                f"{tech['key']}_change_pp",
                f"{tech['key']}_uncovered_households_2024",
            ]
        )

    table = map_data[columns].sort_values(
        f"{DEFAULT_TECH_KEY}_2024_pct", ascending=False
    ).copy()
    table["default_technology"] = DEFAULT_TECH_KEY
    table["default_threshold_pct"] = DEFAULT_THRESHOLD
    table["year"] = 2024
    table.to_csv(OUTPUT_DIR / "mapa4_conectividad_teletrabajo_datos.csv", index=False)

    pd.DataFrame([stats]).to_csv(
        OUTPUT_DIR / "mapa4_conectividad_teletrabajo_validacion_union.csv",
        index=False,
    )


def main() -> None:
    map_data, stats = build_dataset()
    save_static_map(map_data)
    save_interactive_map(map_data)
    save_tables(map_data, stats)

    print("Mapa 4 generado como conectividad municipal multitecnologia.")
    print(
        "Union municipal: "
        f"{stats['matched_municipalities']} con dato, "
        f"{stats['geometries_without_data']} geometria(s) sin dato, "
        f"{stats['data_without_geometry']} dato(s) sin geometria."
    )
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
