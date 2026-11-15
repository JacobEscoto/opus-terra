"""Pruebas de carga y control de calidad del NDVI de MOD13C2."""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from opusterra.mod13c2 import (
    mascara_confiable,
    mes_de_archivo,
    resumen_calidad,
)


def _calidad(modland: int, utilidad: int, tierra: int) -> int:
    """Construye un campo de bits `ndvi_quality` con los bloques indicados."""

    return modland | (utilidad << 2) | (tierra << 11)


def _cubo(ndvi, fiabilidad, calidad) -> xr.Dataset:
    """Arma un cubo mínimo con las tres variables de MOD13C2."""

    forma = (len(ndvi), 1, 1)
    return xr.Dataset(
        {
            "ndvi": (("time", "lat", "lon"), np.asarray(ndvi, dtype=float).reshape(forma)),
            "ndvi_reliability": (
                ("time", "lat", "lon"),
                np.asarray(fiabilidad, dtype=float).reshape(forma),
            ),
            "ndvi_quality": (
                ("time", "lat", "lon"),
                np.asarray(calidad, dtype=float).reshape(forma),
            ),
        },
        coords={
            "time": pd.date_range("2001-01-01", periods=forma[0], freq="MS"),
            "lat": [15.0],
            "lon": [-86.0],
        },
    )


def test_mes_de_archivo_usa_el_dia_del_ano() -> None:
    """El nombre del archivo MOD13C2 determina su mes calendario."""

    assert mes_de_archivo("MOD13C2.A2000032.061.2020042083108.nc") == pd.Period("2000-02", freq="M")
    assert mes_de_archivo("MOD13C2.A2025273.061.2026301132433.nc") == pd.Period("2025-09", freq="M")
    with pytest.raises(ValueError, match="MOD13C2"):
        mes_de_archivo("no-es-un-archivo.nc")


def test_mascara_acepta_solo_calidad_confiable() -> None:
    """Cada estado no confiable de la documentación se descarta."""

    ndvi = [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, np.nan]
    fiabilidad = [0, 1, 2, 3, 4, 0, 0, 0]
    calidad = [
        _calidad(0, 0, 1),   # buena
        _calidad(1, 9, 1),   # marginal, revisable
        _calidad(0, 0, 1),   # fiabilidad 2: nieve/hielo
        _calidad(0, 0, 1),   # fiabilidad 3: nuboso
        _calidad(0, 0, 1),   # fiabilidad 4: estimado del histórico
        _calidad(2, 0, 1),   # MODLAND_QA 10: probablemente nuboso
        _calidad(0, 12, 1),  # utilidad 1100: interpolado, no real
        _calidad(0, 0, 1),   # NDVI no producido
    ]
    cubo = _cubo(ndvi, fiabilidad, calidad)

    mascara, conteos = mascara_confiable(cubo)

    assert mascara[:, 0, 0].tolist() == [True, True, False, False, False, False, False, False]
    assert conteos["celda_meses_validos"] == 2
    assert conteos["celda_meses_excluidos"] == 6


def test_mascara_descarta_celdas_que_no_son_tierra() -> None:
    """La bandera tierra/agua del propio producto define qué es vegetación."""

    ndvi = [0.4, 0.4]
    fiabilidad = [0, 0]
    calidad = [_calidad(0, 0, 1), _calidad(0, 0, 7)]
    cubo = _cubo(ndvi, fiabilidad, calidad)

    mascara, conteos = mascara_confiable(cubo)

    assert mascara[:, 0, 0].tolist() == [True, False]
    assert conteos["no_vegetacion_tierra"] == 1


def test_resumen_calidad_cuenta_celdas_y_meses_excluidos() -> None:
    """El resumen informa celdas conservadas, meses afectados y exclusiones."""

    mascara = np.array([[[True, True]], [[True, False]], [[True, False]]])
    conteos = {
        "ndvi_no_producido": 1,
        "fiabilidad_no_confiable": 1,
        "modland_no_confiable": 1,
        "utilidad_inservible": 1,
        "no_vegetacion_tierra": 1,
        "celda_meses_excluidos": 2,
        "celda_meses_validos": 4,
    }
    tiempos = pd.DatetimeIndex(["2001-01-01", "2001-02-01", "2001-03-01"])

    resumen = resumen_calidad(mascara, conteos, tiempos)

    assert resumen["celdas_malla"] == 2
    assert resumen["celdas_conservadas"] == 1
    assert resumen["celdas_excluidas"] == 1
    assert resumen["celda_meses_excluidos"] == 2
    assert resumen["meses_afectados"] == 2
    assert resumen["meses_totales"] == 3
