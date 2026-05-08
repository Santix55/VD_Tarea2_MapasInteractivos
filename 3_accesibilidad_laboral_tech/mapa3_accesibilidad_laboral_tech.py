from __future__ import annotations

from pathlib import Path
import html
import math
import os
import sys


BASE_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR / ".matplotlib"))

proj_data = Path(sys.prefix) / "share" / "proj"
if proj_data.exists():
    os.environ.setdefault("PROJ_DATA", str(proj_data))
    os.environ.setdefault("PROJ_LIB", str(proj_data))

import folium
from folium import plugins
import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import LineString, Point


DATA_DIR = BASE_DIR / "datos"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"

RENT_FILE = DATA_DIR / "mivau_alquiler_municipios.csv"
NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"
PROJECTED_CRS = "EPSG:3035"

PRICE_MEASURES = {"MEDIANA": "median_rent_eur"}
DISTANCE_BINS = [0, 50, 100, 175, 250, math.inf]
DISTANCE_LABELS = [
    "0-50 km - area inmediata",
    "50-100 km - muy accesible",
    "100-175 km - accesible",
    "175-250 km - periferica",
    ">250 km - alejada",
]
DISTANCE_COLORS = {
    1: "#1a9850",
    2: "#91cf60",
    3: "#fee08b",
    4: "#fc8d59",
    5: "#d73027",
}
HUB_COLORS = {
    "valencia_upv": "#0072B2",
    "madrid": "#D55E00",
    "barcelona": "#009E73",
    "malaga": "#CC79A7",
    "bilbao": "#56B4E9",
    "sevilla": "#E69F00",
    "zaragoza": "#7F3C8D",
}
BUFFER_RADII_KM = [50, 100, 175, 250]
BUFFER_LINEWIDTHS = {
    50: 0.55,
    100: 0.7,
    175: 0.85,
    250: 1.0,
}
BUFFER_LINESTYLES = {
    50: ":",
    100: "--",
    175: "-.",
    250: "-",
}
BUFFER_OPACITIES = {
    50: 0.52,
    100: 0.6,
    175: 0.68,
    250: 0.76,
}
BUFFER_DASH_ARRAYS = {
    50: "2 5",
    100: "5 5",
    175: "8 5",
    250: "",
}

HUBS = [
    {
        "hub_id": "valencia_upv",
        "hub_name": "UPV/Valencia",
        "province_code": "46",
        "latitude": 39.4811,
        "longitude": -0.3407,
        "note": "Nodo de referencia del Master de IA en la UPV.",
    },
    {
        "hub_id": "madrid",
        "hub_name": "Madrid",
        "province_code": "28",
        "latitude": 40.4168,
        "longitude": -3.7038,
        "note": "Gran mercado nacional de empleo tecnologico.",
    },
    {
        "hub_id": "barcelona",
        "hub_name": "Barcelona",
        "province_code": "08",
        "latitude": 41.3874,
        "longitude": 2.1686,
        "note": "Ecosistema tecnologico y universitario consolidado.",
    },
    {
        "hub_id": "malaga",
        "hub_name": "Malaga",
        "province_code": "29",
        "latitude": 36.7213,
        "longitude": -4.4214,
        "note": "Polo tecnologico relevante en el sur.",
    },
    {
        "hub_id": "bilbao",
        "hub_name": "Bilbao",
        "province_code": "48",
        "latitude": 43.2630,
        "longitude": -2.9350,
        "note": "Nodo tecnologico e industrial del norte.",
    },
    {
        "hub_id": "sevilla",
        "hub_name": "Sevilla",
        "province_code": "41",
        "latitude": 37.3891,
        "longitude": -5.9845,
        "note": "Nodo urbano y universitario del suroeste.",
    },
    {
        "hub_id": "zaragoza",
        "hub_name": "Zaragoza",
        "province_code": "50",
        "latitude": 41.6488,
        "longitude": -0.8891,
        "note": "Nodo intermedio entre Madrid, Barcelona y el arco mediterraneo.",
    },
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


def require_file(path: Path, description: str) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise FileNotFoundError(
            f"No se encontro {description}: {path}. Ejecuta antes los mapas que cachean "
            "los datos base o descarga el fichero en datos/."
        )


def clean_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def format_int(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):,.0f}".replace(",", ".")


def format_eur(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):,.0f} EUR".replace(",", ".")


def format_km(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):,.0f} km".replace(",", ".")


def distance_comment(rank: int) -> str:
    comments = {
        1: "Cercania directa al ecosistema tech de referencia.",
        2: "Distancia asumible para visitas frecuentes o movilidad puntual.",
        3: "Accesible, pero conviene valorar transporte real.",
        4: "Posicion periferica respecto a los hubs seleccionados.",
        5: "Alta distancia: mejor entenderlo como destino remoto.",
    }
    return comments[int(rank)]


def load_hubs() -> gpd.GeoDataFrame:
    hubs = pd.DataFrame(HUBS)
    hubs["hub_color"] = hubs["hub_id"].map(HUB_COLORS)
    if hubs["hub_color"].isna().any():
        missing = ", ".join(hubs.loc[hubs["hub_color"].isna(), "hub_id"])
        raise ValueError(f"Faltan colores para estos hubs: {missing}")
    geometry = [Point(lon, lat) for lon, lat in zip(hubs["longitude"], hubs["latitude"])]
    return gpd.GeoDataFrame(hubs, geometry=geometry, crs="EPSG:4326")


def load_province_geometries() -> gpd.GeoDataFrame:
    require_file(NUTS_FILE, "cartografia NUTS3 2024")
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])

    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    provinces = provinces[["COD_PROVINCIA", "geometry"]].copy()
    return provinces.to_crs("EPSG:4326")


def read_mivau(year: int | None = None) -> tuple[pd.DataFrame, int]:
    require_file(RENT_FILE, "CSV municipal de MIVAU")
    rent = pd.read_csv(
        RENT_FILE,
        sep=";",
        encoding="utf-8-sig",
        dtype={"COD_PROVINCIA": str, "COD_POSTAL": str},
    )
    rent["COD_PROVINCIA"] = rent["COD_PROVINCIA"].str.zfill(2)
    rent["COD_POSTAL"] = rent["COD_POSTAL"].str.zfill(5)
    rent["AÑO"] = rent["AÑO"].astype(int)
    rent["VALOR"] = clean_numeric(rent["VALOR"])

    selected_year = int(rent["AÑO"].max() if year is None else year)
    return rent[rent["AÑO"].eq(selected_year)].copy(), selected_year


def load_province_rent(year: int | None = None) -> tuple[pd.DataFrame, int]:
    current, selected_year = read_mivau(year)
    keys = ["COD_PROVINCIA", "PROVINCIA", "COD_POSTAL", "NOMBRE_MUNICIPIO", "TIPO_VIVIENDA"]

    prices = current[
        current["ELEMENTO"].eq("PRECIO") & current["TIPO_MEDIDA"].isin(PRICE_MEASURES)
    ].pivot_table(
        index=keys,
        columns="TIPO_MEDIDA",
        values="VALOR",
        aggfunc="first",
    )
    prices = prices.rename(columns=PRICE_MEASURES).reset_index()

    weights = current[
        current["ELEMENTO"].eq("VIVIENDA") & current["TIPO_MEDIDA"].eq("RECUENTO")
    ][keys + ["VALOR"]].rename(columns={"VALOR": "rent_homes"})

    by_type = prices.merge(weights, on=keys, how="left")
    by_type = by_type.dropna(subset=["median_rent_eur", "rent_homes"])
    by_type = by_type[by_type["rent_homes"].gt(0)].copy()
    by_type["weighted_price"] = by_type["median_rent_eur"] * by_type["rent_homes"]

    municipal = (
        by_type.groupby(["COD_PROVINCIA", "PROVINCIA", "COD_POSTAL"], as_index=False)
        .agg(
            weighted_price=("weighted_price", "sum"),
            rental_homes=("rent_homes", "sum"),
        )
    )
    municipal["median_rent_eur"] = municipal["weighted_price"] / municipal["rental_homes"]
    municipal["weighted_price"] = municipal["median_rent_eur"] * municipal["rental_homes"]

    province = (
        municipal.groupby(["COD_PROVINCIA", "PROVINCIA"], as_index=False)
        .agg(
            total_weighted_price=("weighted_price", "sum"),
            rental_homes=("rental_homes", "sum"),
            municipalities=("COD_POSTAL", "nunique"),
        )
    )
    province["rent_eur_month"] = province["total_weighted_price"] / province["rental_homes"]
    return province.drop(columns=["total_weighted_price"]), selected_year


def classify_distance(distance_km: pd.Series) -> tuple[pd.Series, pd.Series]:
    ranks = pd.cut(
        distance_km,
        bins=DISTANCE_BINS,
        labels=[1, 2, 3, 4, 5],
        include_lowest=True,
    ).astype(int)
    labels = ranks.map({index + 1: label for index, label in enumerate(DISTANCE_LABELS)})
    return ranks, labels


def assign_nearest_hubs(
    map_data: gpd.GeoDataFrame,
    hubs: gpd.GeoDataFrame,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    projected = map_data.to_crs(PROJECTED_CRS)
    province_points = projected[["COD_PROVINCIA"]].copy()
    province_points["geometry"] = projected.geometry.representative_point()
    province_points = gpd.GeoDataFrame(province_points, geometry="geometry", crs=PROJECTED_CRS)
    hubs_projected = hubs.to_crs(PROJECTED_CRS)

    nearest = gpd.sjoin_nearest(
        province_points,
        hubs_projected[["hub_id", "hub_name", "geometry"]],
        how="left",
        distance_col="nearest_hub_m",
    )
    nearest = nearest.rename(
        columns={
            "hub_id": "nearest_hub_id",
            "hub_name": "nearest_hub",
        }
    )
    nearest["nearest_hub_km"] = nearest["nearest_hub_m"] / 1000

    point_wgs84 = province_points.to_crs("EPSG:4326")
    coords = pd.DataFrame(
        {
            "COD_PROVINCIA": point_wgs84["COD_PROVINCIA"].values,
            "province_point_lon": point_wgs84.geometry.x.values,
            "province_point_lat": point_wgs84.geometry.y.values,
        }
    )

    assigned = map_data.merge(
        nearest[
            [
                "COD_PROVINCIA",
                "nearest_hub_id",
                "nearest_hub",
                "nearest_hub_km",
            ]
        ],
        on="COD_PROVINCIA",
        how="left",
    ).merge(coords, on="COD_PROVINCIA", how="left")
    assigned["distance_rank"], assigned["distance_class"] = classify_distance(
        assigned["nearest_hub_km"]
    )
    assigned["distance_color"] = assigned["distance_rank"].map(DISTANCE_COLORS)
    assigned["distance_comment"] = assigned["distance_rank"].map(distance_comment)
    assigned["nearest_hub_km_label"] = assigned["nearest_hub_km"].map(format_km)
    assigned["rent_label"] = assigned["rent_eur_month"].map(format_eur)
    assigned["rental_homes_label"] = assigned["rental_homes"].map(format_int)

    hub_points = hubs_projected.set_index("hub_id").geometry.to_dict()
    province_point_map = province_points.set_index("COD_PROVINCIA").geometry.to_dict()
    line_records = []
    for _, row in assigned.iterrows():
        province_point = province_point_map[row["COD_PROVINCIA"]]
        hub_point = hub_points[row["nearest_hub_id"]]
        line_records.append(
            {
                "COD_PROVINCIA": row["COD_PROVINCIA"],
                "PROVINCIA": row["PROVINCIA"],
                "nearest_hub_id": row["nearest_hub_id"],
                "nearest_hub": row["nearest_hub"],
                "nearest_hub_km": row["nearest_hub_km"],
                "nearest_hub_km_label": row["nearest_hub_km_label"],
                "distance_class": row["distance_class"],
                "line_color": HUB_COLORS[row["nearest_hub_id"]],
                "geometry": LineString([province_point, hub_point]),
            }
        )
    lines = gpd.GeoDataFrame(line_records, geometry="geometry", crs=PROJECTED_CRS).to_crs(
        "EPSG:4326"
    )

    return assigned, lines


def make_buffers(provinces: gpd.GeoDataFrame, hubs: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    hubs_projected = hubs.to_crs(PROJECTED_CRS)
    provinces_projected = provinces.to_crs(PROJECTED_CRS)
    spain_mask = gpd.GeoDataFrame(
        geometry=[provinces_projected.geometry.union_all()],
        crs=PROJECTED_CRS,
    )

    buffer_layers = []
    for radius in BUFFER_RADII_KM:
        layer = hubs_projected.copy()
        layer["radius_km"] = radius
        layer["radius_label"] = f"{radius} km"
        layer["geometry"] = layer.geometry.buffer(radius * 1000)
        layer = gpd.clip(layer, spain_mask)
        layer = layer[~layer.geometry.is_empty].copy()
        buffer_layers.append(layer)

    return pd.concat(buffer_layers, ignore_index=True).pipe(
        lambda frame: gpd.GeoDataFrame(frame, geometry="geometry", crs=PROJECTED_CRS)
    ).to_crs("EPSG:4326")


def build_dataset() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, int]:
    provinces = load_province_geometries()
    rent, year = load_province_rent()
    hubs = load_hubs()

    map_data = provinces.merge(rent, on="COD_PROVINCIA", how="left")
    missing = map_data[map_data["rent_eur_month"].isna()]
    if not missing.empty:
        missing_codes = ", ".join(missing["COD_PROVINCIA"].tolist())
        raise ValueError(f"Faltan datos de alquiler para estas provincias: {missing_codes}")

    map_data, lines = assign_nearest_hubs(map_data, hubs)
    buffers = make_buffers(provinces, hubs)
    validate_dataset(map_data)
    return map_data, hubs, buffers, lines, year


def validate_dataset(map_data: gpd.GeoDataFrame) -> None:
    if len(map_data) != 52:
        raise ValueError(f"Se esperaban 52 provincias y se obtuvieron {len(map_data)}.")
    if map_data["nearest_hub"].isna().any():
        missing = ", ".join(map_data.loc[map_data["nearest_hub"].isna(), "COD_PROVINCIA"])
        raise ValueError(f"Hay provincias sin hub cercano: {missing}")
    if map_data["distance_rank"].nunique() != 5:
        raise ValueError("La clasificacion de distancia no contiene exactamente 5 clases.")

    hub_code_map = {hub["province_code"]: hub["hub_name"] for hub in HUBS}
    hub_provinces = map_data[map_data["COD_PROVINCIA"].isin(hub_code_map)]
    outside_immediate = hub_provinces[hub_provinces["distance_rank"].ne(1)]
    if not outside_immediate.empty:
        names = ", ".join(outside_immediate["PROVINCIA"].tolist())
        raise ValueError(f"Las provincias hub no caen en la clase 0-50 km: {names}")


def distance_legend_handles() -> list[mpatches.Patch]:
    return [
        mpatches.Patch(color=DISTANCE_COLORS[index + 1], label=label)
        for index, label in enumerate(DISTANCE_LABELS)
    ]


def plot_canary_inset(
    map_ax: plt.Axes,
    map_data: gpd.GeoDataFrame,
    buffers: gpd.GeoDataFrame,
) -> None:
    canary_ax = map_ax.inset_axes([0.035, 0.055, 0.21, 0.21])
    canary_codes = ["35", "38"]
    canary_map = map_data[map_data["COD_PROVINCIA"].isin(canary_codes)]
    canary_map.plot(
        ax=canary_ax,
        color=canary_map["distance_color"],
        linewidth=0.45,
        edgecolor="#ffffff",
    )
    canary_buffers = buffers[buffers.intersects(canary_map.union_all())]
    if not canary_buffers.empty:
        canary_buffers.boundary.plot(ax=canary_ax, color="#555555", linewidth=0.5, alpha=0.5)
    for _, row in canary_map.iterrows():
        point = row.geometry.representative_point()
        text = canary_ax.annotate(
            row["nearest_hub_km_label"],
            xy=(point.x, point.y),
            ha="center",
            va="center",
            fontsize=6.8,
            color="#111111",
        )
        text.set_path_effects([path_effects.withStroke(linewidth=2.2, foreground="white")])
    canary_ax.set_xlim(-18.4, -13.1)
    canary_ax.set_ylim(27.55, 29.65)
    canary_ax.set_title("Canarias", fontsize=8.2, pad=2)
    canary_ax.set_xticks([])
    canary_ax.set_yticks([])
    for spine in canary_ax.spines.values():
        spine.set_edgecolor("#8c8c8c")
        spine.set_linewidth(0.8)


def save_static_map(
    map_data: gpd.GeoDataFrame,
    hubs: gpd.GeoDataFrame,
    buffers: gpd.GeoDataFrame,
    lines: gpd.GeoDataFrame,
    year: int,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(16, 9.8), dpi=180)
    grid = fig.add_gridspec(nrows=2, ncols=3, width_ratios=[1.25, 1.25, 1.05], wspace=0.22)
    map_ax = fig.add_subplot(grid[:, :2])
    scatter_ax = fig.add_subplot(grid[0, 2])
    hub_ax = fig.add_subplot(grid[1, 2])

    map_data.plot(
        ax=map_ax,
        color=map_data["distance_color"],
        linewidth=0.55,
        edgecolor="#ffffff",
        zorder=1,
    )

    for radius in BUFFER_RADII_KM:
        subset = buffers[buffers["radius_km"].eq(radius)]
        if subset.empty:
            continue
        subset.boundary.plot(
            ax=map_ax,
            color=subset["hub_color"].tolist(),
            linewidth=BUFFER_LINEWIDTHS[radius],
            linestyle=BUFFER_LINESTYLES[radius],
            alpha=BUFFER_OPACITIES[radius],
            zorder=2,
        )

    mainland_lines = lines[~lines["COD_PROVINCIA"].isin(["35", "38"])].copy()
    for _, hub_lines in mainland_lines.groupby("nearest_hub_id", sort=False):
        hub_lines.plot(
            ax=map_ax,
            color=hub_lines["line_color"].iloc[0],
            linewidth=0.55,
            alpha=0.33,
            zorder=3,
        )
    hubs.plot(
        ax=map_ax,
        marker="*",
        color=hubs["hub_color"].tolist(),
        edgecolor="#ffffff",
        linewidth=0.7,
        markersize=145,
        zorder=4,
    )

    for _, row in hubs.iterrows():
        text = map_ax.annotate(
            row["hub_name"],
            xy=(row.geometry.x, row.geometry.y),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=7.7,
            color="#111111",
            fontweight="bold",
            zorder=5,
        )
        text.set_path_effects([path_effects.withStroke(linewidth=2.6, foreground="white")])

    for _, row in map_data[map_data["distance_rank"].eq(5)].iterrows():
        point = row.geometry.representative_point()
        text = map_ax.annotate(
            row["nearest_hub_km_label"],
            xy=(point.x, point.y),
            ha="center",
            va="center",
            fontsize=7.2,
            color="#111111",
            zorder=5,
        )
        text.set_path_effects([path_effects.withStroke(linewidth=2.4, foreground="white")])

    map_ax.set_xlim(-10.2, 5.0)
    map_ax.set_ylim(35.0, 44.5)
    map_ax.set_axis_off()
    map_ax.set_title(
        "Accesibilidad laboral tech: distancia al hub IA/tech mas cercano",
        fontsize=16.5,
        fontweight="bold",
        pad=12,
    )
    map_ax.legend(
        handles=distance_legend_handles(),
        title="Distancia euclidea",
        loc="upper left",
        frameon=True,
        fontsize=8.2,
        title_fontsize=9.2,
    )
    plot_canary_inset(map_ax, map_data, buffers)

    for rank in range(1, 6):
        subset = map_data[map_data["distance_rank"].eq(rank)]
        scatter_ax.scatter(
            subset["nearest_hub_km"],
            subset["rent_eur_month"],
            s=36 + subset["rental_homes"].apply(lambda value: math.log1p(value) * 4.5),
            color=DISTANCE_COLORS[rank],
            edgecolor="#222222",
            linewidth=0.35,
            alpha=0.82,
            label=DISTANCE_LABELS[rank - 1].split(" - ")[0],
        )
    for threshold in DISTANCE_BINS[1:-1]:
        scatter_ax.axvline(threshold, color="#c7c7c7", linewidth=0.7, linestyle="--")
    national_rent = (map_data["rent_eur_month"] * map_data["rental_homes"]).sum() / map_data[
        "rental_homes"
    ].sum()
    scatter_ax.axhline(national_rent, color="#111111", linewidth=1.0, linestyle=":")
    scatter_ax.text(
        8,
        national_rent + 8,
        f"media ponderada {national_rent:.0f} EUR",
        fontsize=7.6,
        color="#111111",
    )
    label_codes = ["46", "28", "08", "29", "48", "41", "50", "35", "38"]
    for _, row in map_data[map_data["COD_PROVINCIA"].isin(label_codes)].iterrows():
        label = row["PROVINCIA"].replace("Valencia/Valencia", "Valencia").replace(
            "Balears, Illes", "Balears"
        )
        scatter_ax.annotate(
            label,
            (row["nearest_hub_km"], row["rent_eur_month"]),
            xytext=(4, 3),
            textcoords="offset points",
            fontsize=7.0,
            color="#111111",
        )
    scatter_ax.set_title("Distancia al trabajo tech vs alquiler", fontsize=11.2, fontweight="bold")
    scatter_ax.set_xlabel("Km al hub mas cercano", fontsize=8.8)
    scatter_ax.set_ylabel(f"Alquiler medio ponderado {year} (EUR/mes)", fontsize=8.8)
    scatter_ax.grid(color="#dddddd", linewidth=0.6)
    scatter_ax.tick_params(axis="both", labelsize=7.8)

    hub_summary = (
        map_data.groupby("nearest_hub", as_index=False)
        .agg(
            provinces=("COD_PROVINCIA", "count"),
            mean_distance=("nearest_hub_km", "mean"),
        )
        .sort_values("provinces")
    )
    hub_ax.barh(hub_summary["nearest_hub"], hub_summary["provinces"], color="#5ab4ac")
    for index, row in hub_summary.reset_index(drop=True).iterrows():
        hub_ax.text(
            row["provinces"] + 0.12,
            index,
            f"{row['provinces']:.0f} prov. | {row['mean_distance']:.0f} km",
            va="center",
            fontsize=7.5,
            color="#333333",
        )
    hub_ax.set_title("Provincias asignadas a cada hub", fontsize=11.2, fontweight="bold")
    hub_ax.set_xlabel("Numero de provincias", fontsize=8.8)
    hub_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    hub_ax.tick_params(axis="both", labelsize=7.8)
    hub_ax.set_xlim(0, hub_summary["provinces"].max() + 3.2)

    fig.suptitle(
        "Mapa 3. Accesibilidad residencial a hubs de trabajo tech/IA",
        fontsize=20,
        fontweight="bold",
        x=0.44,
        y=0.985,
    )
    fig.text(
        0.02,
        0.012,
        "Fuente: capa metodologica propia de hubs tech/IA, MIVAU 2024 y Eurostat/GISCO NUTS 2024. "
        "Distancias euclideas en EPSG:3035; no representan tiempo real de viaje ni empleo observado.",
        fontsize=8.1,
        color="#4a4a4a",
    )
    fig.savefig(OUTPUT_DIR / "mapa3_accesibilidad_laboral_tech.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa3_accesibilidad_laboral_tech.pdf", bbox_inches="tight")
    plt.close(fig)


def province_popup_fields() -> tuple[list[str], list[str]]:
    return (
        [
            "PROVINCIA",
            "nearest_hub",
            "nearest_hub_km_label",
            "distance_class",
            "rent_label",
            "rental_homes_label",
            "distance_comment",
        ],
        [
            "Provincia",
            "Hub tech/IA mas cercano",
            "Distancia euclidea",
            "Clase",
            "Alquiler medio 2024",
            "Viviendas observadas",
            "Lectura",
        ],
    )


def add_legend(web_map: folium.Map, year: int) -> None:
    class_rows = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:6px; margin:3px 0;">
          <span style="width:13px; height:13px; background:{DISTANCE_COLORS[index + 1]};
                       border:1px solid #555; display:inline-block;"></span>
          <span>{html.escape(label)}</span>
        </div>
        """
        for index, label in enumerate(DISTANCE_LABELS)
    )
    hub_rows = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:5px; white-space:nowrap;">
          <span style="width:16px; height:3px; background:{HUB_COLORS[hub['hub_id']]};
                       display:inline-block;"></span>
          <span>{html.escape(hub['hub_name'])}</span>
        </div>
        """
        for hub in HUBS
    )
    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 28px;
        left: 28px;
        z-index: 9999;
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid #bdbdbd;
        border-radius: 4px;
        padding: 10px 12px;
        font-family: Arial, sans-serif;
        font-size: 12px;
        line-height: 1.35;
        box-shadow: 0 1px 5px rgba(0,0,0,0.18);
        max-width: 330px;
    ">
      <strong>Mapa 3 · accesibilidad tech</strong><br>
      Distancia al hub mas cercano<br>
      {class_rows}
      <hr style="margin:7px 0;">
      <strong>Anillos por hub</strong>: 50, 100, 175 y 250 km<br>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:2px 9px; margin-top:4px;">
        {hub_rows}
      </div>
      <hr style="margin:7px 0;">
      Alquiler {year} solo como contexto.<br>
      Distancia euclidea, no tiempo de viaje.
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(legend_html))


def save_interactive_map(
    map_data: gpd.GeoDataFrame,
    hubs: gpd.GeoDataFrame,
    buffers: gpd.GeoDataFrame,
    lines: gpd.GeoDataFrame,
    year: int,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    web_map = folium.Map(
        location=[40.1, -3.7],
        zoom_start=6,
        tiles="cartodbpositron",
        control_scale=True,
    )
    folium.TileLayer("CartoDB dark_matter", name="Base oscura", control=True).add_to(web_map)

    fields, aliases = province_popup_fields()
    province_layer = folium.GeoJson(
        map_data,
        name="Coropleta: distancia al hub tech/IA",
        style_function=lambda feature: {
            "fillColor": feature["properties"]["distance_color"],
            "color": "#ffffff",
            "weight": 0.65,
            "fillOpacity": 0.78,
        },
        highlight_function=lambda _: {"weight": 2.0, "color": "#111111", "fillOpacity": 0.9},
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "PROVINCIA",
                "nearest_hub",
                "nearest_hub_km_label",
                "distance_class",
                "rent_label",
            ],
            aliases=[
                "Provincia",
                "Hub cercano",
                "Distancia",
                "Clase",
                "Alquiler 2024",
            ],
            sticky=False,
            labels=True,
        ),
        popup=folium.GeoJsonPopup(fields=fields, aliases=aliases, labels=True, max_width=390),
    ).add_to(web_map)

    for radius in BUFFER_RADII_KM:
        subset = buffers[buffers["radius_km"].eq(radius)]
        group = folium.FeatureGroup(
            name=f"Anillos {radius} km por hub",
            show=radius in (100, 250),
        )
        folium.GeoJson(
            subset,
            name=f"Anillos {radius} km",
            style_function=lambda feature, radius=radius: {
                "fillColor": feature["properties"]["hub_color"],
                "color": feature["properties"]["hub_color"],
                "weight": 1.25,
                "dashArray": BUFFER_DASH_ARRAYS[radius],
                "fillOpacity": 0.0,
                "opacity": BUFFER_OPACITIES[radius],
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["hub_name", "radius_label"],
                aliases=["Hub", "Radio"],
                sticky=False,
            ),
        ).add_to(group)
        group.add_to(web_map)

    line_group = folium.FeatureGroup(name="Asignacion provincia-hub (lineas)", show=True)
    folium.GeoJson(
        lines,
        name="Lineas provincia-hub",
        style_function=lambda feature: {
            "color": feature["properties"]["line_color"],
            "weight": 0.85,
            "opacity": 0.48,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["PROVINCIA", "nearest_hub", "nearest_hub_km_label"],
            aliases=["Provincia", "Hub cercano", "Distancia"],
            sticky=False,
        ),
    ).add_to(line_group)
    line_group.add_to(web_map)

    hub_group = folium.FeatureGroup(name="Hubs tech/IA", show=True)
    for _, row in hubs.iterrows():
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; line-height: 1.35; min-width: 220px;">
          <strong style="font-size: 13px;">{html.escape(row['hub_name'])}</strong><br>
          <span>{html.escape(row['note'])}</span>
          <hr style="margin: 6px 0;">
          <table>
            <tr><td>Latitud</td><td style="text-align:right; padding-left:10px;">{row['latitude']:.4f}</td></tr>
            <tr><td>Longitud</td><td style="text-align:right; padding-left:10px;">{row['longitude']:.4f}</td></tr>
          </table>
        </div>
        """
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=8,
            tooltip=row["hub_name"],
            popup=folium.Popup(popup_html, max_width=300),
            color="#ffffff",
            weight=1.5,
            fill=True,
            fill_color=row["hub_color"],
            fill_opacity=0.96,
        ).add_to(hub_group)
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    transform: translate(10px, -8px);
                    min-width: 80px;
                    color: #111;
                    background: rgba(255,255,255,0.86);
                    border: 1px solid {row['hub_color']};
                    border-left: 5px solid {row['hub_color']};
                    border-radius: 3px;
                    padding: 1px 4px;
                    font-family: Arial, sans-serif;
                    font-size: 10px;
                    font-weight: 700;">
                    {html.escape(row['hub_name'])}
                </div>
                """
            ),
        ).add_to(hub_group)
    hub_group.add_to(web_map)

    add_legend(web_map, year)
    plugins.Search(
        layer=province_layer,
        search_label="PROVINCIA",
        placeholder="Buscar provincia",
        collapsed=True,
        geom_type="Polygon",
        position="topleft",
    ).add_to(web_map)
    plugins.Draw(export=False, position="topleft").add_to(web_map)
    plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(web_map)
    plugins.Fullscreen(position="topright").add_to(web_map)
    plugins.MiniMap(toggle_display=True, minimized=True, position="bottomright").add_to(web_map)
    folium.LayerControl(collapsed=False).add_to(web_map)

    web_map.save(OUTPUT_DIR / "mapa3_accesibilidad_laboral_tech_interactivo.html")


def save_tables(map_data: gpd.GeoDataFrame, hubs: gpd.GeoDataFrame, year: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    table_columns = [
        "COD_PROVINCIA",
        "PROVINCIA",
        "nearest_hub",
        "nearest_hub_km",
        "distance_class",
        "distance_rank",
        "rent_eur_month",
        "rental_homes",
    ]
    table = map_data[table_columns].sort_values(["distance_rank", "nearest_hub_km"]).copy()
    table["year"] = year
    table.to_csv(OUTPUT_DIR / "mapa3_accesibilidad_laboral_tech_datos.csv", index=False)

    hub_columns = ["hub_id", "hub_name", "province_code", "latitude", "longitude", "note"]
    hubs[hub_columns].to_csv(OUTPUT_DIR / "mapa3_hubs_tech.csv", index=False)


def main() -> None:
    map_data, hubs, buffers, lines, year = build_dataset()
    save_static_map(map_data, hubs, buffers, lines, year)
    save_interactive_map(map_data, hubs, buffers, lines, year)
    save_tables(map_data, hubs, year)

    print(f"Mapa 3 generado con alquiler contextual de {year}.")
    print(f"Provincias asignadas a hub: {len(map_data)}.")
    print(f"Clases de distancia: {map_data['distance_rank'].nunique()}.")
    print(f"Hubs tech/IA: {len(hubs)}.")
    print(f"Salidas en: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
