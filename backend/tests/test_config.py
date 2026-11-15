"""Pruebas de la configuración y conversiones del backend."""

from datetime import date

import numpy as np

from opusterra.config import (
    HONDURAS_BBOX,
    PERIODO_COMUN,
    PERIODO_GPM,
    PERIODO_NDVI,
    dias_en_mes,
    kelvin_a_celsius,
    kgm2s_a_mm_mes,
    ndvi_desde_raw,
    segundos_en_mes,
)


def test_dias_en_mes_responde_a_anos_bisiestos_y_meses() -> None:
    assert dias_en_mes(2000, 2) == 29
    assert dias_en_mes(1900, 2) == 28
    assert dias_en_mes(2024, 2) == 29
    assert dias_en_mes(2000, 1) == 31
    assert dias_en_mes(2000, 4) == 30


def test_segundos_en_mes_usa_dias_reales() -> None:
    assert segundos_en_mes(2000, 1) == 31 * 86400


def test_kgm2s_a_mm_mes_usa_febrero_de_28_dias() -> None:
    assert kgm2s_a_mm_mes(1e-5, 2001, 2) == 1e-5 * 28 * 86400


def test_kelvin_a_celsius() -> None:
    assert kelvin_a_celsius(273.15) == 0.0
    assert np.isclose(kelvin_a_celsius(300.0), 26.85)


def test_ndvi_desde_raw_escala_y_relleno() -> None:
    assert np.isnan(ndvi_desde_raw(-3000))
    assert ndvi_desde_raw(10000) == 1.0
    assert ndvi_desde_raw(0) == 0.0
    assert ndvi_desde_raw(5000) == 0.5

    resultado = ndvi_desde_raw(np.array([-3000, 0, 5000, 10000, np.nan]))
    esperado = np.array([np.nan, 0.0, 0.5, 1.0, np.nan])
    np.testing.assert_allclose(resultado, esperado, equal_nan=True)


def test_periodos_son_fechas_validas_y_comun_esta_contenido() -> None:
    for periodo in (PERIODO_GPM, PERIODO_NDVI, PERIODO_COMUN):
        assert all(isinstance(valor, date) for valor in periodo)
        assert periodo[0] <= periodo[1]

    assert PERIODO_GPM[0] <= PERIODO_COMUN[0]
    assert PERIODO_COMUN[1] <= PERIODO_GPM[1]
    assert PERIODO_NDVI[0] <= PERIODO_COMUN[0]
    assert PERIODO_COMUN[1] <= PERIODO_NDVI[1]


def test_bounding_box_es_valido_para_honduras() -> None:
    lon_min, lat_min, lon_max, lat_max = HONDURAS_BBOX
    assert lon_min < lon_max
    assert lat_min < lat_max
    assert -90 < lon_min < -83
    assert -90 < lon_max < -83
    assert 12 < lat_min < 17
    assert 12 < lat_max < 17
