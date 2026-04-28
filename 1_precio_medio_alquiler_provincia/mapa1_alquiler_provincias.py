from pathlib import Path

import folium
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

RENT_FILE = DATA_DIR / "mivau_alquiler_municipios.csv"
NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"

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
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    target.write_bytes(response.content)


def load_rent_by_province(year: int | None = None) -> tuple[pd.DataFrame, int]:
    rent = pd.read_csv(
        RENT_FILE,
        sep=";",
        encoding="utf-8-sig",
        dtype={"COD_PROVINCIA": str, "COD_POSTAL": str},
    )
    rent["AÑO"] = rent["AÑO"].astype(int)
    rent["VALOR"] = pd.to_numeric(rent["VALOR"].astype(str).str.replace(",", "."), errors="coerce")

    selected_year = int(rent["AÑO"].max() if year is None else year)
    current = rent[rent["AÑO"].eq(selected_year)].copy()

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
    ].rename(columns={"VALOR": "rent_homes"})

    # El precio municipal mediano se pondera por el recuento de viviendas de alquiler.
    merged = price.merge(
        weights,
        on=["COD_PROVINCIA", "COD_POSTAL", "NOMBRE_MUNICIPIO", "TIPO_VIVIENDA"],
        how="left",
    ).dropna(subset=["median_rent_eur", "rent_homes"])
    merged = merged[merged["rent_homes"].gt(0)]
    merged["weighted_price"] = merged["median_rent_eur"] * merged["rent_homes"]

    summary = (
        merged.groupby(["COD_PROVINCIA", "PROVINCIA"], as_index=False)
        .agg(
            total_weighted_price=("weighted_price", "sum"),
            rental_homes=("rent_homes", "sum"),
            municipalities=("COD_POSTAL", "nunique"),
        )
    )
    summary["rent_eur_month"] = summary["total_weighted_price"] / summary["rental_homes"]

    return summary.drop(columns=["total_weighted_price"]), selected_year


def load_province_geometries() -> gpd.GeoDataFrame:
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])

    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    provinces = provinces[["COD_PROVINCIA", "geometry"]].copy()
    return provinces.to_crs("EPSG:4326")


def build_dataset(year: int | None = None) -> tuple[gpd.GeoDataFrame, int]:
    download_file(MIVAU_URL, RENT_FILE)
    download_file(NUTS_URL, NUTS_FILE)

    rent, selected_year = load_rent_by_province(year)
    provinces = load_province_geometries()
    map_data = provinces.merge(rent, on="COD_PROVINCIA", how="left")

    missing = map_data[map_data["rent_eur_month"].isna()]
    if not missing.empty:
        missing_codes = ", ".join(missing["COD_PROVINCIA"].tolist())
        raise ValueError(f"Faltan datos de alquiler para estas provincias: {missing_codes}")

    return map_data, selected_year


def save_static_map(map_data: gpd.GeoDataFrame, year: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 9), dpi=180)
    map_data.plot(
        column="rent_eur_month",
        ax=ax,
        cmap="YlOrRd",
        scheme="Quantiles",
        k=5,
        linewidth=0.45,
        edgecolor="#ffffff",
        legend=True,
        legend_kwds={
            "title": "Alquiler mensual (€)",
            "loc": "lower left",
            "frameon": True,
            "fmt": "{:.0f}",
        },
    )

    ax.set_title(
        f"Precio medio de alquiler por provincia ({year})",
        fontsize=18,
        fontweight="bold",
        pad=16,
    )
    ax.text(
        0.01,
        0.02,
        "Media ponderada del precio municipal mediano. Fuente: MIVAU y Eurostat/GISCO.",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#444444",
    )
    ax.set_axis_off()

    top_provinces = map_data.nlargest(5, "rent_eur_month")
    for _, row in top_provinces.iterrows():
        point = row.geometry.representative_point()
        label = f"{row['PROVINCIA']}\n{row['rent_eur_month']:.0f} €"
        text = ax.annotate(
            label,
            xy=(point.x, point.y),
            xycoords=ax.transData,
            ha="center",
            va="center",
            fontsize=7,
            color="#1b1b1b",
        )
        text.set_path_effects(
            [path_effects.withStroke(linewidth=2.4, foreground="white", alpha=0.95)]
        )

    fig.savefig(OUTPUT_DIR / "mapa1_alquiler_provincias.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa1_alquiler_provincias.pdf", bbox_inches="tight")
    plt.close(fig)


def save_interactive_map(map_data: gpd.GeoDataFrame, year: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    classifier = mapclassify.Quantiles(map_data["rent_eur_month"], k=5)
    thresholds = [float(map_data["rent_eur_month"].min())] + [float(value) for value in classifier.bins]
    thresholds[0] = max(0, thresholds[0] - 1)

    web_map = folium.Map(location=[40.1, -3.7], zoom_start=6, tiles="cartodbpositron")
    folium.Choropleth(
        geo_data=map_data.to_json(),
        data=map_data,
        columns=["COD_PROVINCIA", "rent_eur_month"],
        key_on="feature.properties.COD_PROVINCIA",
        fill_color="YlOrRd",
        fill_opacity=0.82,
        line_opacity=0.55,
        line_weight=0.7,
        bins=thresholds,
        legend_name=f"Precio medio de alquiler mensual (€), {year}",
    ).add_to(web_map)

    tooltip_fields = ["PROVINCIA", "rent_eur_month", "rental_homes", "municipalities"]
    tooltip_aliases = ["Provincia", "Alquiler medio", "Viviendas ponderadas", "Municipios"]
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
    web_map.save(OUTPUT_DIR / "mapa1_alquiler_provincias_interactivo.html")


def save_tables(map_data: gpd.GeoDataFrame, year: int) -> None:
    columns = ["COD_PROVINCIA", "PROVINCIA", "rent_eur_month", "rental_homes", "municipalities"]
    table = map_data[columns].sort_values("rent_eur_month", ascending=False).copy()
    table["year"] = year
    table.to_csv(OUTPUT_DIR / "mapa1_alquiler_provincias_datos.csv", index=False)


def main() -> None:
    map_data, year = build_dataset()
    save_static_map(map_data, year)
    save_interactive_map(map_data, year)
    save_tables(map_data, year)

    print(f"Mapa 1 generado con datos de {year}.")
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
