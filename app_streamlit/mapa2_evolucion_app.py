from __future__ import annotations

from pathlib import Path
import importlib.util
import sys


sys.dont_write_bytecode = True

ROOT_DIR = Path(__file__).resolve().parents[1]
MAP2_SCRIPT = ROOT_DIR / "2_evolucion_alquiler" / "mapa2_evolucion_alquiler.py"

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium


def load_map2_module():
    spec = importlib.util.spec_from_file_location("mapa2_evolucion_alquiler", MAP2_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {MAP2_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@st.cache_data(show_spinner="Cargando anos disponibles...")
def load_year_options(script_mtime: float) -> list[int]:
    module = load_map2_module()
    module.download_file(module.MIVAU_URL, module.RENT_FILE)
    rent = module.load_mivau()
    yearly = module.build_yearly_province_rent(rent)
    return sorted(int(year) for year in yearly["year"].unique())


@st.cache_data(show_spinner="Preparando trayectorias provinciales...")
def load_data(
    script_mtime: float,
    start_year: int,
    end_year: int,
    allow_first_available: bool,
):
    module = load_map2_module()
    return module.build_dataset(
        start_year=start_year,
        end_year=end_year,
        allow_first_available=allow_first_available,
    )


def build_download_table(data: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "COD_PROVINCIA",
        "province_name",
        "trajectory_class",
        "analysis_window",
        "baseline_note",
        "baseline_rent_eur_month",
        "current_rent_eur_month",
        "rent_change_eur_month",
        "growth_total_pct",
        "growth_recent_pct",
        "growth_pre_pct",
        "acceleration_pp_year",
        "current_rental_homes",
        "current_municipalities",
        "series_complete_2011_2019",
        "has_growth_history",
    ]
    return data[columns].sort_values(
        ["has_growth_history", "growth_total_pct"],
        ascending=[False, False],
        na_position="last",
    )


def build_rank_chart(data: pd.DataFrame, top_n: int):
    ranking = (
        data[data["has_growth_history"]]
        .nlargest(top_n, "growth_total_pct")
        .sort_values("growth_total_pct")
    )
    fig = px.bar(
        ranking,
        x="growth_total_pct",
        y="province_short",
        orientation="h",
        text="growth_total_label",
        color="trajectory_class",
        color_discrete_map={
            row["trajectory_class"]: row["trajectory_fill"]
            for _, row in data.drop_duplicates("trajectory_class").iterrows()
        },
        labels={
            "growth_total_pct": "Subida total (%)",
            "province_short": "",
            "trajectory_class": "Trayectoria",
        },
    )
    fig.update_traces(textposition="outside", marker_line_color="#555", marker_line_width=0.4)
    fig.update_layout(
        height=420,
        margin=dict(l=8, r=24, t=8, b=18),
        xaxis_title="Subida total (%)",
        yaxis_title="",
        legend_title_text="Trayectoria",
    )
    return fig


def build_matrix_chart(data: pd.DataFrame):
    matrix = data.dropna(subset=["acceleration_pp_year", "growth_total_pct"]).copy()
    fig = px.scatter(
        matrix,
        x="growth_total_pct",
        y="acceleration_pp_year",
        color="trajectory_class",
        symbol="trajectory_class",
        size="current_rental_homes",
        size_max=18,
        hover_name="province_name",
        hover_data={
            "growth_total_label": True,
            "growth_recent_label": True,
            "growth_pre_label": True,
            "acceleration_label": True,
            "current_rent_label": True,
            "current_rental_homes": ":,.0f",
            "growth_total_pct": False,
            "acceleration_pp_year": False,
        },
        color_discrete_map={
            row["trajectory_class"]: row["trajectory_fill"]
            for _, row in data.drop_duplicates("trajectory_class").iterrows()
        },
        labels={
            "growth_total_pct": "Subida total (%)",
            "acceleration_pp_year": "Aceleracion (pp/ano)",
            "trajectory_class": "Trayectoria",
        },
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#777")
    if not matrix.empty:
        fig.add_vline(x=matrix["growth_total_pct"].median(), line_dash="dot", line_color="#999")
    fig.update_layout(height=470, margin=dict(l=8, r=16, t=8, b=18))
    return fig


def build_class_chart(data: pd.DataFrame, order: list[str]):
    counts = (
        data["trajectory_class"]
        .value_counts()
        .reindex(order)
        .dropna()
        .reset_index()
    )
    counts.columns = ["trajectory_class", "provinces"]
    fig = px.bar(
        counts,
        x="provinces",
        y="trajectory_class",
        orientation="h",
        text="provinces",
        color="trajectory_class",
        color_discrete_map={
            row["trajectory_class"]: row["trajectory_fill"]
            for _, row in data.drop_duplicates("trajectory_class").iterrows()
        },
        labels={"provinces": "Provincias", "trajectory_class": ""},
    )
    fig.update_layout(
        height=330,
        margin=dict(l=8, r=16, t=8, b=18),
        showlegend=False,
        yaxis=dict(categoryorder="array", categoryarray=list(reversed(order))),
    )
    return fig


def build_series_chart(yearly: pd.DataFrame, row: pd.Series, current_year: int):
    module = load_map2_module()
    code = row["COD_PROVINCIA"]
    subset = yearly[yearly["COD_PROVINCIA"].eq(code)].copy()
    subset = subset[subset["year"].le(current_year)].copy()
    subset["rent_index"] = subset["rent_eur_month"] / subset["rent_eur_month"].iloc[0] * 100

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=subset["year"],
            y=subset["rent_eur_month"],
            mode="lines+markers",
            line=dict(color=row["trajectory_fill"], width=2.4),
            marker=dict(size=6, color=row["trajectory_fill"]),
            name="Alquiler",
            hovertemplate="%{x}: %{y:.0f} EUR<extra></extra>",
        )
    )

    if row["has_growth_history"]:
        baseline_year = int(row["baseline_year"])
        fig.add_vline(x=baseline_year, line_dash="dash", line_color="#2166ac")
        fig.add_vline(x=int(row["recent_start_year"]), line_dash="dot", line_color="#f28e2b")
        fig.add_vline(x=current_year, line_dash="dash", line_color="#b2182b")
        fig.add_annotation(
            x=baseline_year,
            y=float(row["baseline_rent_eur_month"]),
            text=module.format_eur(row["baseline_rent_eur_month"]),
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-34,
            font=dict(size=11),
        )
        fig.add_annotation(
            x=current_year,
            y=float(row["current_rent_eur_month"]),
            text=module.format_eur(row["current_rent_eur_month"]),
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-34,
            font=dict(size=11),
        )

    fig.update_layout(
        height=360,
        margin=dict(l=8, r=18, t=8, b=18),
        xaxis_title="Ano",
        yaxis_title="EUR / mes",
        showlegend=False,
    )
    return fig


def main() -> None:
    st.set_page_config(page_title="Mapa 2 - Trayectorias del alquiler", layout="wide")
    st.title("Mapa 2: trayectorias del alquiler")

    script_mtime = MAP2_SCRIPT.stat().st_mtime
    years = load_year_options(script_mtime)
    module = load_map2_module()

    with st.sidebar:
        st.header("Periodo")
        start_year = st.selectbox(
            "Ano inicial",
            options=years[:-1],
            index=years[:-1].index(2019) if 2019 in years[:-1] else 0,
        )
        end_options = [year for year in years if year > start_year]
        end_year = st.selectbox("Ano final", options=end_options, index=len(end_options) - 1)
        allow_first_available = st.checkbox("Primer historico comparable", value=True)
        top_n = st.slider("Top provincias", min_value=5, max_value=20, value=10, step=1)

    map_data, yearly, current_year, bins = load_data(
        script_mtime,
        start_year,
        end_year,
        allow_first_available,
    )

    class_options = [name for name in module.TRAJECTORY_ORDER if name in set(map_data["trajectory_class"])]
    with st.sidebar:
        selected_classes = st.multiselect(
            "Trayectorias",
            options=class_options,
            default=class_options,
        )

    filtered = map_data[map_data["trajectory_class"].isin(selected_classes)].copy()
    if filtered.empty:
        st.warning("No hay provincias con las trayectorias seleccionadas.")
        return

    valid = map_data[map_data["has_growth_history"]].copy()
    leader = valid.nlargest(1, "growth_total_pct").iloc[0]
    accelerator = valid.nlargest(1, "acceleration_pp_year").iloc[0]

    metric_cols = st.columns(4)
    metric_cols[0].metric("Mayor subida", leader["province_short"], leader["growth_total_label"])
    metric_cols[1].metric(
        "Mayor aceleracion",
        accelerator["province_short"],
        accelerator["acceleration_label"],
    )
    metric_cols[2].metric("Con historico", f"{int(map_data['has_growth_history'].sum())}/{len(map_data)}")
    metric_cols[3].metric("Serie 2011-2019", int(map_data["series_complete_2011_2019"].sum()))

    tab_map, tab_traj, tab_province = st.tabs(["Mapa", "Trayectorias", "Provincia"])

    with tab_map:
        left, right = st.columns([1.45, 0.9], gap="large")
        with left:
            web_map = module.build_web_map(
                filtered,
                bins,
                current_year,
                start_year,
                yearly=yearly,
                top_n=top_n,
            )
            st_folium(web_map, height=610, use_container_width=True)
        with right:
            st.plotly_chart(build_rank_chart(filtered, top_n), use_container_width=True)

    with tab_traj:
        left, right = st.columns([1.25, 0.75], gap="large")
        with left:
            st.plotly_chart(build_matrix_chart(filtered), use_container_width=True)
        with right:
            st.plotly_chart(
                build_class_chart(map_data, module.TRAJECTORY_ORDER),
                use_container_width=True,
            )
            st.dataframe(
                build_download_table(filtered),
                use_container_width=True,
                hide_index=True,
            )

    with tab_province:
        province_options = filtered.sort_values("province_name")["province_name"].tolist()
        selected = st.selectbox("Provincia", options=province_options)
        selected_row = filtered[filtered["province_name"].eq(selected)].iloc[0]

        detail_cols = st.columns([0.8, 1.2], gap="large")
        with detail_cols[0]:
            st.subheader(selected)
            st.metric("Trayectoria", selected_row["trajectory_class"])
            st.metric("Alquiler final", selected_row["current_rent_label"])
            st.metric("Subida total", selected_row["growth_total_label"])
            st.metric("2021-final", selected_row["growth_recent_label"])
            st.metric("Aceleracion", selected_row["acceleration_label"])
            st.caption(
                f"Periodo: {selected_row['analysis_window']} · "
                f"{selected_row['baseline_note']} · {selected_row['trajectory_description']}"
            )
        with detail_cols[1]:
            st.plotly_chart(
                build_series_chart(yearly, selected_row, current_year),
                use_container_width=True,
            )

    download_table = build_download_table(filtered)
    st.download_button(
        "Descargar ranking CSV",
        data=download_table.to_csv(index=False).encode("utf-8"),
        file_name="mapa2_trayectorias_alquiler.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
