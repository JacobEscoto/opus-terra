"""Configuración y conversiones para el análisis climático."""

from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date

import numpy as np

# Orden: (longitud mínima, latitud mínima, longitud máxima, latitud máxima).
HONDURAS_BBOX: tuple[float, float, float, float] = (-89.4, 12.9, -83.1, 16.6)

PERIODO_MERRA2: tuple[date, date] = (date(1996, 1, 1), date(2026, 9, 1))
PERIODO_GPM: tuple[date, date] = (date(1998, 1, 1), date(2025, 9, 1))
PERIODO_NDVI: tuple[date, date] = (date(2000, 2, 1), date(2026, 9, 1))
PERIODO_COMUN: tuple[date, date] = (date(2000, 2, 1), date(2025, 9, 1))

GRID_RES_LAT = 0.5
GRID_RES_LON = 0.625

KELVIN_TO_CELSIUS_OFFSET = 273.15
NDVI_SCALE = 10000.0
NDVI_FILL_VALUE = -3000
NDVI_VALID_RANGE_RAW: tuple[int, int] = (-2000, 10000)

# El índice Niño 3.4 procede de NOAA/KNMI; no es un dato de NASA.
FUENTE_NINO_34 = "NOAA/KNMI"

# La unidad mensual de GPM suele ser mm/hr, pero debe confirmarse al abrir el
# archivo antes de aplicar esta conversión.
GPM_UNIDAD_DOCUMENTADA = "mm/hr (confirmar en el archivo)"
HORAS_POR_DIA = 24


@dataclass(frozen=True)
class NombresVariables:
    """Nombres de variables usados por cada fuente de datos."""

    merra2_temperatura: str = "T2M"
    merra2_precipitacion: str = "PRECTOTCORR"
    gpm_precipitacion: str = "precipitation"
    ndvi: str = "NDVI"


NOMBRES_VARIABLES = NombresVariables()


def dias_en_mes(year: int, month: int) -> int:
    """Devuelve el número real de días del mes indicado."""

    return monthrange(year, month)[1]


def segundos_en_mes(year: int, month: int) -> int:
    """Devuelve los segundos del mes, respetando años bisiestos."""

    return dias_en_mes(year, month) * 86400


def kgm2s_a_mm_mes(
    valor: float | np.ndarray, year: int, month: int
) -> float | np.ndarray:
    """Convierte kg m⁻² s⁻¹ a mm acumulados del mes real."""

    convertido = np.asarray(valor) * segundos_en_mes(year, month)
    return convertido.item() if convertido.ndim == 0 else convertido


def gpm_mm_h_a_mm_mes(
    valor: float | np.ndarray, year: int, month: int
) -> float | np.ndarray:
    """Convierte mm/h a mm/mes, si el archivo confirma esa unidad."""

    convertido = np.asarray(valor) * dias_en_mes(year, month) * HORAS_POR_DIA
    return convertido.item() if convertido.ndim == 0 else convertido


def kelvin_a_celsius(valor: float | np.ndarray) -> float | np.ndarray:
    """Convierte temperaturas de Kelvin a grados Celsius."""

    convertido = np.asarray(valor) - KELVIN_TO_CELSIUS_OFFSET
    return convertido.item() if convertido.ndim == 0 else convertido


def ndvi_desde_raw(valor_raw: float | np.ndarray) -> np.ndarray:
    """Escala NDVI crudo y convierte su valor de relleno en NaN."""

    valores = np.asarray(valor_raw, dtype=float)
    valores = np.where(valores == NDVI_FILL_VALUE, np.nan, valores)
    return valores / NDVI_SCALE
