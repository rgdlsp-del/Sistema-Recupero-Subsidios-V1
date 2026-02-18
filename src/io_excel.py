"""Funciones de entrada/salida para carga de Excel y validaciones."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

REQUIRED_COLUMNS = {
    "id": "id",
    "fecha_registro": "fecha_registro",
    "fecha_ultimo_mov": "fecha_ultimo_mov",
    "estado": "estado",
    "subestado": "subestado",
    "agente": "agente",
    "monto": "monto",
}


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validación de columnas requeridas."""

    is_valid: bool
    missing_columns: tuple[str, ...] = ()


def normalizar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres para facilitar mapeo de columnas entre archivos."""

    normalizadas = [
        str(col)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace(" ", "_")
        for col in df.columns
    ]
    df = df.copy()
    df.columns = normalizadas
    return df


def validar_columnas(df: pd.DataFrame, required_columns: Iterable[str] | None = None) -> ValidationResult:
    """Valida que existan columnas obligatorias."""

    requeridas = tuple(required_columns or REQUIRED_COLUMNS.values())
    faltantes = tuple(col for col in requeridas if col not in df.columns)
    return ValidationResult(is_valid=not faltantes, missing_columns=faltantes)


def cargar_excel(file) -> pd.DataFrame:
    """Carga archivo Excel, normaliza columnas y tipa campos básicos."""

    df = pd.read_excel(file, engine="openpyxl")
    df = normalizar_nombres_columnas(df)

    validacion = validar_columnas(df)
    if not validacion.is_valid:
        faltantes = ", ".join(validacion.missing_columns)
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    for col_fecha in ("fecha_registro", "fecha_ultimo_mov"):
        df[col_fecha] = pd.to_datetime(df[col_fecha], errors="coerce")

    df["estado"] = df["estado"].astype(str).str.strip()
    df["subestado"] = df["subestado"].astype(str).str.strip()
    df["agente"] = df["agente"].astype(str).str.strip()
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
    return df
