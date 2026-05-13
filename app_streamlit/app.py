from __future__ import annotations

from pathlib import Path
import importlib.util
import sys


sys.dont_write_bytecode = True

ROOT_DIR = Path(__file__).resolve().parents[1]
MAP5_SCRIPT = ROOT_DIR / "5_indice_destino_tech" / "mapa5_indice_destino_tech.py"

import folium
from folium import plugins
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium


COMPONENT_LABELS = {
    "rent_score_low_price": "Alquiler bajo",
    "mobility_score": "Movilidad",
    "connectivity_score": "Conectividad",
    "climate_score": "Clima temp+lluvia",
}

DEFAULT_RAW_WEIGHTS = {
    "rent_score_low_price": 41.18,
    "mobility_score": 23.53,
    "connectivity_score": 23.53,
    "climate_score": 11.76,
}

COMPONENT_COLORS = {
    "rent_score_low_price": "#2a9d8f",
    "mobility_score": "#577590",
    "connectivity_score": "#277da1",
    "climate_score": "#90be6d",
}


def load_map6_module():
    spec = importlib.util.spec_from_file_location("mapa5_indice_destino_tech", MAP5_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {MAP5_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@st.cache_data(show_spinner="Cargando indicadores provinciales...")
def load_base_data(script_mtime: float):
    module = load_map6_module()
    map_data, current_year, _ = module.build_dataset()
    map_data = map_data.copy()
    map_data["default_index"] = map_data["tech_destination_index"]
    map_data["default_rank"] = map_data["rank_tech"]
    return map_data, current_year


def normalize_weights(raw_weights: dict[str, float]) -> dict[str, float]:
    total = sum(raw_weights.values())
    if total <= 0:
        return {column: 1 / len(raw_weights) for column in raw_weights}
    return {column: value / total for column, value in raw_weights.items()}


def format_weight(weights: dict[str, float], column: str) -> str:
    return f"{weights[column] * 100:.1f}%"


def recalculate_index(
    data: pd.DataFrame,
    weights: dict[str, float],
    min_coverage: float,
    max_rent: float,
):
    module = load_map6_module()
    result = data.copy()

    contribution_columns = []
    for score_column, weight in weights.items():
        contribution_column = f"app_contribution_{score_column}"
        result[contribution_column] = result[score_column] * weight
        contribution_columns.append(contribution_column)

    result["app_index"] = result[contribution_columns].sum(axis=1).round(2)
    result["app_rank"] = result["app_index"].rank(method="min", ascending=False).astype(int)
    result["rank_change_vs_default"] = result["default_rank"] - result["app_rank"]

    result["passes_filters"] = (
        result["coverage_1gbps_2024_pct"].ge(min_coverage)
        & result["rent_eur_month"].le(max_rent)
    )

    result["filtered_rank"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    filtered_index = result[result["passes_filters"]]["app_index"].rank(
        method="min", ascending=False
    )
    result.loc[filtered_index.index, "filtered_rank"] = filtered_index.astype(int)
    result["filtered_rank_label"] = result["filtered_rank"].map(
        lambda value: "-" if pd.isna(value) else f"#{int(value)}"
    )
    result["filter_label"] = result["passes_filters"].map(
        lambda value: "Dentro de filtros" if value else "Fuera de filtros"
    )

    bins = module.build_quantile_bins(result["app_index"], k=5)
    result["app_index_class"] = result["app_index"].map(
        lambda value: module.label_for_bins(value, bins)
    )
    result["app_index_color"] = result["app_index"].map(
        lambda value: module.color_for_bins(value, bins, module.INDEX_PALETTE)
    )
    return result, bins


def add_map_legend(web_map: folium.Map, bins: list[float]) -> None:
    module = load_map6_module()
    rows = "".join(
        f"""
        <div style="display:flex; align-items:center; gap:6px; margin:3px 0;">
          <span style="width:18px; height:12px; display:inline-block; background:{color};
          border:1px solid rgba(0,0,0,0.35);"></span>
          <span>{label}</span>
        </div>
        """
        for color, label in zip(module.INDEX_PALETTE, module.build_bin_labels(bins))
    )
    html = f"""
    <div style="
      position: fixed; top: 16px; right: 16px; z-index: 9999;
      background: rgba(255,255,255,0.94); padding: 9px 10px;
      border: 1px solid rgba(60,60,60,0.55); border-radius: 4px;
      font-family: Arial, sans-serif; font-size: 11.5px; line-height: 1.25;
      box-shadow: 0 1px 5px rgba(0,0,0,0.22);">
      <div style="font-size:12.5px; font-weight:700; margin-bottom:6px;">Indice recalculado</div>
      {rows}
    </div>
    """
    web_map.get_root().html.add_child(folium.Element(html))


def build_folium_map(map_data: pd.DataFrame, bins: list[float], top_n: int) -> folium.Map:
    module = load_map6_module()
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

    tooltip_fields = [
        "province_name",
        "filtered_rank_label",
        "app_index",
        "app_index_class",
        "rent_eur_month",
        "mobility_label",
        "nearest_strategic_label",
        "coverage_1gbps_2024_pct",
        "rental_homes_per_1000_households",
        "precipitation_annual_mm",
        "climate_comfort_score",
        "filter_label",
    ]
    tooltip_aliases = [
        "Provincia",
        "Ranking filtrado",
        "Indice recalculado",
        "Clase",
        "Alquiler mensual",
        "Movilidad",
        "Nodo estrategico cercano",
        "Cobertura 1 Gbps",
        "Alquiler / 1.000 hogares",
        "Precipitacion anual",
        "Confort climatico temp+lluvia",
        "Filtro",
    ]

    layer = folium.GeoJson(
        map_data,
        name="Indice recalculado",
        style_function=lambda feature: {
            "fillColor": "#d3d3d3"
            if not feature["properties"]["passes_filters"]
            else module.color_for_bins(
                feature["properties"]["app_index"],
                bins,
                module.INDEX_PALETTE,
            ),
            "color": "#666666",
            "weight": 0.42,
            "fillOpacity": 0.24
            if not feature["properties"]["passes_filters"]
            else 0.84,
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
                "rent_score_low_price",
                "mobility_score",
                "connectivity_score",
                "temperature_comfort_score",
                "rain_comfort_score",
                "climate_score",
                "app_index",
                "rank_change_vs_default",
            ],
            aliases=[
                "Provincia",
                "Score alquiler bajo",
                "Score movilidad",
                "Score conectividad",
                "Score temperatura",
                "Score lluvia",
                "Score clima final",
                "Indice recalculado",
                "Cambio ranking vs. pesos base",
            ],
            localize=True,
            labels=True,
            max_width=380,
        ),
    ).add_to(web_map)

    label_layer = folium.FeatureGroup(name=f"Etiquetas top {top_n}", show=True)
    top_rows = map_data[map_data["passes_filters"]].sort_values("filtered_rank").head(top_n)
    for _, row in top_rows.iterrows():
        label_html = f"""
        <div style="
          min-width: 90px; padding: 2px 5px;
          background: rgba(255, 255, 255, 0.90);
          border: 1px solid #444; border-radius: 3px;
          color: #111; font-family: Arial, sans-serif;
          font-size: 10px; font-weight: 700; line-height: 1.15;
          text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.25);">
          {row['filtered_rank_label']} {row['province_name']}<br>{row['app_index']:.1f}
        </div>
        """
        folium.Marker(
            location=[row["label_lat"], row["label_lon"]],
            icon=folium.DivIcon(html=label_html, icon_size=(96, 32), icon_anchor=(48, 16)),
            tooltip=f"{row['filtered_rank_label']} {row['province_name']}",
        ).add_to(label_layer)
    label_layer.add_to(web_map)

    add_map_legend(web_map, bins)
    plugins.Search(
        layer=layer,
        geom_type="Polygon",
        placeholder="Buscar provincia",
        collapsed=True,
        search_label="province_name",
        position="topleft",
    ).add_to(web_map)
    plugins.Fullscreen(position="topleft").add_to(web_map)
    plugins.MiniMap(toggle_display=True, minimized=True).add_to(web_map)
    folium.LayerControl(collapsed=True, position="bottomleft").add_to(web_map)
    return web_map


def build_download_table(data: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "filtered_rank",
        "app_rank",
        "default_rank",
        "rank_change_vs_default",
        "COD_PROVINCIA",
        "province_name",
        "ccaa",
        "app_index",
        "default_index",
        "rent_eur_month",
        "mobility_score",
        "transport_nodes",
        "weighted_transport_nodes",
        "high_speed_nodes",
        "long_distance_nodes",
        "medium_distance_nodes",
        "nodes_per_100k",
        "nearest_strategic_km",
        "strategic_access_score",
        "node_density_score",
        "node_mass_score",
        "rental_homes_per_1000_households",
        "coverage_1gbps_2024_pct",
        "precipitation_annual_mm",
        "temperature_comfort_score",
        "rain_comfort_score",
        "climate_comfort_score",
        "rent_score_low_price",
        "availability_score",
        "connectivity_score",
        "climate_score",
        "passes_filters",
    ]
    return data[columns].sort_values(["passes_filters", "app_index"], ascending=[False, False])


def main() -> None:
    st.set_page_config(
        page_title="Mapa 5 | Indice destino tech",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    base_data, current_year = load_base_data(MAP5_SCRIPT.stat().st_mtime)

    st.sidebar.header("Pesos del indice")
    raw_weights = {}
    for column, label in COMPONENT_LABELS.items():
        raw_weights[column] = st.sidebar.slider(
            label,
            min_value=0.0,
            max_value=60.0,
            value=DEFAULT_RAW_WEIGHTS[column],
            step=0.01,
        )
    weights = normalize_weights(raw_weights)
    st.sidebar.caption(
        f"Suma bruta: {sum(raw_weights.values())}. La app normaliza siempre a 100%."
    )

    st.sidebar.header("Filtros")
    min_coverage = st.sidebar.slider("Cobertura minima 1 Gbps (%)", 0, 100, 0, 5)
    min_rent = int(base_data["rent_eur_month"].min() // 25 * 25)
    max_rent_value = int((base_data["rent_eur_month"].max() // 25 + 1) * 25)
    max_rent = st.sidebar.slider(
        "Alquiler maximo mensual (euros)",
        min_value=min_rent,
        max_value=max_rent_value,
        value=max_rent_value,
        step=25,
    )
    top_n = st.sidebar.slider("Tamano del ranking visible", 5, 20, 10, 1)

    data, bins = recalculate_index(
        base_data,
        weights,
        min_coverage,
        max_rent,
    )
    filtered = data[data["passes_filters"]].copy().sort_values("filtered_rank")

    st.title("Mapa 5. Indice final de destino residencial tech")
    st.caption(
        "App Streamlit para recalcular pesos, filtrar provincias y explorar el ranking final."
    )

    if filtered.empty:
        st.warning("No hay provincias que cumplan los filtros actuales.")
        return

    winner = filtered.iloc[0]
    metric_cols = st.columns(5)
    metric_cols[0].metric("Destino #1", winner["province_name"])
    metric_cols[1].metric("Indice", f"{winner['app_index']:.1f}")
    metric_cols[2].metric("Alquiler", f"{winner['rent_eur_month']:.0f} euros/mes")
    metric_cols[3].metric("Movilidad", f"{winner['mobility_score']:.1f} / 100")
    metric_cols[4].metric("Provincias filtradas", f"{len(filtered)} / {len(data)}")

    tab_map, tab_ranking, tab_province, tab_method = st.tabs(
        ["Mapa recalculado", "Ranking y patrones", "Provincia seleccionada", "Metodo"]
    )

    with tab_map:
        left, right = st.columns([1.85, 1])
        with left:
            st_folium(
                build_folium_map(data, bins, top_n),
                use_container_width=True,
                height=640,
                returned_objects=[],
            )
        with right:
            st.subheader(f"Top {top_n}")
            show_columns = [
                "filtered_rank",
                "province_name",
                "app_index",
                "rent_eur_month",
                "mobility_score",
                "nearest_strategic_km",
                "coverage_1gbps_2024_pct",
                "precipitation_annual_mm",
                "rank_change_vs_default",
            ]
            st.dataframe(
                filtered[show_columns].head(top_n),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "filtered_rank": "Rank",
                    "province_name": "Provincia",
                    "app_index": "Indice",
                    "rent_eur_month": "Alquiler",
                    "mobility_score": "Movilidad",
                    "nearest_strategic_km": "Nodo cercano km",
                    "coverage_1gbps_2024_pct": "1 Gbps",
                    "precipitation_annual_mm": "Lluvia anual",
                    "rank_change_vs_default": "Cambio vs base",
                },
            )
            csv = build_download_table(data).to_csv(index=False).encode("utf-8")
            st.download_button(
                "Descargar ranking recalculado",
                data=csv,
                file_name="mapa5_ranking_recalculado.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with tab_ranking:
        top_chart = filtered.head(top_n).sort_values("app_index")
        fig_rank = px.bar(
            top_chart,
            x="app_index",
            y="province_name",
            orientation="h",
            color="app_index",
            color_continuous_scale=["#cc4c02", "#fdb863", "#018571"],
            text="app_index",
            labels={"app_index": "Indice recalculado", "province_name": "Provincia"},
        )
        fig_rank.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_rank.update_layout(height=420, coloraxis_showscale=False, margin=dict(l=10, r=10))
        st.plotly_chart(fig_rank, use_container_width=True)

        scatter = px.scatter(
            data,
            x="rent_eur_month",
            y="coverage_1gbps_2024_pct",
            size="rental_homes_per_1000_households",
            color="app_index",
            hover_name="province_name",
            color_continuous_scale=["#cc4c02", "#fdb863", "#018571"],
            labels={
                "rent_eur_month": "Alquiler mensual medio",
                "coverage_1gbps_2024_pct": "Cobertura 1 Gbps (%)",
                "rental_homes_per_1000_households": "Alquiler / 1.000 hogares",
                "app_index": "Indice",
            },
        )
        scatter.update_layout(height=430, margin=dict(l=10, r=10))
        st.plotly_chart(scatter, use_container_width=True)

    with tab_province:
        default_selection = winner["province_name"]
        province_name = st.selectbox(
            "Provincia",
            options=sorted(data["province_name"].tolist()),
            index=sorted(data["province_name"].tolist()).index(default_selection),
        )
        selected = data[data["province_name"].eq(province_name)].iloc[0]

        province_cols = st.columns(6)
        province_cols[0].metric("Ranking filtrado", selected["filtered_rank_label"])
        province_cols[1].metric("Indice", f"{selected['app_index']:.1f}")
        province_cols[2].metric("Alquiler", f"{selected['rent_eur_month']:.0f} euros")
        province_cols[3].metric("Movilidad", f"{selected['mobility_score']:.1f} / 100")
        province_cols[4].metric("Lluvia anual", f"{selected['precipitation_annual_mm']:.0f} mm")
        province_cols[5].metric("Cambio vs base", f"{selected['rank_change_vs_default']:+.0f}")

        score_columns = list(COMPONENT_LABELS.keys())
        radar = go.Figure()
        radar.add_trace(
            go.Scatterpolar(
                r=[selected[column] for column in score_columns],
                theta=[COMPONENT_LABELS[column] for column in score_columns],
                fill="toself",
                name=province_name,
                line_color="#018571",
            )
        )
        radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            height=430,
            margin=dict(l=20, r=20, t=35, b=20),
        )

        contribution_df = pd.DataFrame(
            {
                "Componente": [COMPONENT_LABELS[column] for column in score_columns],
                "Aportacion": [selected[f"app_contribution_{column}"] for column in score_columns],
                "Peso": [format_weight(weights, column) for column in score_columns],
                "Color": [COMPONENT_COLORS[column] for column in score_columns],
            }
        )
        contrib = px.bar(
            contribution_df,
            x="Aportacion",
            y="Componente",
            orientation="h",
            color="Componente",
            color_discrete_map=dict(
                zip(contribution_df["Componente"], contribution_df["Color"])
            ),
            hover_data=["Peso"],
        )
        contrib.update_layout(
            height=430,
            showlegend=False,
            margin=dict(l=10, r=10, t=35, b=20),
            xaxis_title="Aportacion ponderada",
            yaxis_title=None,
        )

        chart_left, chart_right = st.columns(2)
        chart_left.plotly_chart(radar, use_container_width=True)
        chart_right.plotly_chart(contrib, use_container_width=True)

    with tab_method:
        st.subheader("Formula activa")
        formula_rows = [
            {
                "Componente": COMPONENT_LABELS[column],
                "Peso normalizado": format_weight(weights, column),
                "Variable": variable,
            }
            for column, variable in [
                ("rent_score_low_price", "Alquiler medio ponderado bajo"),
                (
                    "mobility_score",
                    "Acceso a AV/LD/MD o aeropuerto, volumen de nodos y nodos ponderados por 100.000 habitantes",
                ),
                ("connectivity_score", "Cobertura fija >= 1 Gbps"),
                (
                    "climate_score",
                    "Confort climatico: 70% temperatura y 30% lluvia anual equilibrada",
                ),
            ]
        ]
        st.dataframe(pd.DataFrame(formula_rows), use_container_width=True, hide_index=True)

        st.markdown(
            """
            La app recalcula el indice con los pesos elegidos en la barra lateral. Los pesos se
            normalizan automaticamente para sumar 100%, por lo que puedes comparar escenarios sin
            preocuparte de cuadrar la suma exacta.

            El componente climatico combina la cercania a una temperatura media anual de referencia
            con una puntuacion de lluvia equilibrada, que penaliza tanto provincias muy secas como
            excesivamente lluviosas frente a la mediana provincial.

            Los filtros no cambian el valor del indice: solo sirven para limitar el ranking visible.
            En el mapa, las provincias fuera de filtro aparecen en gris para mantener el contexto
            geografico completo.
            """
        )


if __name__ == "__main__":
    main()
