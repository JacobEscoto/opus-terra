"""Pruebas de tendencias contra implementaciones de referencia."""

import numpy as np
import pymannkendall as mk
import pytest
from scipy.stats import theilslopes

from opusterra.tendencia import fdr_benjamini_hochberg, mann_kendall, pendiente_sen


@pytest.mark.parametrize(
    ("serie", "direccion"),
    [
        (np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0]), "creciente"),
        (np.array([6.0, 5.0, 4.0, 3.0, 2.0, 1.0]), "decreciente"),
        (np.array([2.0, 1.0, 2.0, 1.0, 2.0, 1.0]), "sin tendencia"),
    ],
)
def test_mann_kendall_coincide_con_pymannkendall(serie, direccion) -> None:
    """El estadístico y p-valor coinciden con la referencia externa."""

    estadistico, p_valor, resultado_direccion = mann_kendall(serie)
    referencia = mk.original_test(serie)

    assert estadistico == pytest.approx(referencia.z)
    assert p_valor == pytest.approx(referencia.p)
    assert resultado_direccion == direccion


def test_mann_kendall_rechaza_nan_y_matrices() -> None:
    """La prueba exige una serie 1D completa."""

    with pytest.raises(ValueError, match="NaN"):
        mann_kendall([1.0, np.nan, 3.0])
    with pytest.raises(ValueError, match="1D"):
        mann_kendall(np.ones((2, 3)))


def test_pendiente_sen_coincide_con_scipy() -> None:
    """La pendiente e intercepto coinciden con scipy.stats.theilslopes."""

    serie = np.array([4.2, 5.0, 7.8, 8.1, 11.6, 12.0])
    pendiente, intercepto = pendiente_sen(serie)
    referencia = theilslopes(serie, np.arange(serie.size, dtype=float))

    assert pendiente == pytest.approx(referencia.slope)
    assert intercepto == pytest.approx(referencia.intercept)


def test_fdr_benjamini_hochberg_coincide_con_calculo_manual() -> None:
    """La máscara usa el mayor rango que cumple el umbral BH."""

    pvalores = np.array([0.001, 0.009, 0.02, 0.04, 0.2, np.nan])
    resultado = fdr_benjamini_hochberg(pvalores, alfa=0.05)

    # Ordenados: .001 <= .01, .009 <= .02, .02 <= .03 y .04 <= .04.
    # Los cuatro primeros cumplen el umbral BH.
    np.testing.assert_array_equal(resultado, [True, True, True, True, False, False])


def test_fdr_benjamini_hochberg_valida_entradas() -> None:
    """Los p-valores y alfa deben estar en sus rangos estadísticos."""

    with pytest.raises(ValueError, match="entre 0 y 1"):
        fdr_benjamini_hochberg([0.1, 1.2])
    with pytest.raises(ValueError, match="alfa"):
        fdr_benjamini_hochberg([0.1], alfa=1.1)
