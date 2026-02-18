"""Cálculo de KPIs agregados."""

from __future__ import annotations

import pandas as pd


def calcular_kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Retorna KPIs clave para el tablero."""

    total = len(df)
    cierres = int(df["es_cierre"].sum())
    abiertos = total - cierres
    nivel_1 = int(df["alerta_nivel_1"].sum())
    nivel_2 = int(df["alerta_nivel_2"].sum())
    monto_total = float(df["monto"].sum())

    tasa_cierre = (cierres / total * 100) if total else 0.0

    return {
        "total_casos": total,
        "casos_abiertos": abiertos,
        "casos_cierre": cierres,
        "alertas_nivel_1": nivel_1,
        "alertas_nivel_2": nivel_2,
        "monto_total": monto_total,
        "tasa_cierre": tasa_cierre,
    }
