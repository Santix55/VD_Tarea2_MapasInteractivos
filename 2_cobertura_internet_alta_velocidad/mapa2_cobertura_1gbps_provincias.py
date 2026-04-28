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
import geopandas as gpd
import mapclassify
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
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
COVERAGE_COLUMN = "Cob. 1Gbps descarga condiciones máxima demanda\n(junio 2024)"
PREVIOUS_COVERAGE_COLUMN = "Cob. 1Gbps descarga condiciones máxima demanda\n(junio 2023)"

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

PROVINCE_CODE_BY_NAME = {
    "araba/alava": "01",
    "albacete": "02",
    "alicante/alacant": "03",
    "almeria": "04",
    "avila": "05",
    "badajoz": "06",
    "balears, illes": "07",
    "barcelona": "08",
    "burgos": "09",
    "caceres": "10",
    "cadiz": "11",
    "castellon/castello": "12",
    "ciudad real": "13",
    "cordoba": "14",
    "coruna, a": "15",
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
    "lugo": "27",
    "madrid": "28",
    "malaga": "29",
    "murcia": "30",
    "navarra": "31",
    "ourense": "32",
    "asturias": "33",
    "palencia": "34",
    "palmas, las": "35",
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


def load_broadband_by_province() -> pd.DataFrame:
    broadband = pd.read_excel(BROADBAND_FILE, sheet_name=SHEET_NAME)
    broadband["COD_PROVINCIA"] = broadband["Provincia"].map(
        lambda value: PROVINCE_CODE_BY_NAME.get(normalize_text(value))
    )

    missing_codes = broadband[broadband["COD_PROVINCIA"].isna()]["Provincia"].tolist()
    if missing_codes:
        raise ValueError(f"No se pudo asignar código INE a estas provincias: {missing_codes}")

    summary = broadband[
        [
            "COD_PROVINCIA",
            "Comunidad Autónoma",
            "Provincia",
            "Habitantes",
            "Hogares",
            PREVIOUS_COVERAGE_COLUMN,
            COVERAGE_COLUMN,
        ]
    ].rename(
        columns={
            "Comunidad Autónoma": "ccaa",
            "Provincia": "province_name",
            "Habitantes": "population",
            "Hogares": "households",
            PREVIOUS_COVERAGE_COLUMN: "coverage_1gbps_2023_pct",
            COVERAGE_COLUMN: "coverage_1gbps_pct",
        }
    )
    summary["coverage_1gbps_pct"] = pd.to_numeric(summary["coverage_1gbps_pct"]) * 100
    summary["coverage_1gbps_2023_pct"] = pd.to_numeric(summary["coverage_1gbps_2023_pct"]) * 100
    summary["coverage_change_pp"] = (
        summary["coverage_1gbps_pct"] - summary["coverage_1gbps_2023_pct"]
    )

    return summary


def load_province_geometries() -> gpd.GeoDataFrame:
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])

    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    provinces = provinces[["COD_PROVINCIA", "geometry"]].copy()
    return provinces.to_crs("EPSG:4326")


def build_dataset() -> gpd.GeoDataFrame:
    download_file(BROADBAND_URL, BROADBAND_FILE)
    download_file(NUTS_URL, NUTS_FILE)

    coverage = load_broadband_by_province()
    provinces = load_province_geometries()
    map_data = provinces.merge(coverage, on="COD_PROVINCIA", how="left")

    missing = map_data[map_data["coverage_1gbps_pct"].isna()]
    if not missing.empty:
        missing_codes = ", ".join(missing["COD_PROVINCIA"].tolist())
        raise ValueError(f"Faltan datos de cobertura para estas provincias: {missing_codes}")

    return map_data


def save_static_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 9), dpi=180)
    map_data.plot(
        column="coverage_1gbps_pct",
        ax=ax,
        cmap="YlGnBu",
        scheme="Quantiles",
        k=5,
        linewidth=0.45,
        edgecolor="#ffffff",
        legend=True,
        legend_kwds={
            "title": "Cobertura hogares (%)",
            "loc": "lower left",
            "frameon": True,
            "fmt": "{:.1f}",
        },
    )

    ax.set_title(
        "Cobertura provincial de banda ancha fija >= 1 Gbps (2024)",
        fontsize=18,
        fontweight="bold",
        pad=16,
    )
    ax.text(
        0.01,
        0.93,
        "Cobertura sobre hogares, junio 2024.\nFuente: SETELECO/MTDFP y Eurostat/GISCO.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#444444",
        ha="left",
    )
    ax.set_axis_off()

    # En este mapa interesan especialmente los territorios con menor cobertura.
    low_coverage = map_data.nsmallest(5, "coverage_1gbps_pct")
    for _, row in low_coverage.iterrows():
        point = row.geometry.representative_point()
        label = f"{row['province_name']}\n{row['coverage_1gbps_pct']:.1f}%"
        text = ax.annotate(
            label,
            xy=(point.x, point.y),
            xycoords=ax.transData,
            ha="center",
            va="center",
            fontsize=7,
            color="#111111",
        )
        text.set_path_effects(
            [path_effects.withStroke(linewidth=2.4, foreground="white", alpha=0.95)]
        )

    fig.savefig(OUTPUT_DIR / "mapa2_cobertura_1gbps_provincias.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa2_cobertura_1gbps_provincias.pdf", bbox_inches="tight")
    plt.close(fig)


def save_interactive_map(map_data: gpd.GeoDataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    classifier = mapclassify.Quantiles(map_data["coverage_1gbps_pct"], k=5)
    thresholds = [float(map_data["coverage_1gbps_pct"].min())] + [
        float(value) for value in classifier.bins
    ]
    thresholds[0] = max(0, thresholds[0] - 0.1)

    web_map = folium.Map(location=[40.1, -3.7], zoom_start=6, tiles="cartodbpositron")
    folium.Choropleth(
        geo_data=map_data.to_json(),
        data=map_data,
        columns=["COD_PROVINCIA", "coverage_1gbps_pct"],
        key_on="feature.properties.COD_PROVINCIA",
        fill_color="YlGnBu",
        fill_opacity=0.82,
        line_opacity=0.55,
        line_weight=0.7,
        bins=thresholds,
        legend_name="Cobertura de banda ancha fija >= 1 Gbps (% hogares), 2024",
    ).add_to(web_map)

    tooltip_fields = [
        "province_name",
        "ccaa",
        "coverage_1gbps_pct",
        "coverage_change_pp",
        "households",
        "population",
    ]
    tooltip_aliases = [
        "Provincia",
        "CCAA",
        "Cobertura 2024",
        "Cambio 2023-2024 (pp)",
        "Hogares",
        "Habitantes",
    ]
    folium.GeoJson(
        map_data,
        name="Detalle provincial",
        style_function=lambda _: {"fillOpacity": 0, "color": "#333333", "weight": 0.25},
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            labels=True,
            sticky=False,
        ),
    ).add_to(web_map)
    folium.LayerControl(collapsed=True).add_to(web_map)
    web_map.save(OUTPUT_DIR / "mapa2_cobertura_1gbps_provincias_interactivo.html")


def save_tables(map_data: gpd.GeoDataFrame) -> None:
    columns = [
        "COD_PROVINCIA",
        "province_name",
        "ccaa",
        "population",
        "households",
        "coverage_1gbps_2023_pct",
        "coverage_1gbps_pct",
        "coverage_change_pp",
    ]
    table = map_data[columns].sort_values("coverage_1gbps_pct", ascending=False).copy()
    table["year"] = 2024
    table.to_csv(OUTPUT_DIR / "mapa2_cobertura_1gbps_provincias_datos.csv", index=False)


def main() -> None:
    map_data = build_dataset()
    save_static_map(map_data)
    save_interactive_map(map_data)
    save_tables(map_data)

    print("Mapa 2 generado con datos de cobertura de junio de 2024.")
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
