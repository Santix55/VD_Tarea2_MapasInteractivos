from __future__ import annotations

from calendar import monthrange
from pathlib import Path
import os
import sys
from time import sleep


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
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import pandas as pd
import requests


DATA_DIR = BASE_DIR / "datos"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"

NUTS_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson"
POWER_MONTHLY_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"

NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"
TEMPERATURE_FILE = DATA_DIR / "nasa_power_temperatura_provincias_1995_2024.csv"

START_YEAR = 1995
END_YEAR = 2024

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


def calculate_weighted_annual_mean(monthly_values: dict[str, float]) -> float:
    weighted_sum = 0.0
    total_days = 0

    for key, value in monthly_values.items():
        if value is None or float(value) <= -900:
            continue

        year = int(str(key)[:4])
        month = int(str(key)[4:6])
        if not 1 <= month <= 12:
            continue
        days = monthrange(year, month)[1]
        weighted_sum += float(value) * days
        total_days += days

    if total_days == 0:
        raise ValueError("NASA POWER no devolvio valores mensuales validos.")

    return weighted_sum / total_days


def fetch_temperature_for_point(latitude: float, longitude: float) -> float:
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

    monthly_values = payload["properties"]["parameter"]["T2M"]
    return calculate_weighted_annual_mean(monthly_values)


def load_temperature_by_province(provinces: gpd.GeoDataFrame) -> pd.DataFrame:
    if TEMPERATURE_FILE.exists() and TEMPERATURE_FILE.stat().st_size > 0:
        return pd.read_csv(TEMPERATURE_FILE, dtype={"COD_PROVINCIA": str})

    rows = []
    points = provinces.copy()
    points["point"] = points.geometry.representative_point()

    for _, row in points.sort_values("COD_PROVINCIA").iterrows():
        point = row["point"]
        # Pausa suave para no castigar la API con 52 peticiones seguidas.
        annual_temp = fetch_temperature_for_point(point.y, point.x)
        rows.append(
            {
                "COD_PROVINCIA": row["COD_PROVINCIA"],
                "province_name": row["province_name"],
                "latitude": point.y,
                "longitude": point.x,
                "temperature_mean_c": annual_temp,
                "start_year": START_YEAR,
                "end_year": END_YEAR,
            }
        )
        sleep(0.15)

    temperature = pd.DataFrame(rows)
    TEMPERATURE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temperature.to_csv(TEMPERATURE_FILE, index=False)
    return temperature


def build_dataset() -> gpd.GeoDataFrame:
    download_file(NUTS_URL, NUTS_FILE)

    provinces = load_province_geometries()
    temperature = load_temperature_by_province(provinces)
    map_data = provinces.merge(
        temperature.drop(columns=["province_name"], errors="ignore"),
        on="COD_PROVINCIA",
        how="left",
    )

    missing = map_data[map_data["temperature_mean_c"].isna()]
    if not missing.empty:
        missing_codes = ", ".join(missing["COD_PROVINCIA"].tolist())
        raise ValueError(f"Faltan datos de temperatura para estas provincias: {missing_codes}")

    return add_climate_metrics(map_data)


def add_climate_metrics(map_data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    data = map_data.copy()
    projected = data.to_crs("EPSG:3035")
    data["area_km2"] = projected.area / 1_000_000

    country_mean = data["temperature_mean_c"].mean()
    data["temperature_anomaly_c"] = data["temperature_mean_c"] - country_mean

    # Para teletrabajo se premia el clima templado: ni frio continuado ni calor excesivo.
    comfort_target = 17.0
    comfort_gap = (data["temperature_mean_c"] - comfort_target).abs()
    data["climate_comfort_score"] = 100 * (1 - comfort_gap / comfort_gap.max())
    data["climate_comfort_score"] = data["climate_comfort_score"].round(1)

    data["climate_group"] = pd.cut(
        data["temperature_mean_c"],
        bins=[-float("inf"), 12, 15, 17, float("inf")],
        labels=["Fria", "Templada fresca", "Templada", "Calida"],
    ).astype(str)
    return data


def classify_temperatures(values: pd.Series) -> list[float]:
    classifier = mapclassify.NaturalBreaks(values, k=5)
    bins = [float(values.min())] + [float(value) for value in classifier.bins]
    bins[0] -= 0.1
    return bins


def color_for_anomaly(value: float) -> str:
    if value < -1.5:
        return "#2b6cb0"
    if value < 0:
        return "#63b3ed"
    if value < 1.5:
        return "#f6ad55"
    return "#c53030"


def save_static_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    bins = classify_temperatures(map_data["temperature_mean_c"])
    fig = plt.figure(figsize=(16, 9.5), dpi=180)
    grid = fig.add_gridspec(
        nrows=2,
        ncols=2,
        width_ratios=[3.35, 1],
        height_ratios=[2.25, 1],
        wspace=0.16,
        hspace=0.48,
    )
    ax = fig.add_subplot(grid[:, 0])
    rank_ax = fig.add_subplot(grid[0, 1])
    hist_ax = fig.add_subplot(grid[1, 1])

    map_data.plot(
        column="temperature_mean_c",
        ax=ax,
        cmap="Spectral_r",
        scheme="UserDefined",
        classification_kwds={"bins": bins[1:]},
        linewidth=0.45,
        edgecolor="#ffffff",
        legend=True,
        legend_kwds={
            "title": "Temperatura media (C)",
            "loc": "lower left",
            "frameon": True,
            "fmt": "{:.1f}",
        },
    )
    temperature_legend = ax.get_legend()
    map_data.boundary.plot(ax=ax, color="#5f6368", linewidth=0.18, alpha=0.55, zorder=3)
    if temperature_legend is not None:
        temperature_legend.set_bbox_to_anchor((0.03, 0.46))
        temperature_legend.set_title("Temperatura media (C)")

    fig.suptitle(
        f"Mapa 3. Clima para teletrabajar: temperatura media anual ({START_YEAR}-{END_YEAR})",
        fontsize=18,
        fontweight="bold",
        y=0.985,
    )
    ax.text(
        0.01,
        0.94,
        "Coropleta con cortes naturales (Jenks). Circulos: desviacion respecto a la media provincial espanola.",
        transform=ax.transAxes,
        fontsize=8.2,
        color="#444444",
        ha="left",
    )
    ax.set_axis_off()

    points = map_data.copy()
    points["point"] = points.geometry.representative_point()
    max_abs_anomaly = points["temperature_anomaly_c"].abs().max()
    for _, row in points.iterrows():
        point = row["point"]
        radius = 18 + 95 * abs(row["temperature_anomaly_c"]) / max_abs_anomaly
        ax.scatter(
            point.x,
            point.y,
            s=radius,
            color=color_for_anomaly(row["temperature_anomaly_c"]),
            alpha=0.62,
            edgecolor="white",
            linewidth=0.45,
            zorder=4,
        )

    label_offsets = {
        "35": (34, -10),
        "38": (-38, 12),
        "52": (0, -12),
        "39": (18, 12),
        "24": (-22, 0),
        "09": (28, -8),
    }

    selected_labels = pd.concat(
        [
            map_data.nlargest(3, "temperature_mean_c"),
            map_data.nsmallest(3, "temperature_mean_c"),
        ]
    ).drop_duplicates("COD_PROVINCIA")
    for _, row in selected_labels.iterrows():
        point = row.geometry.representative_point()
        label = f"{row['province_name']}\n{row['temperature_mean_c']:.1f} C"
        offset = label_offsets.get(row["COD_PROVINCIA"], (0, 0))
        text = ax.annotate(
            label,
            xy=(point.x, point.y),
            xycoords=ax.transData,
            xytext=offset,
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=7,
            color="#111111",
        )
        text.set_path_effects(
            [path_effects.withStroke(linewidth=2.4, foreground="white", alpha=0.95)]
        )

    legend_items = [
        Line2D([0], [0], marker="o", color="w", label="Mas fria que la media", markerfacecolor="#2b6cb0", markersize=8),
        Line2D([0], [0], marker="o", color="w", label="Mas calida que la media", markerfacecolor="#c53030", markersize=8),
    ]
    ax.legend(
        handles=legend_items,
        title="Anomalia termica",
        loc="upper left",
        bbox_to_anchor=(0.78, 0.93),
        frameon=True,
        fontsize=8,
        title_fontsize=9,
    )
    if temperature_legend is not None:
        ax.add_artist(temperature_legend)

    top = map_data.nlargest(7, "climate_comfort_score").sort_values("climate_comfort_score")
    rank_ax.barh(top["province_name"], top["climate_comfort_score"], color="#4c956c")
    rank_ax.set_title("Mejor ajuste a clima templado", fontsize=9.5, fontweight="bold", pad=8)
    rank_ax.set_xlim(0, 100)
    rank_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    rank_ax.tick_params(axis="y", labelsize=7)
    rank_ax.tick_params(axis="x", labelsize=7)
    rank_ax.set_xlabel("Indice 0-100", fontsize=8, labelpad=3)
    for spine in ["top", "right", "left"]:
        rank_ax.spines[spine].set_visible(False)

    hist_ax.hist(
        map_data["temperature_mean_c"],
        bins=10,
        color="#6a994e",
        edgecolor="white",
        alpha=0.86,
    )
    hist_ax.axvline(map_data["temperature_mean_c"].mean(), color="#bc4749", linewidth=1.8)
    hist_ax.set_title("Distribucion provincial", fontsize=9.5, fontweight="bold", pad=8)
    hist_ax.set_xlabel("C", fontsize=8)
    hist_ax.set_ylabel("Provincias", fontsize=8)
    hist_ax.tick_params(labelsize=7)
    hist_ax.grid(axis="y", color="#dddddd", linewidth=0.6)
    hist_ax.legend(
        handles=[Patch(facecolor="#bc4749", label="Media")],
        loc="upper right",
        fontsize=7,
        frameon=False,
    )
    for spine in ["top", "right"]:
        hist_ax.spines[spine].set_visible(False)

    fig.text(
        0.02,
        0.02,
        "Fuente: NASA POWER (T2M mensual) y Eurostat/GISCO NUTS3. Metodos: dissolve, to_crs, representative_point, Jenks y capas superpuestas.",
        fontsize=8,
        color="#555555",
    )
    fig.savefig(OUTPUT_DIR / "mapa3_temperatura_media_anual_provincias.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa3_temperatura_media_anual_provincias.pdf", bbox_inches="tight")
    plt.close(fig)


def save_interactive_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    thresholds = classify_temperatures(map_data["temperature_mean_c"])

    web_map = folium.Map(
        location=[40.1, -3.7],
        zoom_start=6,
        tiles="cartodbpositron",
        control_scale=True,
        max_bounds=True,
    )
    web_map.fit_bounds([[27.3, -18.8], [43.9, 4.7]])
    folium.TileLayer("CartoDB dark_matter", name="Base oscura", control=True).add_to(web_map)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(web_map)

    folium.Choropleth(
        geo_data=map_data.to_json(),
        data=map_data,
        columns=["COD_PROVINCIA", "temperature_mean_c"],
        key_on="feature.properties.COD_PROVINCIA",
        fill_color="Spectral_r",
        fill_opacity=0.76,
        line_opacity=0.45,
        line_weight=0.65,
        bins=thresholds,
        legend_name=f"Temperatura media anual (C), Jenks, {START_YEAR}-{END_YEAR}",
        name="Coropleta temperatura",
    ).add_to(web_map)

    tooltip_fields = [
        "province_name",
        "temperature_mean_c",
        "temperature_anomaly_c",
        "climate_comfort_score",
        "climate_group",
        "area_km2",
        "latitude",
        "longitude",
    ]
    tooltip_aliases = [
        "Provincia",
        "Temperatura media",
        "Anomalia vs media",
        "Indice clima templado",
        "Grupo climatico",
        "Area km2",
        "Latitud punto",
        "Longitud punto",
    ]
    detail_layer = folium.GeoJson(
        map_data,
        name="Detalle provincial",
        style_function=lambda _: {"fillOpacity": 0, "color": "#3b3b3b", "weight": 0.35},
        highlight_function=lambda _: {"weight": 2.2, "color": "#111111", "fillOpacity": 0.08},
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            labels=True,
            sticky=False,
        ),
    ).add_to(web_map)

    popup_html = """
    <div style="font-family:Arial; font-size:13px; line-height:1.35">
      <b>{province}</b><br>
      Temperatura media: <b>{temp:.1f} C</b><br>
      Anomalia provincial: <b>{anomaly:+.1f} C</b><br>
      Indice de clima templado: <b>{comfort:.1f}/100</b><br>
      Periodo: {start}-{end}
    </div>
    """
    anomaly_layer = folium.FeatureGroup(name="Circulos de anomalia termica", show=True)
    for _, row in map_data.iterrows():
        radius = 4 + 7 * abs(row["temperature_anomaly_c"]) / map_data["temperature_anomaly_c"].abs().max()
        popup = popup_html.format(
            province=row["province_name"],
            temp=row["temperature_mean_c"],
            anomaly=row["temperature_anomaly_c"],
            comfort=row["climate_comfort_score"],
            start=START_YEAR,
            end=END_YEAR,
        )
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=radius,
            color="#ffffff",
            weight=0.8,
            fill=True,
            fill_color=color_for_anomaly(row["temperature_anomaly_c"]),
            fill_opacity=0.78,
            tooltip=f"{row['province_name']}: {row['temperature_anomaly_c']:+.1f} C",
            popup=folium.Popup(popup, max_width=280),
        ).add_to(anomaly_layer)
    anomaly_layer.add_to(web_map)

    label_layer = folium.FeatureGroup(name="Top provincias calidas y frias", show=False)
    extremes = pd.concat(
        [map_data.nlargest(5, "temperature_mean_c"), map_data.nsmallest(5, "temperature_mean_c")]
    ).drop_duplicates("COD_PROVINCIA")
    for _, row in extremes.iterrows():
        icon_color = "red" if row["temperature_anomaly_c"] >= 0 else "blue"
        icon_name = "fire" if row["temperature_anomaly_c"] >= 0 else "asterisk"
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            icon=folium.Icon(color=icon_color, icon=icon_name),
            tooltip=f"{row['province_name']} ({row['temperature_mean_c']:.1f} C)",
        ).add_to(label_layer)
    label_layer.add_to(web_map)

    web_map.add_child(folium.LatLngPopup())
    plugins.MiniMap(toggle_display=True, minimized=True).add_to(web_map)
    plugins.Fullscreen(position="topright").add_to(web_map)
    plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(web_map)
    plugins.Draw(export=True, position="topleft").add_to(web_map)
    plugins.Search(
        layer=detail_layer,
        geom_type="Polygon",
        placeholder="Buscar provincia",
        collapsed=True,
        search_label="province_name",
        position="topleft",
    ).add_to(web_map)
    folium.LayerControl(collapsed=False).add_to(web_map)
    web_map.save(OUTPUT_DIR / "mapa3_temperatura_media_anual_provincias_interactivo.html")


def save_tables(map_data: gpd.GeoDataFrame) -> None:
    columns = [
        "COD_PROVINCIA",
        "province_name",
        "temperature_mean_c",
        "temperature_anomaly_c",
        "climate_group",
        "climate_comfort_score",
        "area_km2",
        "latitude",
        "longitude",
        "start_year",
        "end_year",
    ]
    table = map_data[columns].sort_values("temperature_mean_c", ascending=False).copy()
    table.to_csv(OUTPUT_DIR / "mapa3_temperatura_media_anual_provincias_datos.csv", index=False)


def main() -> None:
    map_data = build_dataset()
    save_static_map(map_data)
    save_interactive_map(map_data)
    save_tables(map_data)

    print(f"Mapa 3 generado con temperatura media anual {START_YEAR}-{END_YEAR}.")
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
