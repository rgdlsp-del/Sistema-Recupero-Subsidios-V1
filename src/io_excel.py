"""Funciones de entrada/salida para carga de Excel y validaciones."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

import pandas as pd

INTERNAL_COLUMNS = {
    "id": "id",
    "fecha_registro": "fecha_registro",
    "fecha_ultimo_mov": "fecha_ultimo_mov",
    "estado": "estado",
    "subestado": "subestado",
    "agente": "agente",
    "monto": "monto",
}

REQUIRED_EXCEL_COLUMNS = (
    "DNI",
    "TIPO DE SUBSIDIO",
    "FECHA DE INICIO",
    "FECHA FIN",
    "STATUS PLATAFORMA VIVA",
)


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validación de columnas requeridas."""

    is_valid: bool
    missing_columns: tuple[str, ...] = ()


def _normalizar_header(col: object) -> str:
    """Normaliza un nombre de columna según formato esperado del Excel fuente."""

    texto = str(col).replace('"', "").strip().upper()
    return re.sub(r"\s+", " ", texto)


def normalizar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres para facilitar mapeo de columnas entre archivos."""

    df = df.copy()
    df.columns = [_normalizar_header(col) for col in df.columns]
    return df


def validar_columnas(df: pd.DataFrame, required_columns: Iterable[str] | None = None) -> ValidationResult:
    """Valida que existan columnas obligatorias del Excel fuente."""

    requeridas = tuple(required_columns or REQUIRED_EXCEL_COLUMNS)
    faltantes = tuple(col for col in requeridas if col not in df.columns)
    return ValidationResult(is_valid=not faltantes, missing_columns=faltantes)


def _serie_texto(df: pd.DataFrame, col: str) -> pd.Series:
    """Obtiene una serie de texto limpia o vacía si la columna no existe."""

    if col not in df.columns:
        return pd.Series("", index=df.index, dtype="object")
    return df[col].fillna("").astype(str).str.strip()


def _coalesce_fecha(data: pd.DataFrame, columnas: tuple[str, ...]) -> pd.Series:
    """Retorna la primera fecha disponible por fila entre columnas candidatas."""

    acumulada = pd.Series(pd.NaT, index=data.index, dtype="datetime64[ns]")
    for col in columnas:
        if col in data.columns:
            candidata = pd.to_datetime(data[col], errors="coerce")
            acumulada = acumulada.fillna(candidata)
    return acumulada


def _coalesce_monto(data: pd.DataFrame, columnas: tuple[str, ...]) -> pd.Series:
    """Retorna el primer monto numérico disponible por fila entre columnas candidatas."""

    acumulado = pd.Series(pd.NA, index=data.index, dtype="Float64")
    for col in columnas:
        if col in data.columns:
            candidato = pd.to_numeric(data[col], errors="coerce")
            acumulado = acumulado.fillna(candidato)
    return acumulado.fillna(0).astype(float)


def _crear_id(data: pd.DataFrame) -> pd.Series:
    """Crea ID interno cuando no existe en el archivo fuente."""

    if "ID" in data.columns:
        return _serie_texto(data, "ID")

    partes = [
        _serie_texto(data, "DNI"),
        _serie_texto(data, "TIPO DE SUBSIDIO"),
        _serie_texto(data, "FECHA DE INICIO"),
        _serie_texto(data, "FECHA FIN"),
    ]
    return partes[0] + "|" + partes[1] + "|" + partes[2] + "|" + partes[3]


def cargar_excel(file) -> pd.DataFrame:
    """Carga archivo Excel real, valida cabeceras y crea columnas internas."""

    df = pd.read_excel(file, engine="openpyxl")
    df = normalizar_nombres_columnas(df)

    validacion = validar_columnas(df)
    if not validacion.is_valid:
        faltantes = ", ".join(validacion.missing_columns)
        raise ValueError(f"Faltan columnas requeridas del Excel: {faltantes}")

    data = df.copy()
    data["id"] = _crear_id(df)
    data["estado"] = _serie_texto(df, "STATUS PLATAFORMA VIVA")
    data["subestado"] = _serie_texto(df, "STATUS EBE")
    data["agente"] = _serie_texto(df, "TRABAJADORA SOCIAL")
    data["fecha_registro"] = pd.to_datetime(df.get("FECHA DE INICIO"), errors="coerce")
    data["fecha_ultimo_mov"] = _coalesce_fecha(
        df,
        ("FECHA ULTIMA ACCION", "FECHA DE PRESENTACIÓN A ESSALUD", "FECHA FIN"),
    )
    data["monto"] = _coalesce_monto(df, ("IMPORTE PAGADO PLANILLA", "IMPORTE SOLICITADO"))

    # Asegura presencia de columnas internas esperadas por la app.
    for col in INTERNAL_COLUMNS.values():
        if col not in data.columns:
            data[col] = "" if col in {"id", "estado", "subestado", "agente"} else pd.NA

    return data
