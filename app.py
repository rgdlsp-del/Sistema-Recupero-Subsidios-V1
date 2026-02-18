"""UI Streamlit para recuperación de subsidios."""

from __future__ import annotations

import streamlit as st

from src.alertas import calcular_alertas
from src.casos import calcular_consecutividad
from src.io_excel import cargar_excel
from src.kpis import calcular_kpis

st.set_page_config(page_title="Sistema Recupero Subsidios", layout="wide")
st.title("Sistema de Recupero de Subsidios")

archivo = st.file_uploader("Cargar archivo Excel", type=["xlsx"])

if archivo is not None:
    try:
        df = cargar_excel(archivo)
        df = calcular_consecutividad(df)
        df = calcular_alertas(df)
        kpis = calcular_kpis(df)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total casos", kpis["total_casos"])
    c2.metric("Casos cierre", kpis["casos_cierre"])
    c3.metric("Alertas Nivel 1", kpis["alertas_nivel_1"])
    c4.metric("Alertas Nivel 2", kpis["alertas_nivel_2"])

    st.caption(
        f"Monto total: ${kpis['monto_total']:,.2f} | "
        f"Tasa cierre: {kpis['tasa_cierre']:.2f}%"
    )

    estados = sorted(df["estado"].dropna().unique().tolist())
    agentes = sorted(df["agente"].dropna().unique().tolist())
    alertas = ["Todas"] + sorted(df["alerta"].dropna().unique().tolist())

    f1, f2, f3 = st.columns(3)
    filtro_estado = f1.multiselect("Estado", options=estados, default=[])
    filtro_agente = f2.multiselect("Agente", options=agentes, default=[])
    filtro_alerta = f3.selectbox("Alerta", options=alertas, index=0)

    filtrado = df.copy()
    if filtro_estado:
        filtrado = filtrado[filtrado["estado"].isin(filtro_estado)]
    if filtro_agente:
        filtrado = filtrado[filtrado["agente"].isin(filtro_agente)]
    if filtro_alerta != "Todas":
        filtrado = filtrado[filtrado["alerta"] == filtro_alerta]

    columnas_tabla = [
        "id",
        "fecha_registro",
        "fecha_ultimo_mov",
        "estado",
        "subestado",
        "caso",
        "dias_sin_mov",
        "prioridad_consecutividad",
        "alerta",
        "agente",
        "monto",
    ]

    st.subheader("Casos")
    st.dataframe(filtrado[columnas_tabla], use_container_width=True, hide_index=True)

    st.subheader("Detalle de caso")
    ids = filtrado["id"].astype(str).tolist()
    if ids:
        id_seleccionado = st.selectbox("Seleccionar ID", options=ids)
        detalle = filtrado[filtrado["id"].astype(str) == id_seleccionado].iloc[0]
        st.json({k: str(v) for k, v in detalle.to_dict().items()})
    else:
        st.info("No hay casos para los filtros seleccionados.")
else:
    st.info("Sube un archivo para comenzar.")
