from __future__ import annotations

from pathlib import Path
import html
import math
import os
import shutil
import sys
import unicodedata
import zipfile


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
import urllib3
from shapely.geometry import LineString, Point


DATA_DIR = BASE_DIR / "datos"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"

RENFE_ALL_URL = (
    "https://data.renfe.com/dataset/ed3d44e5-1d04-41d6-9aa5-396442bf3e07/"
    "resource/783e0626-6fa8-4ac7-a880-fa53144654ff/download/"
    "listado-estaciones-completo-act.csv"
)
RENFE_GTFS_URL = "https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip"
BROADBAND_URL = (
    "https://digital.gob.es/content/dam/portal-mtdfp/avance-digital/"
    "telecomunicacion-e-infraestructuras-digitales/areas_interes/banda-ancha/"
    "cobertura/documents/cobertura_ba_espana_2021-2024_mun_prov_ccaa_nacional_datosgob.xlsx"
)
NUTS_URL = "https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_01M_2024_4326_LEVL_3.geojson"

RENFE_ALL_FILE = DATA_DIR / "renfe_estaciones_listado_completo.csv"
RENFE_GTFS_FILE = DATA_DIR / "renfe_gtfs_av_ld_md.zip"
BROADBAND_FILE = DATA_DIR / "cobertura_ba_espana_2021_2024.xlsx"
NUTS_FILE = DATA_DIR / "nuts3_2024_01m.geojson"

PROJECTED_CRS = "EPSG:3035"
HIGH_SPEED_SEGMENT_MAX_KM = 180.0
STRATEGIC_ACCESS_REFERENCE_KM = 100.0
MOBILITY_WEIGHTS = {
    "Alta velocidad": 2.0,
    "Larga distancia": 2.0,
    "Media distancia": 2.0,
    "Cercanias": 1.0,
    "FEVE": 1.0,
    "Aeropuerto": 3.0,
}
MOBILITY_PALETTE = ["#d6eaf8", "#a9d2e8", "#6baed6", "#3182bd", "#08519c"]
MODE_COLORS = {
    "Alta velocidad": "#08519c",
    "Larga distancia": "#3182bd",
    "Media distancia": "#6baed6",
    "Cercanias": "#31a354",
    "FEVE": "#756bb1",
    "Aeropuerto": "#ca6702",
}
RAIL_ROUTE_MODES = ["Alta velocidad", "Larga distancia", "Media distancia"]
STRATEGIC_MODES = RAIL_ROUTE_MODES + ["Aeropuerto"]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    "araba/alava": "01", "albacete": "02", "alicante/alacant": "03", "alicante": "03",
    "almeria": "04", "avila": "05", "badajoz": "06", "balears, illes": "07",
    "illes balears": "07", "baleares": "07", "barcelona": "08", "burgos": "09",
    "caceres": "10", "cadiz": "11", "castellon/castello": "12", "castellon": "12",
    "ciudad real": "13", "cordoba": "14", "coruna, a": "15", "a coruna": "15",
    "la coruna": "15", "cuenca": "16", "girona": "17", "gerona": "17",
    "granada": "18", "guadalajara": "19", "gipuzkoa": "20", "guipuzcoa": "20",
    "huelva": "21", "huesca": "22", "jaen": "23", "leon": "24", "lleida": "25",
    "lerida": "25", "rioja, la": "26", "la rioja": "26", "lugo": "27",
    "madrid": "28", "malaga": "29", "murcia": "30", "navarra": "31",
    "ourense": "32", "orense": "32", "asturias": "33", "palencia": "34",
    "palmas, las": "35", "las palmas": "35", "pontevedra": "36",
    "salamanca": "37", "santa cruz de tenerife": "38", "cantabria": "39",
    "segovia": "40", "sevilla": "41", "soria": "42", "tarragona": "43",
    "teruel": "44", "toledo": "45", "valencia/valencia": "46", "valencia": "46",
    "valladolid": "47", "bizkaia": "48", "vizcaya": "48", "zamora": "49",
    "zaragoza": "50", "ceuta": "51", "melilla": "52",
}

AIRPORTS = [
    ("A Coruña", "LCG", "15", 43.3021, -8.3773),
    ("Adolfo Suárez Madrid-Barajas", "MAD", "28", 40.4983, -3.5676),
    ("Albacete", "ABC", "02", 38.9485, -1.8635),
    ("Algeciras", "AEI", "11", 36.1289, -5.4411),
    ("Alicante-Elche Miguel Hernández", "ALC", "03", 38.2822, -0.5582),
    ("Almería", "LEI", "04", 36.8439, -2.3701),
    ("Asturias", "OVD", "33", 43.5636, -6.0346),
    ("Badajoz", "BJZ", "06", 38.8913, -6.8213),
    ("Bilbao", "BIO", "48", 43.3011, -2.9106),
    ("Burgos", "RGS", "09", 42.3576, -3.6208),
    ("Castellón", "CDT", "12", 40.2139, 0.0733),
    ("Ceuta", "JCU", "51", 35.8969, -5.3064),
    ("Córdoba", "ODB", "14", 37.8419, -4.8489),
    ("El Hierro", "VDE", "38", 27.8148, -17.8871),
    ("Federico García Lorca Granada-Jaén", "GRX", "18", 37.1887, -3.7774),
    ("Fuerteventura", "FUE", "35", 28.4527, -13.8638),
    ("Girona-Costa Brava", "GRO", "17", 41.9010, 2.7606),
    ("Gran Canaria", "LPA", "35", 27.9319, -15.3866),
    ("Huesca-Pirineos", "HSK", "22", 42.0761, -0.3167),
    ("Ibiza", "IBZ", "07", 38.8729, 1.3731),
    ("Internacional Región de Murcia", "RMU", "30", 37.8030, -1.1250),
    ("Jerez", "XRY", "11", 36.7446, -6.0601),
    ("Josep Tarradellas Barcelona-El Prat", "BCN", "08", 41.2974, 2.0833),
    ("La Gomera", "GMZ", "38", 28.0296, -17.2146),
    ("La Palma", "SPC", "38", 28.6265, -17.7556),
    ("León", "LEN", "24", 42.5890, -5.6556),
    ("Lleida-Alguaire", "ILD", "25", 41.7282, 0.5350),
    ("Logroño-Agoncillo", "RJL", "26", 42.4609, -2.3222),
    ("Madrid-Cuatro Vientos", "MCV", "28", 40.3707, -3.7851),
    ("Málaga-Costa del Sol", "AGP", "29", 36.6749, -4.4991),
    ("Melilla", "MLN", "52", 35.2798, -2.9563),
    ("Menorca", "MAH", "07", 39.8626, 4.2186),
    ("Palma de Mallorca", "PMI", "07", 39.5517, 2.7388),
    ("Pamplona", "PNA", "31", 42.7700, -1.6463),
    ("Reus", "REU", "43", 41.1474, 1.1672),
    ("Sabadell", "QSA", "08", 41.5209, 2.1051),
    ("Salamanca", "SLM", "37", 40.9521, -5.5019),
    ("San Sebastián", "EAS", "20", 43.3565, -1.7906),
    ("Santiago-Rosalía de Castro", "SCQ", "15", 42.8963, -8.4151),
    ("Seve Ballesteros-Santander", "SDR", "39", 43.4271, -3.8200),
    ("Sevilla", "SVQ", "41", 37.4180, -5.8931),
    ("Son Bonet", "SBO", "07", 39.5989, 2.7028),
    ("Tenerife Norte-Ciudad de La Laguna", "TFN", "38", 28.4827, -16.3415),
    ("Tenerife Sur", "TFS", "38", 28.0445, -16.5725),
    ("Valencia", "VLC", "46", 39.4893, -0.4816),
    ("Valladolid", "VLL", "47", 41.7061, -4.8519),
    ("Vigo", "VGO", "36", 42.2318, -8.6268),
    ("Vitoria", "VIT", "01", 42.8828, -2.7245),
    ("Zaragoza", "ZAZ", "50", 41.6662, -1.0416),
]


def download_file(url: str, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    verify_ssl = "ssl.renfe.com" not in url
    response = requests.get(
        url,
        timeout=120,
        headers={"User-Agent": "VD-map-project/1.0"},
        verify=verify_ssl,
    )
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
        .replace("\ufeff", "")
        .strip()
        for column in columns
    }


def clean_coord(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def format_int(value: float | int | None) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):,.0f}".replace(",", ".")


def format_float(value: float | int | None, decimals: int = 1) -> str:
    if pd.isna(value):
        return "sin dato"
    return f"{float(value):.{decimals}f}"


def rescale_0_100(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    clean = pd.to_numeric(series, errors="coerce")
    minimum = clean.min()
    maximum = clean.max()
    if pd.isna(minimum) or pd.isna(maximum) or maximum == minimum:
        return pd.Series(50.0, index=series.index)
    score = (clean - minimum) / (maximum - minimum) * 100
    if not higher_is_better:
        score = 100 - score
    return score.clip(0, 100)


def capped_distance_score(series: pd.Series, reference_km: float) -> pd.Series:
    clean = pd.to_numeric(series, errors="coerce")
    return (100 * (1 - clean.clip(lower=0, upper=reference_km) / reference_km)).clip(0, 100)


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


def load_province_geometries() -> gpd.GeoDataFrame:
    nuts = gpd.read_file(NUTS_FILE)
    nuts = nuts[nuts["CNTR_CODE"].eq("ES")].copy()
    nuts["COD_PROVINCIA"] = nuts["NUTS_ID"].map(PROVINCE_BY_NUTS)
    nuts = nuts.dropna(subset=["COD_PROVINCIA"])
    provinces = nuts.dissolve(by="COD_PROVINCIA", as_index=False)
    return provinces[["COD_PROVINCIA", "geometry"]].to_crs("EPSG:4326")


def load_population() -> pd.DataFrame:
    provincial = pd.read_excel(BROADBAND_FILE, sheet_name="Provincia_%hogar")
    provincial = provincial.rename(columns=normalize_columns(provincial.columns))
    provincial["COD_PROVINCIA"] = provincial["Provincia"].map(
        lambda value: PROVINCE_CODE_BY_NAME.get(normalize_text(value))
    )
    provincial["population"] = pd.to_numeric(provincial["Habitantes"], errors="coerce")
    return provincial[["COD_PROVINCIA", "Provincia", "population"]].rename(
        columns={"Provincia": "province_name"}
    )


def classify_rail_service(service_name: object) -> str:
    name = normalize_text(service_name).replace(".", "").replace(" ", "")
    if name in {"ave", "avlo", "avant", "avantexp", "aveint"}:
        return "Alta velocidad"
    if name in {"alvia", "intercity", "euromed", "trenhotel", "talgo"}:
        return "Larga distancia"
    return "Media distancia"


def read_gtfs_table(zip_file: zipfile.ZipFile, name: str, **kwargs) -> pd.DataFrame:
    with zip_file.open(name) as file:
        table = pd.read_csv(file, **kwargs)
    table.columns = table.columns.str.strip()
    return table


def load_gtfs_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    with zipfile.ZipFile(RENFE_GTFS_FILE) as gtfs:
        routes = read_gtfs_table(gtfs, "routes.txt", dtype=str)
        trips = read_gtfs_table(gtfs, "trips.txt", dtype=str)
        stop_times = read_gtfs_table(
            gtfs,
            "stop_times.txt",
            dtype={"trip_id": str, "stop_id": str, "stop_sequence": int},
        )
        stops = read_gtfs_table(gtfs, "stops.txt", dtype={"stop_id": str})

    routes["rail_mode"] = routes["route_short_name"].map(classify_rail_service)
    stops["stop_id"] = stops["stop_id"].astype(str).str.zfill(5)
    stop_times["stop_id"] = stop_times["stop_id"].astype(str).str.zfill(5)
    stops["stop_lat"] = pd.to_numeric(stops["stop_lat"], errors="coerce")
    stops["stop_lon"] = pd.to_numeric(stops["stop_lon"], errors="coerce")
    return routes, trips, stop_times, stops


def load_station_reference() -> pd.DataFrame:
    all_stations = pd.read_csv(RENFE_ALL_FILE, sep=";", encoding="latin1")
    all_stations = all_stations.rename(columns=normalize_columns(all_stations.columns))
    all_stations["CODIGO"] = all_stations["CODIGO"].astype(str).str.zfill(5)
    all_stations["LATITUD"] = clean_coord(all_stations["LATITUD"])
    all_stations["LONGITUD"] = clean_coord(all_stations["LONGITUD"])
    all_stations["province_name_raw"] = all_stations["PROVINCIA"].astype(str)
    all_stations["COD_PROVINCIA"] = all_stations["province_name_raw"].map(
        lambda value: PROVINCE_CODE_BY_NAME.get(normalize_text(value))
    )
    return all_stations.dropna(subset=["LATITUD", "LONGITUD", "COD_PROVINCIA"])


def complete_missing_province_codes(
    nodes: gpd.GeoDataFrame,
    provinces: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    result = nodes.copy()
    missing = result["COD_PROVINCIA"].isna()
    if not missing.any():
        return result

    province_lookup = provinces[["COD_PROVINCIA", "geometry"]].copy()
    spatial = gpd.sjoin(
        result[missing].drop(columns=["COD_PROVINCIA"]),
        province_lookup,
        how="left",
        predicate="within",
    )
    result.loc[missing, "COD_PROVINCIA"] = spatial["COD_PROVINCIA"].values
    return result


def load_renfe_stations(
    station_reference: pd.DataFrame,
    routes: pd.DataFrame,
    trips: pd.DataFrame,
    stop_times: pd.DataFrame,
    stops: pd.DataFrame,
    provinces: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    trip_modes = trips[["trip_id", "route_id"]].merge(
        routes[["route_id", "rail_mode"]], on="route_id", how="left"
    )
    served_stops = (
        stop_times[["trip_id", "stop_id"]]
        .merge(trip_modes, on="trip_id", how="left")
        .dropna(subset=["rail_mode"])
        .drop_duplicates(["stop_id", "rail_mode"])
        .merge(
            stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]],
            on="stop_id",
            how="left",
        )
    )
    served_stops = served_stops.dropna(subset=["stop_lat", "stop_lon"])
    served_stops = served_stops.merge(
        station_reference[
            ["CODIGO", "DESCRIPCION", "POBLACION", "PROVINCIA", "COD_PROVINCIA"]
        ],
        left_on="stop_id",
        right_on="CODIGO",
        how="left",
    )
    served_stops["CODIGO"] = served_stops["stop_id"]
    served_stops["DESCRIPCION"] = served_stops["DESCRIPCION"].fillna(
        served_stops["stop_name"]
    )
    served_stops["POBLACION"] = served_stops["POBLACION"].fillna(served_stops["stop_name"])
    served_stops["LATITUD"] = served_stops["stop_lat"]
    served_stops["LONGITUD"] = served_stops["stop_lon"]
    served_stops["mode"] = served_stops["rail_mode"]
    served_stops["source"] = "Renfe Data GTFS alta/larga/media"
    served_stops["node_weight"] = served_stops["mode"].map(MOBILITY_WEIGHTS)
    rail_geometry = [
        Point(lon, lat) for lon, lat in zip(served_stops["LONGITUD"], served_stops["LATITUD"])
    ]
    rail_nodes = gpd.GeoDataFrame(served_stops, geometry=rail_geometry, crs="EPSG:4326")
    rail_nodes = complete_missing_province_codes(rail_nodes, provinces)

    frames = [rail_nodes]
    cercanias = station_reference[
        station_reference["CERCANIAS"].astype(str).str.upper().eq("SI")
    ].copy()
    cercanias["mode"] = "Cercanias"
    frames.append(cercanias)

    feve = station_reference[station_reference["FEVE"].astype(str).str.upper().eq("SI")].copy()
    feve["mode"] = "FEVE"
    frames.append(feve)

    stations = pd.concat(frames, ignore_index=True).drop_duplicates(["CODIGO", "mode"])
    stations["node_weight"] = stations["mode"].map(MOBILITY_WEIGHTS)
    stations["source"] = stations["source"].fillna("Renfe Data")
    geometry = [Point(lon, lat) for lon, lat in zip(stations["LONGITUD"], stations["LATITUD"])]
    return gpd.GeoDataFrame(stations, geometry=geometry, crs="EPSG:4326").dropna(
        subset=["COD_PROVINCIA"]
    )


def load_airports() -> gpd.GeoDataFrame:
    airports = pd.DataFrame(
        AIRPORTS,
        columns=["DESCRIPCION", "iata", "COD_PROVINCIA", "LATITUD", "LONGITUD"],
    )
    airports["mode"] = "Aeropuerto"
    airports["node_weight"] = MOBILITY_WEIGHTS["Aeropuerto"]
    airports["source"] = "AENA/ENAIRE"
    airports["CODIGO"] = airports["iata"]
    airports["POBLACION"] = airports["DESCRIPCION"]
    airports["PROVINCIA"] = airports["COD_PROVINCIA"]
    geometry = [Point(lon, lat) for lon, lat in zip(airports["LONGITUD"], airports["LATITUD"])]
    return gpd.GeoDataFrame(airports, geometry=geometry, crs="EPSG:4326")


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    value = min(1.0, max(0.0, value))
    return 2 * radius_km * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def build_representative_route_stops(
    routes: pd.DataFrame,
    trips: pd.DataFrame,
    stop_times: pd.DataFrame,
    stops: pd.DataFrame,
) -> pd.DataFrame:
    trip_lengths = (
        stop_times.groupby("trip_id", as_index=False)
        .agg(stop_count=("stop_id", "count"))
        .merge(trips[["trip_id", "route_id"]], on="trip_id", how="left")
    )
    representative_trips = (
        trip_lengths.sort_values(["route_id", "stop_count"], ascending=[True, False])
        .drop_duplicates("route_id")
        [["trip_id", "route_id", "stop_count"]]
    )
    route_meta = routes[["route_id", "route_short_name", "rail_mode"]]
    route_stops = (
        stop_times.merge(representative_trips, on="trip_id", how="inner")
        .merge(stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]], on="stop_id", how="left")
        .merge(route_meta, on="route_id", how="left")
        .dropna(subset=["stop_lat", "stop_lon", "rail_mode"])
        .sort_values(["route_id", "stop_sequence"])
    )
    return route_stops


def build_route_lines_from_route_stops(route_stops: pd.DataFrame) -> gpd.GeoDataFrame:
    rows = []
    for route_id, group in route_stops.groupby("route_id", sort=False):
        points = [
            (float(lon), float(lat))
            for lon, lat in zip(group["stop_lon"], group["stop_lat"])
            if pd.notna(lon) and pd.notna(lat)
        ]
        if len(points) < 2:
            continue
        rows.append(
            {
                "route_id": route_id,
                "route_short_name": group["route_short_name"].iloc[0],
                "mode": group["rail_mode"].iloc[0],
                "stop_count": int(group["stop_count"].iloc[0]),
                "from_stop": group["stop_name"].iloc[0],
                "to_stop": group["stop_name"].iloc[-1],
                "source": "Renfe Data GTFS alta/larga/media",
                "geometry": LineString(points),
            }
        )
    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")


def build_route_lines(
    routes: pd.DataFrame,
    trips: pd.DataFrame,
    stop_times: pd.DataFrame,
    stops: pd.DataFrame,
) -> gpd.GeoDataFrame:
    route_stops = build_representative_route_stops(routes, trips, stop_times, stops)
    return build_route_lines_from_route_stops(route_stops)


def build_clean_high_speed_segments(route_stops: pd.DataFrame) -> gpd.GeoDataFrame:
    rows_by_pair: dict[tuple[str, str], dict[str, object]] = {}
    high_speed_stops = route_stops[route_stops["rail_mode"].eq("Alta velocidad")]

    for route_id, group in high_speed_stops.groupby("route_id", sort=False):
        ordered = list(group.itertuples())
        for start, end in zip(ordered, ordered[1:]):
            distance_km = haversine_km(
                float(start.stop_lon),
                float(start.stop_lat),
                float(end.stop_lon),
                float(end.stop_lat),
            )
            if distance_km > HIGH_SPEED_SEGMENT_MAX_KM:
                continue

            stop_ids = tuple(sorted([str(start.stop_id), str(end.stop_id)]))
            segment = rows_by_pair.get(stop_ids)
            if segment is None:
                segment = {
                    "stop_a_id": stop_ids[0],
                    "stop_b_id": stop_ids[1],
                    "stop_a": start.stop_name if str(start.stop_id) == stop_ids[0] else end.stop_name,
                    "stop_b": end.stop_name if str(start.stop_id) == stop_ids[0] else start.stop_name,
                    "distance_km": distance_km,
                    "services_set": set(),
                    "route_ids_set": set(),
                    "source": (
                        "Esquema GTFS: tramos entre paradas consecutivas; "
                        "no es geometria ferroviaria real"
                    ),
                    "geometry": LineString(
                        [
                            (float(start.stop_lon), float(start.stop_lat)),
                            (float(end.stop_lon), float(end.stop_lat)),
                        ]
                    ),
                }
                rows_by_pair[stop_ids] = segment

            segment["distance_km"] = min(float(segment["distance_km"]), distance_km)
            segment["services_set"].add(str(start.route_short_name))
            segment["route_ids_set"].add(str(route_id))

    rows = []
    for segment in rows_by_pair.values():
        services = sorted(segment.pop("services_set"))
        route_ids = sorted(segment.pop("route_ids_set"))
        segment["distance_km"] = round(float(segment["distance_km"]), 1)
        segment["services"] = ", ".join(services)
        segment["route_count"] = len(route_ids)
        segment["route_ids"] = ", ".join(route_ids)
        rows.append(segment)

    if not rows:
        return gpd.GeoDataFrame(
            columns=[
                "stop_a_id",
                "stop_b_id",
                "stop_a",
                "stop_b",
                "distance_km",
                "services",
                "route_count",
                "route_ids",
                "source",
                "geometry",
            ],
            geometry="geometry",
            crs="EPSG:4326",
        )

    return gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326").sort_values(
        ["stop_a", "stop_b"]
    )


def add_geographic_metrics(data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    result = data.copy()
    projected = result.to_crs(PROJECTED_CRS)
    points = projected.geometry.representative_point().to_crs("EPSG:4326")
    result["label_lon"] = points.x
    result["label_lat"] = points.y
    result["area_km2"] = (projected.area / 1_000_000).round(1)
    return result


def calculate_province_mobility(
    provinces: gpd.GeoDataFrame,
    population: pd.DataFrame,
    nodes: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    map_data = provinces.merge(population, on="COD_PROVINCIA", how="left")
    node_summary = (
        nodes.groupby("COD_PROVINCIA", as_index=False)
        .agg(
            transport_nodes=("CODIGO", "count"),
            weighted_transport_nodes=("node_weight", "sum"),
            high_speed_nodes=("mode", lambda values: int((values == "Alta velocidad").sum())),
            long_distance_nodes=("mode", lambda values: int((values == "Larga distancia").sum())),
            medium_distance_nodes=("mode", lambda values: int((values == "Media distancia").sum())),
            cercanias_nodes=("mode", lambda values: int((values == "Cercanias").sum())),
            feve_nodes=("mode", lambda values: int((values == "FEVE").sum())),
            airport_nodes=("mode", lambda values: int((values == "Aeropuerto").sum())),
        )
    )
    map_data = map_data.merge(node_summary, on="COD_PROVINCIA", how="left")
    count_columns = [
        "transport_nodes",
        "weighted_transport_nodes",
        "high_speed_nodes",
        "long_distance_nodes",
        "medium_distance_nodes",
        "cercanias_nodes",
        "feve_nodes",
        "airport_nodes",
    ]
    map_data[count_columns] = map_data[count_columns].fillna(0)
    map_data["av_ld_md_nodes"] = (
        map_data["high_speed_nodes"]
        + map_data["long_distance_nodes"]
        + map_data["medium_distance_nodes"]
    )
    map_data["nodes_per_100k"] = (
        map_data["weighted_transport_nodes"] / map_data["population"] * 100000
    )

    province_points = map_data.to_crs(PROJECTED_CRS).geometry.representative_point()
    strategic = nodes[nodes["mode"].isin(STRATEGIC_MODES)].to_crs(PROJECTED_CRS)
    strategic_union = strategic.geometry.union_all()
    map_data["nearest_strategic_km"] = province_points.distance(strategic_union) / 1000
    map_data["strategic_access_score"] = capped_distance_score(
        map_data["nearest_strategic_km"],
        STRATEGIC_ACCESS_REFERENCE_KM,
    )
    map_data["node_mass_score"] = rescale_0_100(
        map_data["weighted_transport_nodes"].map(lambda value: math.log1p(float(value))),
        higher_is_better=True,
    )
    map_data["node_density_score"] = rescale_0_100(
        map_data["nodes_per_100k"], higher_is_better=True
    )
    map_data["mobility_score"] = (
        map_data["strategic_access_score"] * 0.45
        + map_data["node_mass_score"] * 0.35
        + map_data["node_density_score"] * 0.20
    ).clip(0, 100)
    return add_geographic_metrics(map_data)


def build_dataset() -> tuple[
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    gpd.GeoDataFrame,
    list[float],
]:
    download_file(RENFE_ALL_URL, RENFE_ALL_FILE)
    download_file(RENFE_GTFS_URL, RENFE_GTFS_FILE)
    download_file(BROADBAND_URL, BROADBAND_FILE)
    download_file(NUTS_URL, NUTS_FILE)

    provinces = load_province_geometries()
    population = load_population()
    station_reference = load_station_reference()
    routes, trips, stop_times, stops = load_gtfs_tables()
    stations = load_renfe_stations(
        station_reference, routes, trips, stop_times, stops, provinces
    )
    airports = load_airports()
    nodes = pd.concat([stations, airports], ignore_index=True)
    nodes = gpd.GeoDataFrame(nodes, geometry="geometry", crs="EPSG:4326")
    route_stops = build_representative_route_stops(routes, trips, stop_times, stops)
    route_lines = build_route_lines_from_route_stops(route_stops)
    clean_high_speed_segments = build_clean_high_speed_segments(route_stops)
    map_data = calculate_province_mobility(provinces, population, nodes)

    required = ["population", "mobility_score", "nearest_strategic_km"]
    missing = map_data[map_data[required].isna().any(axis=1)]
    if not missing.empty:
        raise ValueError(
            "Faltan datos de movilidad/poblacion para: "
            + ", ".join(missing["COD_PROVINCIA"].tolist())
        )

    bins = build_quantile_bins(map_data["mobility_score"], 5)
    map_data["mobility_color"] = map_data["mobility_score"].map(
        lambda value: color_for_bins(value, bins, MOBILITY_PALETTE)
    )
    return map_data, nodes, route_lines, clean_high_speed_segments, bins


def save_static_map(
    map_data: gpd.GeoDataFrame,
    nodes: gpd.GeoDataFrame,
    route_lines: gpd.GeoDataFrame,
    clean_high_speed_segments: gpd.GeoDataFrame,
    bins: list[float],
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(16, 9.5), dpi=180)
    grid = fig.add_gridspec(2, 3, width_ratios=[1.25, 1.25, 0.95], hspace=0.34, wspace=0.2)
    map_ax = fig.add_subplot(grid[:, :2])
    rank_ax = fig.add_subplot(grid[0, 2])
    mode_ax = fig.add_subplot(grid[1, 2])

    map_data.plot(ax=map_ax, color=map_data["mobility_color"], linewidth=0.42, edgecolor="white")
    map_data.boundary.plot(ax=map_ax, color="#555555", linewidth=0.14, alpha=0.55)
    for mode in RAIL_ROUTE_MODES:
        if mode == "Alta velocidad":
            line_group = clean_high_speed_segments
        else:
            line_group = route_lines[route_lines["mode"].eq(mode)]
        if line_group.empty:
            continue
        line_group.plot(
            ax=map_ax,
            color=MODE_COLORS[mode],
            linewidth=0.55 if mode == "Alta velocidad" else 0.38,
            alpha=0.34,
            zorder=2,
        )

    visible_nodes = nodes[nodes["mode"].isin(STRATEGIC_MODES)]
    for mode, group in visible_nodes.groupby("mode"):
        size = 58 if mode == "Aeropuerto" else 22
        marker = "^" if mode == "Aeropuerto" else "o"
        map_ax.scatter(
            group.geometry.x,
            group.geometry.y,
            s=size,
            c=MODE_COLORS[mode],
            marker=marker,
            edgecolor="#1f1f1f",
            linewidth=0.25,
            alpha=0.82,
            label=mode,
            zorder=4,
        )

    top_labels = map_data.nlargest(7, "mobility_score")
    for _, row in top_labels.iterrows():
        text = map_ax.annotate(
            f"{row['province_name']}\n{row['mobility_score']:.1f}",
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
        for color, label in zip(MOBILITY_PALETTE, build_bin_labels(bins))
    ]
    map_ax.legend(
        handles=legend_handles,
        title="Score movilidad relativa",
        loc="lower right",
        fontsize=7.6,
        title_fontsize=8.7,
        frameon=True,
        framealpha=0.96,
    )
    map_ax.set_title(
        "Movilidad intermodal: recorridos Renfe y aeropuertos",
        fontsize=16.2,
        fontweight="bold",
        pad=12,
    )

    top = map_data.nlargest(10, "mobility_score").sort_values("mobility_score")
    rank_ax.barh(
        top["province_name"],
        top["mobility_score"],
        color=top["mobility_color"],
        edgecolor="#555555",
        linewidth=0.35,
    )
    rank_ax.set_title("Mejor movilidad relativa", fontsize=11, fontweight="bold")
    rank_ax.set_xlabel("Score 0-100", fontsize=8.5)
    rank_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    rank_ax.tick_params(axis="both", labelsize=8)

    mode_counts = (
        nodes.groupby("mode", as_index=False)
        .agg(nodos=("CODIGO", "count"), peso=("node_weight", "sum"))
        .sort_values("peso")
    )
    mode_ax.barh(
        mode_counts["mode"],
        mode_counts["peso"],
        color=[MODE_COLORS[mode] for mode in mode_counts["mode"]],
        edgecolor="#555555",
        linewidth=0.35,
    )
    mode_ax.set_title("Nodos ponderados por modo", fontsize=11, fontweight="bold")
    mode_ax.set_xlabel("Peso total", fontsize=8.5)
    mode_ax.grid(axis="x", color="#dddddd", linewidth=0.6)
    mode_ax.tick_params(axis="both", labelsize=8)

    for axis in [rank_ax, mode_ax]:
        for spine in ["top", "right", "left"]:
            axis.spines[spine].set_visible(False)

    fig.suptitle("Mapa 2. Movilidad y transporte", fontsize=20, fontweight="bold", x=0.44, y=0.985)
    fig.text(
        0.02,
        0.018,
        "Fuentes: Renfe Data GTFS alta/larga/media, Renfe Data estaciones, AENA/ENAIRE, SETELECO poblacion "
        "y Eurostat/GISCO. Las lineas unen paradas de recorridos GTFS; los aeropuertos son nodos, no rutas aereas.",
        fontsize=8,
        color="#555555",
    )
    fig.savefig(OUTPUT_DIR / "mapa2_movilidad_transportes.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa2_movilidad_transportes.pdf", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa2_movilidad_y_transporte.png", bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / "mapa2_movilidad_y_transporte.pdf", bbox_inches="tight")
    plt.close(fig)


def add_legend(web_map: folium.Map, bins: list[float]) -> None:
    rows = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:6px; margin:3px 0;">
          <span style="width:18px; height:12px; display:inline-block; background:{color};
          border:1px solid rgba(0,0,0,0.35);"></span>
          <span>{label}</span>
        </div>
        """
        for color, label in zip(MOBILITY_PALETTE, build_bin_labels(bins))
    )
    html_block = f"""
    <div style="
      position: fixed; bottom: 28px; right: 18px; z-index: 9999;
      background: rgba(255,255,255,0.94); padding: 10px 12px;
      border: 1px solid rgba(80,80,80,0.55); border-radius: 4px;
      font-family: Arial, sans-serif; font-size: 12px; line-height: 1.25;
      box-shadow: 0 1px 5px rgba(0,0,0,0.22);">
      <div style="font-weight:700; margin-bottom:5px;">Score movilidad relativa</div>
      {rows}
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(html_block))


def add_transport_radio_control(
    web_map: folium.Map,
    transport_layers: dict[str, list[str]],
) -> None:
    labels = {
        "none": "Ninguno",
        "Alta velocidad": "Alta velocidad GTFS limpio",
        "Larga distancia": "Larga distancia",
        "Media distancia": "Media distancia",
        "Aeropuerto": "Aeropuertos",
        "Cercanias": "Cercanias",
        "FEVE": "FEVE",
    }
    radios = "\n".join(
        f"""
        <label class="transport-radio-option">
          <input type="radio" name="transport-layer-mode" value="{html.escape(key)}"
                 {"checked" if key == "none" else ""}>
          <span>{html.escape(labels[key])}</span>
        </label>
        """
        for key in labels
    )
    layer_entries = ",\n".join(
        f'"{key}": [{", ".join(layer_names)}]' for key, layer_names in transport_layers.items()
    )
    map_name = web_map.get_name()
    control_css = """
    <style>
      .transport-radio-control {
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(80, 80, 80, 0.45);
        border-radius: 4px;
        box-shadow: 0 1px 5px rgba(0, 0, 0, 0.22);
        color: #222;
        font-family: Arial, sans-serif;
        font-size: 12px;
        line-height: 1.25;
        padding: 10px 12px;
        min-width: 205px;
      }
      .transport-radio-control-title {
        font-weight: 700;
        margin-bottom: 6px;
      }
      .transport-radio-option {
        align-items: center;
        cursor: pointer;
        display: flex;
        gap: 6px;
        margin: 5px 0;
        white-space: nowrap;
      }
      .transport-radio-option input {
        margin: 0;
      }
    </style>
    """
    control_script = f"""
      setTimeout(function() {{
        const map = {map_name};
        const transportLayers = {{
          none: [],
          {layer_entries}
        }};
        const allLayers = Object.values(transportLayers).flat();

        function setTransportMode(mode) {{
          allLayers.forEach((layer) => {{
            if (map.hasLayer(layer)) {{
              map.removeLayer(layer);
            }}
          }});
          (transportLayers[mode] || []).forEach((layer) => {{
            map.addLayer(layer);
          }});
        }}

        const control = L.control({{position: "topright"}});
        control.onAdd = function() {{
          const container = L.DomUtil.create("div", "transport-radio-control leaflet-bar");
          container.innerHTML = `
            <div class="transport-radio-control-title">Recorridos y nodos</div>
            {radios}
          `;
          L.DomEvent.disableClickPropagation(container);
          L.DomEvent.disableScrollPropagation(container);
          container.querySelectorAll("input[name='transport-layer-mode']").forEach((input) => {{
            input.addEventListener("change", () => setTransportMode(input.value));
          }});
          return container;
        }};
        control.addTo(map);
        setTransportMode("none");
      }}, 0);
    """
    web_map.get_root().header.add_child(folium.Element(control_css))
    web_map.get_root().script.add_child(folium.Element(control_script))


def save_interactive_map(
    map_data: gpd.GeoDataFrame,
    nodes: gpd.GeoDataFrame,
    route_lines: gpd.GeoDataFrame,
    clean_high_speed_segments: gpd.GeoDataFrame,
    bins: list[float],
) -> None:
    web_map = folium.Map(location=[40.2, -3.7], zoom_start=6, tiles="cartodbpositron")
    plugins.Fullscreen(position="topleft").add_to(web_map)
    plugins.MiniMap(toggle_display=True, minimized=True).add_to(web_map)
    folium.plugins.MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(
        web_map
    )

    province_layer = folium.FeatureGroup(name="Score provincial de movilidad relativa", show=True)
    folium.GeoJson(
        map_data,
        name="Score provincial",
        style_function=lambda feature: {
            "fillColor": feature["properties"]["mobility_color"],
            "color": "#555555",
            "weight": 0.55,
            "fillOpacity": 0.78,
        },
        highlight_function=lambda feature: {"weight": 2, "color": "#111111"},
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "province_name",
                "mobility_score",
                "weighted_transport_nodes",
                "nodes_per_100k",
                "node_mass_score",
                "nearest_strategic_km",
            ],
            aliases=[
                "Provincia",
                "Score movilidad",
                "Nodos ponderados",
                "Nodos ponderados / 100.000 hab.",
                "Score volumen nodos",
                "Distancia a nodo estrategico",
            ],
            localize=True,
            sticky=False,
        ),
        popup=folium.GeoJsonPopup(
            fields=[
                "province_name",
                "population",
                "transport_nodes",
                "high_speed_nodes",
                "long_distance_nodes",
                "medium_distance_nodes",
                "cercanias_nodes",
                "feve_nodes",
                "airport_nodes",
                "nodes_per_100k",
                "node_mass_score",
                "nearest_strategic_km",
                "mobility_score",
            ],
            aliases=[
                "Provincia",
                "Habitantes",
                "Nodos totales",
                "Alta velocidad",
                "Larga distancia",
                "Media distancia",
                "Cercanias",
                "FEVE",
                "Aeropuertos",
                "Nodos ponderados / 100.000 hab.",
                "Score volumen nodos",
                "Km a nodo estrategico",
                "Score movilidad",
            ],
            localize=True,
            max_width=390,
        ),
    ).add_to(province_layer)
    province_layer.add_to(web_map)

    transport_layers: dict[str, list[str]] = {}

    for mode in RAIL_ROUTE_MODES:
        if mode == "Alta velocidad":
            route_group = clean_high_speed_segments.copy()
            layer_name = "Alta velocidad: esquema GTFS limpio"
            tooltip_fields = ["stop_a", "stop_b", "distance_km", "services", "route_count"]
            tooltip_aliases = ["Parada A", "Parada B", "Distancia directa (km)", "Servicios", "Rutas"]
            popup_fields = [
                "stop_a",
                "stop_b",
                "distance_km",
                "services",
                "route_count",
                "source",
            ]
            popup_aliases = [
                "Parada A",
                "Parada B",
                "Distancia directa (km)",
                "Servicios",
                "Rutas",
                "Fuente/nota",
            ]
        else:
            route_group = route_lines[route_lines["mode"].eq(mode)].copy()
            layer_name = f"Recorridos: {mode}"
            tooltip_fields = ["route_short_name", "from_stop", "to_stop", "stop_count"]
            tooltip_aliases = ["Servicio", "Desde", "Hasta", "Paradas"]
            popup_fields = ["route_short_name", "mode", "from_stop", "to_stop", "source"]
            popup_aliases = ["Servicio", "Modo", "Desde", "Hasta", "Fuente"]

        if route_group.empty:
            continue

        route_layer = folium.GeoJson(
            route_group,
            name=layer_name,
            show=False,
            control=False,
            style_function=lambda feature, local_mode=mode: {
                "color": MODE_COLORS[local_mode],
                "weight": 2.0 if local_mode == "Alta velocidad" else 1.45,
                "opacity": 0.58,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases,
                sticky=False,
            ),
            popup=folium.GeoJsonPopup(
                fields=popup_fields,
                aliases=popup_aliases,
                max_width=360,
            ),
        )
        route_layer.add_to(web_map)
        transport_layers.setdefault(mode, []).append(route_layer.get_name())

    for mode in RAIL_ROUTE_MODES + ["Aeropuerto", "Cercanias", "FEVE"]:
        cluster = plugins.MarkerCluster(name=f"Nodos: {mode}", show=False, control=False)
        group = nodes[nodes["mode"].eq(mode)]
        for _, row in group.iterrows():
            radius = 6 if mode != "Aeropuerto" else 8
            popup_html = (
                f"<b>{html.escape(str(row['DESCRIPCION']))}</b><br>"
                f"Modo: {html.escape(str(row['mode']))}<br>"
                f"Provincia/codigo: {html.escape(str(row['COD_PROVINCIA']))}<br>"
                f"Poblacion local: {html.escape(str(row.get('POBLACION', 'sin dato')))}<br>"
                f"Fuente: {html.escape(str(row['source']))}"
            )
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=radius,
                color="#262626",
                weight=0.5,
                fill=True,
                fill_color=MODE_COLORS[mode],
                fill_opacity=0.82,
                tooltip=f"{row['DESCRIPCION']} ({mode})",
                popup=folium.Popup(popup_html, max_width=340),
            ).add_to(cluster)
        cluster.add_to(web_map)
        transport_layers.setdefault(mode, []).append(cluster.get_name())

    add_legend(web_map, bins)
    add_transport_radio_control(web_map, transport_layers)
    folium.LayerControl(collapsed=False).add_to(web_map)
    web_map.save(OUTPUT_DIR / "mapa2_movilidad_transportes_interactivo.html")
    shutil.copyfile(
        OUTPUT_DIR / "mapa2_movilidad_transportes_interactivo.html",
        OUTPUT_DIR / "mapa2_movilidad_y_transporte_interactivo.html",
    )


def save_tables(
    map_data: gpd.GeoDataFrame,
    nodes: gpd.GeoDataFrame,
    route_lines: gpd.GeoDataFrame,
    clean_high_speed_segments: gpd.GeoDataFrame,
) -> None:
    province_columns = [
        "COD_PROVINCIA",
        "province_name",
        "population",
        "transport_nodes",
        "weighted_transport_nodes",
        "high_speed_nodes",
        "long_distance_nodes",
        "medium_distance_nodes",
        "av_ld_md_nodes",
        "cercanias_nodes",
        "feve_nodes",
        "airport_nodes",
        "nodes_per_100k",
        "nearest_strategic_km",
        "strategic_access_score",
        "node_mass_score",
        "node_density_score",
        "mobility_score",
        "label_lat",
        "label_lon",
        "area_km2",
    ]
    node_columns = [
        "CODIGO",
        "DESCRIPCION",
        "mode",
        "COD_PROVINCIA",
        "POBLACION",
        "node_weight",
        "source",
        "LATITUD",
        "LONGITUD",
    ]
    map_data[province_columns].round(2).to_csv(
        OUTPUT_DIR / "mapa2_movilidad_transportes_datos.csv", index=False
    )
    map_data[province_columns].round(2).to_csv(
        OUTPUT_DIR / "mapa2_movilidad_y_transporte_datos.csv", index=False
    )
    nodes[node_columns].to_csv(
        OUTPUT_DIR / "mapa2_movilidad_transportes_nodos.csv", index=False
    )
    route_lines[
        ["route_id", "route_short_name", "mode", "from_stop", "to_stop", "stop_count", "source"]
    ].to_csv(OUTPUT_DIR / "mapa2_movilidad_transportes_recorridos.csv", index=False)

    clean_segments_table = clean_high_speed_segments[
        [
            "stop_a_id",
            "stop_b_id",
            "stop_a",
            "stop_b",
            "distance_km",
            "services",
            "route_count",
            "route_ids",
            "source",
        ]
    ].copy()
    clean_segments_table["distance_km"] = clean_segments_table["distance_km"].round(1)
    clean_segments_table.to_csv(
        OUTPUT_DIR / "mapa2_movilidad_transportes_tramos_av_limpios.csv",
        index=False,
    )


def main() -> None:
    map_data, nodes, route_lines, clean_high_speed_segments, bins = build_dataset()
    save_static_map(map_data, nodes, route_lines, clean_high_speed_segments, bins)
    save_interactive_map(map_data, nodes, route_lines, clean_high_speed_segments, bins)
    save_tables(map_data, nodes, route_lines, clean_high_speed_segments)
    print("Mapa 2 generado: movilidad y transporte.")
    print(
        f"Provincias: {len(map_data)} | nodos: {len(nodes)} | "
        f"recorridos: {len(route_lines)} | tramos AV limpios: {len(clean_high_speed_segments)}"
    )


if __name__ == "__main__":
    main()
