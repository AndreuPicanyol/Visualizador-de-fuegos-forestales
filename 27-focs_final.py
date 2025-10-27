import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

# =====================================================
# 🧭 Configuración básica
# =====================================================
import streamlit as st

st.set_page_config(page_title="🔥 Visualizador de Incendios Forestales", layout="wide", initial_sidebar_state="expanded")

# Configuración de tema dentro del código
st.markdown(
    """
    <style>
    body {
        background-color: #2e2e2e;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔥 Visualizador de Incendios Forestales")

# =====================================================
# 🧩 Función para obtener rango de fechas con validación
# =====================================================
def obtener_rango_fechas(df, columna_fecha="fecha"):
    df[columna_fecha] = pd.to_datetime(df[columna_fecha], errors="coerce")

    fecha_min_default = df[columna_fecha].min().date()
    fecha_max_default = df[columna_fecha].max().date()

    st.sidebar.write(f"📅 Rango de datos: {fecha_min_default} — {fecha_max_default}")

    fecha_desde = st.sidebar.date_input(
        "Desde",
        value=fecha_min_default,
        min_value=fecha_min_default,
        max_value=fecha_max_default
    )
    fecha_hasta = st.sidebar.date_input(
        "Hasta",
        value=fecha_max_default,
        min_value=fecha_min_default,
        max_value=fecha_max_default
    )

    if fecha_desde > fecha_hasta:
        st.sidebar.error("⚠️ La fecha 'Desde' no puede ser posterior a 'Hasta'. Se intercambiarán automáticamente.")
        fecha_desde, fecha_hasta = fecha_hasta, fecha_desde

    fecha_min = datetime.datetime.combine(fecha_desde, datetime.datetime.min.time())
    fecha_max = datetime.datetime.combine(fecha_hasta, datetime.datetime.max.time())

    # Mini timeline interactivo
    df_timeline = df.copy()
    df_timeline["fecha"] = pd.to_datetime(df_timeline["fecha"], errors="coerce")
    df_timeline["año"] = df_timeline["fecha"].dt.year
    timeline_data = df_timeline.groupby("año")["id"].count().reset_index().sort_values("año")

    fig_timeline = go.Figure()
    fig_timeline.add_trace(
        go.Scatter(
            x=timeline_data["año"],
            y=timeline_data["id"],
            mode="lines",
            name="Incendios por año",
            line=dict(color="firebrick", width=2)
        )
    )
    fig_timeline.add_vline(x=fecha_min.year, line_dash="dash", line_color="green", annotation_text="Desde", annotation_position="top left")
    fig_timeline.add_vline(x=fecha_max.year, line_dash="dash", line_color="blue", annotation_text="Hasta", annotation_position="top right")

    fig_timeline.update_layout(
        title="📆 Rango temporal seleccionado",
        xaxis_title="Año",
        yaxis_title="N° incendios",
        height=200,
        margin=dict(l=30, r=30, t=40, b=30),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.sidebar.plotly_chart(fig_timeline, use_container_width=True)

    return fecha_min, fecha_max

# =====================================================
# 🔥 Cargar datos
# =====================================================
df = pd.read_csv('./dat/fires-all.csv', encoding='UTF-8')
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

# Diccionario de causas
d_causas = {
    1: 'rayo',
    2: 'accidente/negligencia',
    3: 'trabajos forestales',
    4: 'intencionado',
    5: 'causa desconocida',
    6: 'incendio reproducido'
}
df["causa"] = pd.to_numeric(df["causa"], errors="coerce").map(d_causas)

# Diccionario de comunidades (idcomunidad → nombre)
d_comunidades = {
    1: 'Andalucía',
    2: 'Cataluña',
    3: 'Galicia',
    4: 'Andalucía',
    5: 'Asturias',
    6: 'Cantabria',
    7: 'La Rioja',
    8: 'Murcia',
    9: 'Valencia',
    10: 'Aragón',
    11: 'Castilla-La Mancha',
    12: 'Canarias',
    13: 'País Vasco',
    14: 'Castilla-La Mancha',
    15: 'Islas Baleares',
    16: 'Madrid',
    17: 'Castilla y León',
    18: 'Ceuta'
}
df["comunidad"] = df["idcomunidad"].map(d_comunidades)

# =====================================================
# 🎚️ Barra lateral: filtros
# =====================================================
st.sidebar.header("Filtros")

# Filtro por causa
causa = st.sidebar.multiselect("Causa", sorted(df["causa"].dropna().unique()))

# Filtro por siniestralidad
siniestralidad = st.sidebar.selectbox(
    "Siniestralidad",
    ["Todos", "Heridos", "Muertos", "Heridos y Muertos"]
)

# Filtro por rango de fechas
fecha_min, fecha_max = obtener_rango_fechas(df)

# Slider dinámico según número total de incendios
total_incendios = len(df)
max_incendios = st.sidebar.slider(
    "Cantidad de incendios a mostrar",
    min_value=0,
    max_value=total_incendios,
    value=min(100000, total_incendios),  # valor inicial grande
    step=100
)

# 🆕 Filtro por superficie quemada (ha) usando min/max
st.sidebar.markdown("### 🌾 Superficie quemada (ha)")
superficie_min = float(df["superficie"].min())
superficie_max = float(df["superficie"].max())
ha_min, ha_max = st.sidebar.slider(
    "Selecciona rango de hectáreas",
    min_value=0.0,
    max_value=superficie_max,
    value=(superficie_min, superficie_max),
    step=1.0
)

# =====================================================
# 🧮 Aplicar filtros
# =====================================================
df_filtrado = df[
    (df["fecha"] >= fecha_min) & (df["fecha"] <= fecha_max)
]

# Filtrar por causa
if causa:
    df_filtrado = df_filtrado[df_filtrado["causa"].isin(causa)]

# Filtrar por siniestralidad
if siniestralidad == "Heridos":
    df_filtrado = df_filtrado[df_filtrado["heridos"] > 0]
elif siniestralidad == "Muertos":
    df_filtrado = df_filtrado[df_filtrado["muertos"] > 0]
elif siniestralidad == "Heridos y Muertos":
    df_filtrado = df_filtrado[(df_filtrado["heridos"] > 0) | (df_filtrado["muertos"] > 0)]

# Filtrar por superficie quemada usando el slider
df_filtrado = df_filtrado[(df_filtrado["superficie"] >= ha_min) & (df_filtrado["superficie"] <= ha_max)]

df_filtrado = df_filtrado.dropna(subset=["lat", "lng"])
df_vis = df_filtrado.sort_values(by="superficie", ascending=False).head(max_incendios)

# =====================================================
# 📊 Estadísticas generales
# =====================================================
if not df_vis.empty:
    st.markdown("### 📊 Estadísticas generales")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Incendios", len(df_vis))
    col2.metric("Superficie quemada (ha)", int(df_vis["superficie"].sum()))
    col3.metric("Muertes", int(df_vis["muertos"].sum()))
    col4.metric("Heridos", int(df_vis["heridos"].sum()))
else:
    st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados.")

# =====================================================
# 🗂️ Pestañas principales
# =====================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗺️ Mapa", "📈 Evolución", "🔥 Causas", "📆 Estacionalidad", "🚒 Por comunidad"])

# =====================================================
# 🗺️ TAB 1 - Mapa interactivo
# =====================================================
with tab1:
    if not df_vis.empty:
        st.subheader("🗺️ Mapa de la distribución de los incendios")
        fig_map = px.scatter_mapbox(
            df_vis,
            lat="lat",
            lon="lng",
            color="causa",
            size="superficie",
            hover_name="municipio",
            hover_data={
                "fecha": True,
                "superficie": True,
                "muertos": True,
                "heridos": True,
                "lat": False,
                "lng": False
            },
            zoom=5,
            height=600,
        )
        fig_map.update_layout(mapbox_style="carto-positron", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("No hay datos para mostrar en el mapa.")

# =====================================================
# 📈 TAB 2 - Evolución anual
# =====================================================
with tab2:
    if not df_vis.empty:
        st.subheader("📈 Evolución anual de incendios y superficie quemada")
        df_year = df_vis.copy()
        df_year["año"] = df_year["fecha"].dt.year
        df_grouped = df_year.groupby("año").agg({"superficie": "sum"}).reset_index()
        df_grouped["incendios"] = df_year.groupby("año").size().values

        # Crear gráfico combinado
        fig = go.Figure()
        # Barras: incendios
        paleta_rojos = px.colors.sequential.Reds

        # Barras: incendios
        fig.add_trace(go.Bar(
            x=df_grouped["año"],
            y=df_grouped["incendios"],
            name="Número de incendios",
            marker_color=paleta_rojos[4]  # un rojo medio
        ))
        # Líneas: superficie quemada
        fig.add_trace(go.Scatter(
            x=df_grouped["año"],
            y=df_grouped["superficie"],
            name="Superficie quemada (ha)",
            mode="lines+markers",
            line=dict(color=paleta_rojos[-2], width=3),  # un rojo más intenso
            yaxis="y2"
        ))


        fig.update_layout(
            title="Incendios y superficie quemada por año",
            yaxis=dict(title="Número de incendios"),
            yaxis2=dict(title="Superficie quemada (ha)", overlaying="y", side="right"),
            barmode="group",
            legend=dict(x=0.01, y=0.99),
            margin={"r":40,"t":40,"l":0,"b":0}
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar la evolución.")

# =====================================================
# 🔥 TAB 3 - Evolución de causas
# =====================================================
with tab3:
    if not df_vis.empty:
        st.subheader("📈 Evolución de incendios por causa")
        df_causas = df_vis.copy()
        df_causas["año"] = df_causas["fecha"].dt.year
        df_grouped = df_causas.groupby(["año", "causa"]).size().reset_index(name="cantidad")

        fig_causas = px.line(
            df_grouped,
            x="año",
            y="cantidad",
            color="causa",
            markers=True,
            color_discrete_sequence=px.colors.sequential.Reds
        )
        fig_causas.update_layout(
            title="Incendios por causa a lo largo de los años",
            xaxis_title="Año",
            yaxis_title="Cantidad de incendios",
            legend_title="Causa"
        )
        st.plotly_chart(fig_causas, use_container_width=True)
    else:
        st.info("No hay datos para mostrar causas.")

# =====================================================
# 📆 TAB 4 - Estacionalidad
# =====================================================
with tab4:
    if not df_vis.empty:
        st.subheader("📆 Estacionalidad (por mes)")
        df_month = df_vis.copy()
        df_month["mes"] = df_month["fecha"].dt.month
        df_month_group = df_month.groupby("mes")["id"].count().reset_index()
        fig_month = px.bar(
            df_month_group, x="mes", y="id",
            title="Número de incendios por mes",
            labels={"id": "Incendios"},  # Cambié aquí
            color="id",
            color_continuous_scale=px.colors.sequential.Reds
        )
        st.plotly_chart(fig_month, use_container_width=True)
    else:
        st.info("No hay datos estacionales para mostrar.")


# =====================================================
# 🏆 TAB 5 - Ranking por comunidad autónoma
# =====================================================
with tab5:
    if not df_vis.empty:
        st.subheader(" Comunidades autónomas con más incendios")
        ranking_comunidad = (
            df_vis.groupby("comunidad")["id"]
            .count()
            .reset_index()
            .rename(columns={"id": "incendios"})
            .sort_values(by="incendios", ascending=False)
        )
        fig_rank = px.bar(
            ranking_comunidad,
            x="comunidad",
            y="incendios",
            title="Ranking de incendios por comunidad autónoma",
            color="incendios",
            color_continuous_scale=px.colors.sequential.Reds
        )

        st.plotly_chart(fig_rank, use_container_width=True)
    else:
        st.info("No hay datos para mostrar el ranking.")


