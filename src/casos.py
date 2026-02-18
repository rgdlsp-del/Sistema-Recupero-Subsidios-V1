"""Motor de casos: clasificación y consecutividad de gestión."""

from __future__ import annotations

import pandas as pd

ESTADOS_CIERRE = {"cerrado", "finalizado", "pagado"}


def clasificar_caso(estado: str, subestado: str) -> str:
    """Asigna etiqueta de caso según estado/subestado."""

    estado_norm = (estado or "").strip().lower()
    subestado_norm = (subestado or "").strip().lower()

    if estado_norm in ESTADOS_CIERRE:
        return "Cierre"
    if "devol" in subestado_norm:
        return "Devolucion"
    if "reclamo" in subestado_norm:
        return "Reclamo"
    if "pend" in estado_norm:
        return "Pendiente"
    return "En gestion"


def calcular_consecutividad(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula dias de inactividad y prioridad de consecutividad."""

    data = df.copy()
    hoy = pd.Timestamp.today().normalize()
    data["dias_sin_mov"] = (hoy - data["fecha_ultimo_mov"].dt.normalize()).dt.days
    data["dias_sin_mov"] = data["dias_sin_mov"].fillna(999).astype(int)

    data["caso"] = data.apply(
        lambda row: clasificar_caso(row.get("estado", ""), row.get("subestado", "")),
        axis=1,
    )
    data["es_cierre"] = data["caso"].eq("Cierre")

    data["prioridad_consecutividad"] = pd.cut(
        data["dias_sin_mov"],
        bins=[-1, 2, 7, 15, 10_000],
        labels=["Baja", "Media", "Alta", "Critica"],
    ).astype(str)

    data = data.sort_values(by=["es_cierre", "dias_sin_mov", "fecha_registro"], ascending=[True, False, True])
    return data
