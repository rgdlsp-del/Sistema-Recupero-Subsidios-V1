"""UI Streamlit para recuperación de subsidios."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import streamlit as st

from src.alertas import calcular_alertas
from src.casos import calcular_consecutividad
from src.io_excel import cargar_excel
from src.kpis import calcular_kpis

st.set_page_config(page_title="Sistema Recupero Subsidios", layout="wide")
st.title("Sistema de Recupero de Subsidios")

GESTION_COLUMNS = [
    "EMPRESA",
    "DNI",
    "APELLIDOS Y NOMBRES",
    "TIPO DE SUBSIDIO",
    "FECHA DE INICIO",
    "FECHA FIN",
    "TOTAL DIAS",
    "VENCIMIENTO DE EXPEDIENTE",
    "STATUS PLATAFORMA VIVA",
    "STATUS TRABAJADORA SOCIAL",
    "STATUS EBE",
    "EXPEDIENTE",
    "IMPORTE SOLICITADO",
    "IMPORTE REEMBOLSADO POR ESSALUD",
    "DIFERENCIA S/. A FAVOR",
    "DIFERENCIA S/. EN CONTRA",
    "FECHA ULTIMA ACCION",
    "DETALLE DE RPTA ESSALUD OBSERVACIÓN",
    "FECHA DE COBRO (CONTABILIDAD)",
    "AÑO DE COBRO (CONTABILIDAD)",
    "MES DE COBRO (CONTABILIDAD)",
]


def _columnas_presentes(df: pd.DataFrame, orden: list[str]) -> list[str]:
    return [col for col in orden if col in df.columns]


def _build_excel_report(gestion_df: pd.DataFrame, detalle_df: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        gestion_df.to_excel(writer, index=False, sheet_name="GESTION")
        detalle_df.to_excel(writer, index=False, sheet_name="DETALLE")
    buffer.seek(0)
    return buffer.getvalue()


archivo = st.file_uploader("Cargar archivo Excel", type=["xlsx"])

if archivo is not None:
    try:
        df, faltantes_opcionales = cargar_excel(archivo)
        df = calcular_consecutividad(df)
        df = calcular_alertas(df)
        kpis = calcular_kpis(df)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    if faltantes_opcionales:
        st.warning(
            "Faltan columnas opcionales para la vista de gestión: "
            + ", ".join(faltantes_opcionales)
        )

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
    filtro_estado = f1.multiselect("Estado plataforma", options=estados, default=[])
    filtro_agente = f2.multiselect("Trabajadora social", options=agentes, default=[])
    filtro_alerta = f3.selectbox("Alerta", options=alertas, index=0)

    filtrado = df.copy()
    if filtro_estado:
        filtrado = filtrado[filtrado["estado"].isin(filtro_estado)]
    if filtro_agente:
        filtrado = filtrado[filtrado["agente"].isin(filtro_agente)]
    if filtro_alerta != "Todas":
        filtrado = filtrado[filtrado["alerta"] == filtro_alerta]

    columnas_tabla = _columnas_presentes(filtrado, GESTION_COLUMNS)

    st.subheader("Gestión de casos")
    if columnas_tabla:
        st.dataframe(filtrado[columnas_tabla], use_container_width=True, hide_index=True)
    else:
        st.info("No hay columnas de gestión disponibles para mostrar.")

    if not filtrado.empty:
        reporte_excel = _build_excel_report(
            gestion_df=filtrado[columnas_tabla] if columnas_tabla else pd.DataFrame(),
            detalle_df=filtrado[df.columns],
        )
        st.download_button(
            "Descargar reporte Excel (.xlsx)",
            data=reporte_excel,
            file_name="reporte_recupero_subsidios.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        with st.expander("Ver detalle del caso seleccionado"):
            opciones = {
                f"{str(row.get('APELLIDOS Y NOMBRES', 'Sin nombre'))} | DNI {str(row.get('DNI', 'Sin DNI'))}": idx
                for idx, row in filtrado.iterrows()
            }
            seleccionado = st.selectbox(
                "Seleccionar caso",
                options=list(opciones.keys()),
                index=None,
                placeholder="Seleccione un caso para ver su detalle",
            )
            if seleccionado:
                idx = opciones[seleccionado]
                detalle = filtrado.loc[idx, df.columns]
                st.dataframe(detalle.to_frame("Valor"), use_container_width=True)
    else:
        st.info("No hay casos para los filtros seleccionados.")
else:
    st.info("Sube un archivo para comenzar.")
