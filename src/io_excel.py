"""Funciones de entrada/salida para carga de Excel y validaciones."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

import pandas as pd

CORE_REQUIRED_COLUMNS = (
    "DNI",
    "APELLIDOS Y NOMBRES",
    "FECHA DE INICIO",
    "FECHA FIN",
    "VENCIMIENTO DE EXPEDIENTE",
    "STATUS PLATAFORMA VIVA",
)

OPTIONAL_GESTION_COLUMNS = (
    "EMPRESA",
    "TIPO DE SUBSIDIO",
    "TOTAL DIAS",
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
)


@dataclass(frozen=True)
class ValidationResult:
    """Resultado de validación de columnas del Excel fuente."""

    is_valid: bool
    missing_columns: tuple[str, ...] = ()


def _normalizar_header(col: object) -> str:
    """Normaliza nombre de columna para validación sin alterar UI."""

    texto = str(col).replace('"', "").strip().upper()
    return re.sub(r"\s+", " ", texto)


def _build_normalized_map(columns: Iterable[object]) -> dict[str, str]:
    """Mapea cabecera normalizada -> cabecera original."""

    mapping: dict[str, str] = {}
    for col in columns:
        mapping[_normalizar_header(col)] = str(col)
    return mapping


def validar_columnas(columnas: Iterable[object], required_columns: Iterable[str]) -> ValidationResult:
    """Valida que existan columnas obligatorias según cabeceras origen."""

    mapping = _build_normalized_map(columnas)
    faltantes = tuple(col for col in required_columns if _normalizar_header(col) not in mapping)
    return ValidationResult(is_valid=not faltantes, missing_columns=faltantes)


def obtener_columnas_faltantes_opcionales(columnas: Iterable[object]) -> tuple[str, ...]:
    """Retorna columnas opcionales de gestión no presentes en el archivo."""

    mapping = _build_normalized_map(columnas)
    return tuple(col for col in OPTIONAL_GESTION_COLUMNS if _normalizar_header(col) not in mapping)


def _serie_texto(data: pd.DataFrame, mapping: dict[str, str], col_norm: str) -> pd.Series:
    """Obtiene serie de texto limpia usando columna normalizada."""

    original = mapping.get(col_norm)
    if not original or original not in data.columns:
        return pd.Series("", index=data.index, dtype="object")
    return data[original].fillna("").astype(str).str.strip()


def _coalesce_fecha(data: pd.DataFrame, mapping: dict[str, str], columnas_norm: tuple[str, ...]) -> pd.Series:
    """Retorna la primera fecha disponible por fila entre columnas candidatas."""

    acumulada = pd.Series(pd.NaT, index=data.index, dtype="datetime64[ns]")
    for col_norm in columnas_norm:
        original = mapping.get(col_norm)
        if original and original in data.columns:
            candidata = pd.to_datetime(data[original], errors="coerce")
            acumulada = acumulada.fillna(candidata)
    return acumulada


def _coalesce_monto(data: pd.DataFrame, mapping: dict[str, str], columnas_norm: tuple[str, ...]) -> pd.Series:
    """Retorna el primer monto numérico disponible por fila entre columnas candidatas."""

    acumulado = pd.Series(pd.NA, index=data.index, dtype="Float64")
    for col_norm in columnas_norm:
        original = mapping.get(col_norm)
        if original and original in data.columns:
            candidato = pd.to_numeric(data[original], errors="coerce")
            acumulado = acumulado.fillna(candidato)
    return acumulado.fillna(0).astype(float)


def _crear_id(data: pd.DataFrame, mapping: dict[str, str]) -> pd.Series:
    """Crea ID interno sin exponerlo en UI."""

    id_original = mapping.get("ID")
    if id_original and id_original in data.columns:
        return _serie_texto(data, mapping, "ID")

    partes = [
        _serie_texto(data, mapping, "DNI"),
        _serie_texto(data, mapping, "TIPO DE SUBSIDIO"),
        _serie_texto(data, mapping, "FECHA DE INICIO"),
        _serie_texto(data, mapping, "FECHA FIN"),
    ]
    return partes[0] + "|" + partes[1] + "|" + partes[2] + "|" + partes[3]


def cargar_excel(file) -> tuple[pd.DataFrame, tuple[str, ...]]:
    """Carga Excel de gestión y agrega columnas técnicas para reglas internas."""

    data = pd.read_excel(file, engine="openpyxl")
    mapping = _build_normalized_map(data.columns)

    validacion = validar_columnas(data.columns, CORE_REQUIRED_COLUMNS)
    if not validacion.is_valid:
        faltantes = ", ".join(validacion.missing_columns)
        raise ValueError(f"Faltan columnas mínimas requeridas del Excel: {faltantes}")

    data = data.copy()
    data["id"] = _crear_id(data, mapping)
    data["estado"] = _serie_texto(data, mapping, "STATUS PLATAFORMA VIVA")
    data["subestado"] = _serie_texto(data, mapping, "STATUS EBE")
    data["agente"] = _serie_texto(data, mapping, "TRABAJADORA SOCIAL")
    data["fecha_registro"] = _coalesce_fecha(data, mapping, ("FECHA DE INICIO",))
    data["fecha_ultimo_mov"] = _coalesce_fecha(
        data,
        mapping,
        ("FECHA ULTIMA ACCION", "FECHA DE PRESENTACIÓN A ESSALUD", "FECHA FIN"),
    )
    data["monto"] = _coalesce_monto(data, mapping, ("IMPORTE PAGADO PLANILLA", "IMPORTE SOLICITADO"))

    faltantes_opcionales = obtener_columnas_faltantes_opcionales(data.columns)
    return data, faltantes_opcionales
