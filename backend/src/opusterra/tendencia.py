"""Pruebas de tendencia para series temporales climáticas."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy.stats import theilslopes


def _serie_numerica(serie: Sequence[float] | np.ndarray) -> np.ndarray:
    """Convierte una serie a un vector numérico y valida sus valores."""

    valores = np.asarray(serie, dtype=float)
    if valores.ndim != 1:
        raise ValueError("La serie debe ser un vector 1D")
    if valores.size < 3:
        raise ValueError("La serie debe tener al menos tres observaciones")
    if not np.isfinite(valores).all():
        raise ValueError("La serie no puede contener NaN ni valores infinitos")
    return valores


def mann_kendall(
    serie: Sequence[float] | np.ndarray,
) -> tuple[float, float, str]:
    """Aplica Mann-Kendall y devuelve `(estadístico, p_valor, dirección)`.

    El estadístico devuelto es ``z`` (la estadística normalizada de
    ``pymannkendall.original_test``). La dirección se determina con la prueba:
    ``creciente``, ``decreciente`` o ``sin tendencia``.
    """

    valores = _serie_numerica(serie)
    try:
        import pymannkendall as mk
    except ImportError as exc:  # pragma: no cover - la dependencia es de desarrollo
        raise ImportError(
            "Falta pymannkendall; instálalo con 'uv add --dev pymannkendall'"
        ) from exc

    resultado = mk.original_test(valores)
    direccion = {
        "increasing": "creciente",
        "decreasing": "decreciente",
        "no trend": "sin tendencia",
    }.get(resultado.trend, resultado.trend)
    return float(resultado.z), float(resultado.p), direccion


def pendiente_sen(
    serie: Sequence[float] | np.ndarray,
) -> tuple[float, float]:
    """Devuelve la pendiente de Theil-Sen y su intercepto.

    El eje temporal es el índice de observación ``0, 1, ...``. Si la serie es
    anual, la pendiente queda expresada en unidades por año.
    """

    valores = _serie_numerica(serie)
    tiempo = np.arange(valores.size, dtype=float)
    resultado = theilslopes(valores, tiempo)
    return float(resultado.slope), float(resultado.intercept)


def fdr_benjamini_hochberg(
    pvalores: Sequence[float] | np.ndarray,
    alfa: float = 0.05,
) -> np.ndarray:
    """Devuelve la máscara de p-valores significativos con FDR de BH.

    Los p-valores se ordenan de menor a mayor y se compara cada uno con
    ``alfa * rango / número_de_pruebas``. Se usa el mayor rango que cumple la
    condición, como define Benjamini-Hochberg.
    """

    valores = np.asarray(pvalores, dtype=float)
    if valores.ndim != 1:
        raise ValueError("Los p-valores deben ser un vector 1D")
    if not 0 <= alfa <= 1:
        raise ValueError("alfa debe estar entre 0 y 1")
    validos = np.isfinite(valores)
    if np.any((valores[validos] < 0) | (valores[validos] > 1)):
        raise ValueError("Los p-valores deben estar entre 0 y 1")

    mascara = np.zeros(valores.shape, dtype=bool)
    indices = np.flatnonzero(validos)
    if indices.size == 0:
        return mascara
    orden = indices[np.argsort(valores[indices], kind="stable")]
    umbrales = alfa * np.arange(1, indices.size + 1) / indices.size
    cumple = valores[orden] <= umbrales
    if np.any(cumple):
        ultimo = np.flatnonzero(cumple)[-1]
        # Se incluyen también empates con el p-valor de corte.
        corte = valores[orden[ultimo]]
        mascara[validos & (valores <= corte)] = True
    return mascara
