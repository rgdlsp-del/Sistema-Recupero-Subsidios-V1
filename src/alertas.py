"""Reglas de alertamiento: Nivel 1 (vencimiento) y Nivel 2 (estancamiento)."""

from __future__ import annotations

import pandas as pd


UMBRAL_NIVEL_1_DIAS = 30
UMBRAL_NIVEL_2_DIAS = 15


def calcular_alertas(df: pd.DataFrame) -> pd.DataFrame:
    """Marca alertas sin alterar reglas de negocio de niveles."""

    data = df.copy()

    data["alerta_nivel_1"] = (
        ~data["es_cierre"]
        & (data["dias_sin_mov"] >= UMBRAL_NIVEL_1_DIAS)
    )
    data["alerta_nivel_2"] = (
        ~data["es_cierre"]
        & (data["dias_sin_mov"] >= UMBRAL_NIVEL_2_DIAS)
    )

    data["alerta"] = "Sin alerta"
    data.loc[data["alerta_nivel_2"], "alerta"] = "Nivel 2 - Estancamiento"
    data.loc[data["alerta_nivel_1"], "alerta"] = "Nivel 1 - Vencimiento"

    return data
