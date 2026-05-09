from __future__ import annotations

from pathlib import Path
import html
import os
import re
import shutil
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

CRIME_URL = (
    "https://estadisticasdecriminalidad.ses.mir.es/sec/jaxiPx/files/_px/es/"
    "csv_bdsc/DatosBalanceAnt/l0/1409012.csv_bdsc"
)
BROADBAND_URL = (
    "https://digital.gob.es/content/dam/portal-mtdfp/avance-digital/"
    "telecomunicacion-e-infraestructuras-digitales/areas_interes/banda-ancha/"
    "cobertura/documents/cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx"
)
NUTS_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson"
LAU_URL = "https://gisco-services.ec.europa.eu/distribution/v2/lau/geojson/LAU_RG_01M_2024_4326.geojson"

CRIME_FILE = DATA_DIR / "criminalidad_balance_2024_municipios_mas_20000.csv"
BROADBAND_FILE = DATA_DIR / "cobertura_ba_espana_2021_2024.xlsx"
NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"
LAU_FILE = DATA_DIR / "lau_2024_01m.geojson"

CRIME_TYPE = "III. TOTAL INFRACCIONES PENALES"
CRIME_PERIOD = "enero-diciembre 2024"
PROVINCE_PALETTE = ["#f0f9e8", "#bae4bc", "#7bccc4", "#fdae61", "#d7301f"]
POINT_PALETTE = ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"]

PROVINCE_BY_NUTS = {
    "ES111": "15", "ES112": "27", "ES113": "32", "ES114": "36", "ES120": "33",
    "ES130": "39", "ES211": "01", "ES212": "20", "ES213": "48", "ES220": "31",
    "ES230": "26", "ES241": "22", "ES242": "44", "ES243": "50", "ES300": "28",
    "ES411": "05", "ES412": "09", "ES413": "24", "ES414": "34", "ES415": "37",
    "ES416": "40", "ES417": "42", "ES418": "47", "ES419": "49", "ES421": "02",
    "ES422": "13", "ES423": "16", "ES424": "19", "ES425": "45", "ES431": "06",
    "ES432": "10", "ES511": "08", "ES512": "17", "ES513": "25", "ES514": "43",
    "ES521": "03", "ES522": "12", "ES523": "46", "ES531": "07", "ES532": "07",
    "ES533": "07", "ES611": "04", "ES612": "11", "ES613": "14", "ES614": "18",
    "ES615": "21", "ES616": "23", "ES617": "29", "ES618": "41", "ES620": "30",
    "ES630": "51", "ES640": "52", "ES703": "38", "ES704": "35", "ES705": "35",
    "ES706": "38", "ES707": "38", "ES708": "35", "ES709": "38",
}

PROVINCE_CODE_BY_NAME = {
    "araba/alava": "01", "albacete": "02", "alicante/alacant": "03", "almeria": "04",
    "avila": "05", "badajoz": "06", "balears, illes": "07", "illes balears": "07",
    "balears (illes)": "07", "barcelona": "08", "burgos": "09", "caceres": "10",
    "cadiz": "11", "castellon/castello": "12", "castellon": "12",
    "ciudad real": "13", "cordoba": "14", "coruna, a": "15", "a coruna": "15",
    "coruna (a)": "15", "cuenca": "16", "girona": "17", "granada": "18", "guadalajara": "19",
    "gipuzkoa": "20", "huelva": "21", "huesca": "22", "jaen": "23", "leon": "24",
    "lleida": "25", "rioja, la": "26", "la rioja": "26", "rioja (la)": "26",
    "lugo": "27", "madrid": "28", "madrid (comunidad de)": "28", "malaga": "29",
    "murcia": "30", "murcia (region de)": "30", "navarra": "31",
    "navarra (comunidad foral de)": "31", "ourense": "32",
    "asturias": "33", "asturias (principado de)": "33", "palencia": "34",
    "palmas, las": "35", "palmas (las)": "35", "las palmas": "35", "pontevedra": "36", "salamanca": "37",
    "santa cruz de tenerife": "38", "cantabria": "39", "segovia": "40",
    "sevilla": "41", "soria": "42", "tarragona": "43", "teruel": "44",
    "toledo": "45", "valencia/valencia": "46", "valencia": "46",
    "valladolid": "47", "bizkaia": "48", "zamora": "49", "zaragoza": "50",
    "ceuta": "51", "ciudad autonoma de ceuta": "51", "melilla": "52",
    "ciudad autonoma de melilla": "52",
}


def download_file(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=90, headers={"User-Agent": "VD-map-project/1.0"})
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


def parse_number(value: object) -> float:
    text = str(value).strip().replace(".", "").replace(",", ".")
    return pd.to_numeric(text, errors="coerce")


def format_int(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):,.0f}".replace(",", ".")


def format_rate(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):.1f}"


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
    if pd.isna(value):
        return "#cfcfcf"
    for index, upper in enumerate(bins[1:]):
        if float(value) <= upper or index == len(colors) - 1:
            return colors[index]
    return colors[-1]


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


def classify_reading(rate: float) -> str:
    if pd.isna(rate):
        return "Sin dato"
    if rate < 32:
        return "Presion baja"
    if rate < 42:
        return "Presion media-baja"
    if rate < 52:
        return "Presion media"
    if rate < 65:
        return "Presion alta"
    return "Presion muy alta"


def load_province_geometries() -> gpd.GeoDataFrame:
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])
    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    return provinces[["COD_PROVINCIA", "geometry"]].to_crs("EPSG:4326")


def load_lau_points() -> gpd.GeoDataFrame:
    lau = gpd.read_file(LAU_FILE)
    lau = lau[lau["CNTR_CODE"].eq("ES")].copy()
    lau["CMUN"] = lau["GISCO_ID"].str.replace("ES_", "", regex=False)
    projected = lau.to_crs("EPSG:3035")
    points = projected.geometry.representative_point().to_crs("EPSG:4326")
    lau["lon"] = points.x
    lau["lat"] = points.y
    return lau[["CMUN", "LAU_NAME", "lat", "lon", "geometry"]].to_crs("EPSG:4326")


def load_population() -> tuple[pd.DataFrame, pd.DataFrame]:
    municipal = pd.read_excel(BROADBAND_FILE, sheet_name="Municipio_%hogar")
    municipal = municipal.rename(columns=normalize_columns(municipal.columns))
    municipal["CMUN"] = municipal["CMUN"].astype(str).str.zfill(5)
    municipal["COD_PROVINCIA"] = municipal["CMUN"].str[:2]
    municipal["population"] = pd.to_numeric(municipal["Habitantes"], errors="coerce")
    municipal = municipal[["CMUN", "COD_PROVINCIA", "Municipio", "population"]].copy()

    provincial = pd.read_excel(BROADBAND_FILE, sheet_name="Provincia_%hogar")
    provincial = provincial.rename(columns=normalize_columns(provincial.columns))
    provincial["COD_PROVINCIA"] = provincial["Provincia"].map(
        lambda value: PROVINCE_CODE_BY_NAME.get(normalize_text(value))
    )
    provincial["population"] = pd.to_numeric(provincial["Habitantes"], errors="coerce")
    provincial = provincial[["COD_PROVINCIA", "Provincia", "population"]].rename(
        columns={"Provincia": "province_name"}
    )
    return municipal, provincial


def load_crime() -> pd.DataFrame:
    crime = pd.read_csv(CRIME_FILE, sep=";", encoding="utf-8-sig")
    crime = crime[
        crime["Tipología penal"].eq(CRIME_TYPE) & crime["Periodos:"].eq(CRIME_PERIOD)
    ].copy()
    crime["crime_total"] = crime["Total"].map(parse_number)
    return crime[["Geografía", "crime_total"]]


def extract_province_code(geography: str) -> str | None:
    text = str(geography).strip()
    if text.startswith("Provincia de "):
        name = text.replace("Provincia de ", "", 1)
        return PROVINCE_CODE_BY_NAME.get(normalize_text(name))
    if text in {"NACIONAL", "EXTRANJERA"}:
        return None
    if re.match(r"^\d{5}\s+", text):
        return None
    if text.startswith("Isla de "):
        return None
    return PROVINCE_CODE_BY_NAME.get(normalize_text(text))


def build_dataset() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, list[float], list[float]]:
    download_file(CRIME_URL, CRIME_FILE)
    download_file(BROADBAND_URL, BROADBAND_FILE)
    download_file(NUTS_URL, NUTS_FILE)
    download_file(LAU_URL, LAU_FILE)

    municipal_population, provincial_population = load_population()
    crime = load_crime()

    provincial_crime = crime.copy()
    provincial_crime["COD_PROVINCIA"] = provincial_crime["Geografía"].map(extract_province_code)
    provincial_crime = provincial_crime.dropna(subset=["COD_PROVINCIA"])
    provincial_crime = provincial_crime.groupby("COD_PROVINCIA", as_index=False).agg(
        crime_total=("crime_total", "sum")
    )

    provinces = load_province_geometries()
    map_data = (
        provinces.merge(provincial_population, on="COD_PROVINCIA", how="left")
        .merge(provincial_crime, on="COD_PROVINCIA", how="left")
    )
    map_data["crime_rate_per_1000"] = map_data["crime_total"] / map_data["population"] * 1000
    map_data["safety_score"] = 100 - (
        (map_data["crime_rate_per_1000"] - map_data["crime_rate_per_1000"].min())
        / (map_data["crime_rate_per_1000"].max() - map_data["crime_rate_per_1000"].min())
        * 100
    )
    map_data["safety_reading"] = map_data["crime_rate_per_1000"].map(classify_reading)

    projected = map_data.to_crs("EPSG:3035")
    points = projected.geometry.representative_point().to_crs("EPSG:4326")
    map_data["label_lon"] = points.x
    map_data["label_lat"] = points.y

    municipal_crime = crime[crime["Geografía"].str.match(r"^\d{5}\s+", na=False)].copy()
    municipal_crime["CMUN"] = municipal_crime["Geografía"].str.extract(r"^(\d{5})")
    municipal_crime["municipality_name_crime"] = municipal_crime["Geografía"].str.replace(
        r"^\d{5}\s+", "", regex=True
    )
    municipal_points = (
        municipal_crime.merge(municipal_population, on="CMUN", how="left")
        .merge(load_lau_points()[["CMUN", "lat", "lon", "geometry"]], on="CMUN", how="left")
    )
    municipal_points["crime_rate_per_1000"] = (
        municipal_points["crime_total"] / municipal_points["population"] * 1000
    )
    municipal_points["safety_reading"] = municipal_points["crime_rate_per_1000"].map(
        classify_reading
    )
    municipal_points = gpd.GeoDataFrame(
        municipal_points.dropna(subset=["lat", "lon", "population", "crime_rate_per_1000"]),
        geometry="geometry",
        crs="EPSG:4326",
    )

    province_bins = build_quantile_bins(map_data["crime_rate_per_1000"], 5)
    point_bins = build_quantile_bins(municipal_points["crime_rate_per_1000"], 5)
    map_data["province_color"] = map_data["crime_rate_per_1000"].map(
        lambda value: color_for_bins(value, province_bins, PROVINCE_PALETTE)
    )
    municipal_points["point_color"] = municipal_points["crime_rate_per_1000"].map(
        lambda value: color_for_bins(value, point_bins, POINT_PALETTE)
    )
    return map_data, municipal_points, province_bins, point_bins


def save_static_map(
    map_data: gpd.GeoDataFrame,
    municipal_points: gpd.GeoDataFrame,
    province_bins: list[float],
    point_bins: list[float],
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(16, 9.5), dpi=180)
    grid = fig.add_gridspec(2, 3, width_ratios=[1.25, 1.25, 0.95], hspace=0.34, wspace=0.2)
    map_ax = fig.add_subplot(grid[:, :2])
    ranking_ax = fig.add_subplot(grid[0, 2])
    points_ax = fig.add_subplot(grid[1, 2])

    map_data.plot(
        ax=map_ax,
        color=map_data["province_color"],
        linewidth=0.42,
        edgecolor="#ffffff",
    )
    map_data.boundary.plot(ax=map_ax, color="#555555", linewidth=0.14, alpha=0.55)

    top_points = municipal_points.nlargest(65, "crime_total")
    sizes = (top_points["crime_total"] ** 0.5).clip(8, 46)
    map_ax.scatter(
        top_points["lon"],
        top_points["lat"],
        s=sizes,
        c=top_points["point_color"],
        edgecolor="#1f1f1f",
        linewidth=0.25,
        alpha=0.78,
        zorder=4,
    )

    safest = map_data.nsmallest(7, "crime_rate_per_1000")
    for _, row in safest.iterrows():
        text = map_ax.annotate(
            f"{row['province_name']}\n{row['crime_rate_per_1000']:.1f}",
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
    map_ax.set_axis_off()
    legend_handles = [
        mpatches.Patch(facecolor=color, edgecolor="#666666", label=label)
        for color, label in zip(PROVINCE_PALETTE, build_bin_labels(province_bins))
    ]
    map_ax.legend(
        handles=legend_handles,
        title="Delitos por 1.000 hab.",
        loc="lower right",
        fontsize=7.6,
        title_fontsize=8.7,
        frameon=True,
        framealpha=0.96,
    )
    map_ax.set_title(
        "Seguridad relativa y poblacion: tasa provincial y puntos municipales disponibles",
        fontsize=16.2,
        fontweight="bold",
        pad=12,
    )

    safest_rank = map_data.nsmallest(10, "crime_rate_per_1000").sort_values(
        "crime_rate_per_1000"
    )
    ranking_ax.barh(
        safest_rank["province_name"],
        safest_rank["crime_rate_per_1000"],
        color="#7bccc4",
        edgecolor="#555555",
        linewidth=0.35,
    )
    ranking_ax.set_title("Menor presion delictiva", fontsize=11, fontweight="bold")
    ranking_ax.set_xlabel("Delitos por 1.000 habitantes", fontsize=8.5)
    ranking_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    ranking_ax.tick_params(axis="both", labelsize=8)

    largest_points = municipal_points.nlargest(10, "crime_total").sort_values("crime_total")
    points_ax.barh(
        largest_points["municipality_name_crime"],
        largest_points["crime_total"],
        color=largest_points["point_color"],
        edgecolor="#555555",
        linewidth=0.35,
    )
    points_ax.set_title("Municipios con mas hechos", fontsize=11, fontweight="bold")
    points_ax.set_xlabel("Hechos conocidos", fontsize=8.5)
    points_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    points_ax.tick_params(axis="both", labelsize=8)

    for side_ax in [ranking_ax, points_ax]:
        for spine in ["top", "right", "left"]:
            side_ax.spines[spine].set_visible(False)

    fig.suptitle(
        "Mapa 2. Seguridad y poblacion (criminalidad 2024)",
        fontsize=20,
        fontweight="bold",
        x=0.44,
        y=0.985,
    )
    fig.text(
        0.02,
        0.018,
        "Fuente: Ministerio del Interior, Balance de Criminalidad 2024; poblacion/hogares de SETELECO "
        "y cartografia Eurostat/GISCO. Los puntos son municipios agregados disponibles, no delitos individuales.",
        fontsize=8,
        color="#555555",
    )

    fig.savefig(OUTPUT_DIR / "mapa2_seguridad_poblacion.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa2_seguridad_poblacion.pdf", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa2_evolucion_alquiler.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa2_evolucion_alquiler.pdf", bbox_inches="tight")
    plt.close(fig)


def add_legend(web_map: folium.Map, bins: list[float], colors: list[str], title: str) -> None:
    rows = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:6px; margin:3px 0;">
          <span style="width:18px; height:12px; display:inline-block; background:{color};
          border:1px solid rgba(0,0,0,0.35);"></span>
          <span>{label}</span>
        </div>
        """
        for color, label in zip(colors, build_bin_labels(bins))
    )
    html_block = f"""
    <div style="
      position: fixed; bottom: 28px; right: 18px; z-index: 9999;
      background: rgba(255,255,255,0.94); padding: 10px 12px;
      border: 1px solid rgba(80,80,80,0.55); border-radius: 4px;
      font-family: Arial, sans-serif; font-size: 12px; line-height: 1.25;
      box-shadow: 0 1px 5px rgba(0,0,0,0.22);">
      <div style="font-weight:700; margin-bottom:5px;">{html.escape(title)}</div>
      {rows}
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(html_block))


def save_interactive_map(
    map_data: gpd.GeoDataFrame,
    municipal_points: gpd.GeoDataFrame,
    province_bins: list[float],
    point_bins: list[float],
) -> None:
    web_map = folium.Map(location=[40.2, -3.7], zoom_start=6, tiles="cartodbpositron")
    plugins.Fullscreen(position="topleft").add_to(web_map)
    plugins.MiniMap(toggle_display=True, minimized=True).add_to(web_map)
    folium.plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(
        web_map
    )

    province_layer = folium.FeatureGroup(name="Tasa provincial por 1.000 habitantes", show=True)
    folium.GeoJson(
        map_data,
        name="Tasa provincial",
        style_function=lambda feature: {
            "fillColor": feature["properties"]["province_color"],
            "color": "#555555",
            "weight": 0.55,
            "fillOpacity": 0.82,
        },
        highlight_function=lambda feature: {"weight": 2, "color": "#111111"},
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "province_name",
                "crime_total",
                "population",
                "crime_rate_per_1000",
                "safety_reading",
            ],
            aliases=[
                "Provincia",
                "Hechos conocidos",
                "Habitantes",
                "Delitos / 1.000 hab.",
                "Lectura",
            ],
            localize=True,
            sticky=False,
        ),
        popup=folium.GeoJsonPopup(
            fields=[
                "province_name",
                "crime_total",
                "population",
                "crime_rate_per_1000",
                "safety_score",
                "safety_reading",
            ],
            aliases=[
                "Provincia",
                "Hechos conocidos",
                "Habitantes",
                "Delitos / 1.000 hab.",
                "Score seguridad",
                "Lectura",
            ],
            localize=True,
            max_width=360,
        ),
    ).add_to(province_layer)
    province_layer.add_to(web_map)

    point_layer = plugins.MarkerCluster(name="Municipios disponibles en el balance", show=True)
    for _, row in municipal_points.iterrows():
        radius = max(4, min(18, float(row["crime_total"]) ** 0.5 / 8))
        popup_html = (
            f"<b>{html.escape(str(row['municipality_name_crime']))}</b><br>"
            f"Provincia: {html.escape(str(row['COD_PROVINCIA']))}<br>"
            f"Hechos conocidos: {format_int(row['crime_total'])}<br>"
            f"Habitantes: {format_int(row['population'])}<br>"
            f"Tasa: {format_rate(row['crime_rate_per_1000'])} por 1.000 hab.<br>"
            f"{html.escape(str(row['safety_reading']))}<br><br>"
            "Punto municipal agregado; no localiza delitos individuales."
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color="#262626",
            weight=0.45,
            fill=True,
            fill_color=row["point_color"],
            fill_opacity=0.78,
            tooltip=(
                f"{row['municipality_name_crime']}: "
                f"{format_rate(row['crime_rate_per_1000'])} delitos/1.000 hab."
            ),
            popup=folium.Popup(popup_html, max_width=340),
        ).add_to(point_layer)
    point_layer.add_to(web_map)

    add_legend(web_map, province_bins, PROVINCE_PALETTE, "Tasa provincial")
    folium.LayerControl(collapsed=False).add_to(web_map)
    web_map.save(OUTPUT_DIR / "mapa2_seguridad_poblacion_interactivo.html")
    shutil.copyfile(
        OUTPUT_DIR / "mapa2_seguridad_poblacion_interactivo.html",
        OUTPUT_DIR / "mapa2_evolucion_alquiler_interactivo.html",
    )


def save_tables(map_data: gpd.GeoDataFrame, municipal_points: gpd.GeoDataFrame) -> None:
    province_columns = [
        "COD_PROVINCIA",
        "province_name",
        "population",
        "crime_total",
        "crime_rate_per_1000",
        "safety_score",
        "safety_reading",
        "label_lat",
        "label_lon",
    ]
    municipal_columns = [
        "CMUN",
        "COD_PROVINCIA",
        "municipality_name_crime",
        "population",
        "crime_total",
        "crime_rate_per_1000",
        "safety_reading",
        "lat",
        "lon",
    ]
    map_data[province_columns].round(2).to_csv(
        OUTPUT_DIR / "mapa2_seguridad_poblacion_datos.csv", index=False
    )
    map_data[province_columns].round(2).to_csv(
        OUTPUT_DIR / "mapa2_evolucion_alquiler_datos.csv", index=False
    )
    municipal_points[municipal_columns].round(2).to_csv(
        OUTPUT_DIR / "mapa2_seguridad_poblacion_municipios.csv", index=False
    )


def main() -> None:
    map_data, municipal_points, province_bins, point_bins = build_dataset()
    missing = map_data[map_data[["crime_total", "population", "crime_rate_per_1000"]].isna().any(axis=1)]
    if not missing.empty:
        raise ValueError(
            "Faltan datos provinciales de criminalidad/poblacion para: "
            + ", ".join(missing["COD_PROVINCIA"].tolist())
        )
    save_static_map(map_data, municipal_points, province_bins, point_bins)
    save_interactive_map(map_data, municipal_points, province_bins, point_bins)
    save_tables(map_data, municipal_points)
    print("Mapa 2 generado: seguridad y poblacion con criminalidad 2024.")
    print(f"Provincias: {len(map_data)} | municipios disponibles: {len(municipal_points)}")


if __name__ == "__main__":
    main()
