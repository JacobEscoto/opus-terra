"""Pruebas de carga y preparación de MERRA-2 con datos sintéticos pequeños."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from opusterra.merra2 import (
    anomalias_mensuales,
    cargar_merra2,
    precipitacion_mm_mes,
    promedio_regional,
    t2m_celsius,
)

LATITUDES = np.array([13.0, 14.0, 15.0])
LONGITUDES = np.array([-88.0, -86.5])


def _mesh(valor: float = 1.0) -> np.ndarray:
    """Malla sintética mensual de 1x3x2 con un valor constante."""

    return np.full((1, len(LATITUDES), len(LONGITUDES)), valor, dtype=float)


def _escribir_mes(
    carpeta: Path,
    nombre: str,
    fecha: str,
    valores: np.ndarray,
    variable: str = "PRECTOTCORR",
    unidades: str = "kg m-2 s-1",
) -> Path:
    """Escribe un NetCDF mensual sintético de una variable."""

    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / nombre
    dataset = xr.Dataset(
        {variable: (("time", "lat", "lon"), valores)},
        coords={
            "time": np.array([np.datetime64(fecha, "ns")]),
            "lat": LATITUDES,
            "lon": LONGITUDES,
        },
    )
    dataset[variable].attrs = {"units": unidades, "long_name": "sintético"}
    dataset.to_netcdf(ruta, engine="netcdf4")
    return ruta


def _serie_mensual(fechas: pd.DatetimeIndex, valores: np.ndarray) -> xr.DataArray:
    """Construye un DataArray mensual sintético."""

    return xr.DataArray(
        valores,
        dims=("time", "lat", "lon"),
        coords={"time": fechas, "lat": LATITUDES, "lon": LONGITUDES},
        name="PRECTOTCORR",
    )


# --- Conversiones ------------------------------------------------------------


def test_precipitacion_mm_mes_usa_febrero_de_29_dias() -> None:
    """Febrero de un año bisiesto se convierte con 29 días reales."""

    ds = xr.Dataset(
        {"PRECTOTCORR": (("time", "lat", "lon"), _mesh(1e-5))},
        coords={
            "time": np.array([np.datetime64("2024-02-01", "ns")]),
            "lat": LATITUDES,
            "lon": LONGITUDES,
        },
    )
    ds["PRECTOTCORR"].attrs = {"units": "kg m-2 s-1", "long_name": "total_precipitation"}

    resultado = precipitacion_mm_mes(ds)

    esperado = 1e-5 * 29 * 86400
    assert float(resultado["PRECTOTCORR"].values[0, 0, 0]) == pytest.approx(esperado)
    assert resultado["PRECTOTCORR"].attrs["units"] == "mm/mes"
    assert resultado["PRECTOTCORR"].attrs["units_original"] == "kg m-2 s-1"
    # Los atributos originales se conservan.
    assert resultado["PRECTOTCORR"].attrs["long_name"] == "total_precipitation"


def test_precipitacion_mm_mes_usa_mes_de_31_dias() -> None:
    """Un mes de 31 días se convierte con 31 días reales."""

    ds = xr.Dataset(
        {"PRECTOTCORR": (("time", "lat", "lon"), _mesh(1e-5))},
        coords={
            "time": np.array([np.datetime64("2023-01-01", "ns")]),
            "lat": LATITUDES,
            "lon": LONGITUDES,
        },
    )

    resultado = precipitacion_mm_mes(ds)

    esperado = 1e-5 * 31 * 86400
    assert float(resultado["PRECTOTCORR"].values[0, 0, 0]) == pytest.approx(esperado)


def test_precipitacion_mm_mes_usa_febrero_de_28_dias() -> None:
    """Febrero de un año no bisiesto usa 28 días."""

    ds = xr.Dataset(
        {"PRECTOTCORR": (("time", "lat", "lon"), _mesh(1e-5))},
        coords={
            "time": np.array([np.datetime64("2023-02-01", "ns")]),
            "lat": LATITUDES,
            "lon": LONGITUDES,
        },
    )

    resultado = precipitacion_mm_mes(ds)

    assert float(resultado["PRECTOTCORR"].values[0, 0, 0]) == pytest.approx(1e-5 * 28 * 86400)


def test_precipitacion_mm_mes_convierte_cada_mes_con_su_duracion() -> None:
    """Cada mes del cubo usa su propia cantidad de días."""

    fechas = pd.to_datetime(["2024-01-01", "2024-02-01", "2024-04-01"])
    valores = np.full((3, len(LATITUDES), len(LONGITUDES)), 1e-5)
    ds = xr.Dataset(
        {"PRECTOTCORR": (("time", "lat", "lon"), valores)},
        coords={"time": np.array(fechas.values, dtype="datetime64[ns]"), "lat": LATITUDES, "lon": LONGITUDES},
    )

    resultado = precipitacion_mm_mes(ds)

    for indice, dias in enumerate((31, 29, 30)):
        esperado = 1e-5 * dias * 86400
        assert float(resultado["PRECTOTCORR"].values[indice, 0, 0]) == pytest.approx(esperado)


def test_t2m_celsius_convierte_kelvin() -> None:
    """T2M pasa de Kelvin a grados Celsius."""

    ds = xr.Dataset(
        {"T2M": (("time", "lat", "lon"), _mesh(300.0))},
        coords={
            "time": np.array([np.datetime64("2020-01-01", "ns")]),
            "lat": LATITUDES,
            "lon": LONGITUDES,
        },
    )
    ds["T2M"].attrs = {"units": "K", "long_name": "2-meter_air_temperature"}

    resultado = t2m_celsius(ds)

    assert float(resultado["T2M"].values[0, 0, 0]) == pytest.approx(26.85)
    assert resultado["T2M"].attrs["units"] == "degC"
    assert resultado["T2M"].attrs["long_name"] == "2-meter_air_temperature"


# --- Anomalías ---------------------------------------------------------------


def test_anomalias_mensuales_tienen_media_cero_en_cada_mes() -> None:
    """La anomalía mensual promedia cero dentro de cada mes calendario."""

    fechas = pd.date_range("2000-01-01", periods=36, freq="MS")
    ciclo = 20.0 + 5.0 * np.sin(2 * np.pi * (fechas.month - 1) / 12)
    valores = (
        ciclo.to_numpy()[:, None, None]
        + np.array([0.0, 1.0, 2.0])[None, :, None]
        + np.array([0.0, 2.0])[None, None, :]
    )
    serie = _serie_mensual(fechas, valores)

    climatologia, anomalia = anomalias_mensuales(serie)

    assert climatologia.sizes["mes"] == 12
    assert anomalia.sizes["time"] == 36
    medias = anomalia.groupby("time.month").mean("time")
    assert np.allclose(medias.values, 0.0, atol=1e-12)


def test_anomalias_mensuales_conservan_el_ciclo_de_la_climatologia() -> None:
    """La climatología reproduce el ciclo anual de la serie."""

    fechas = pd.date_range("2000-01-01", periods=24, freq="MS")
    ciclo = 20.0 + 5.0 * np.sin(2 * np.pi * (fechas.month - 1) / 12)
    valores = ciclo.to_numpy()[:, None, None] + np.arange(6.0).reshape(3, 2)
    serie = _serie_mensual(fechas, valores)

    climatologia, _ = anomalias_mensuales(serie)

    for mes in range(1, 13):
        esperado = 20.0 + 5.0 * np.sin(2 * np.pi * (mes - 1) / 12)
        assert float(climatologia.sel(mes=mes).values[0, 0]) == pytest.approx(esperado)


# --- Cobertura temporal ------------------------------------------------------


def test_cargar_merra2_falla_con_mes_faltante(tmp_path: Path) -> None:
    """Un hueco temporal dentro del rango produce un error claro."""

    carpeta = tmp_path / "merra2_flx"
    for mes in ("202001", "202002", "202004"):
        _escribir_mes(carpeta, f"merra_{mes}.nc", f"{mes[:4]}-{mes[4:]}-01", _mesh())

    with pytest.raises(ValueError) as error:
        cargar_merra2(carpeta, ["PRECTOTCORR"])

    mensaje = str(error.value)
    assert "faltan meses" in mensaje
    assert "2020-03" in mensaje


def test_cargar_merra2_falla_con_mes_duplicado(tmp_path: Path) -> None:
    """Un mes repetido produce un error claro."""

    carpeta = tmp_path / "merra2_flx"
    _escribir_mes(carpeta, "merra_202001.nc", "2020-01-01", _mesh())
    _escribir_mes(carpeta, "merra_202002a.nc", "2020-02-01", _mesh())
    _escribir_mes(carpeta, "merra_202002b.nc", "2020-02-01", _mesh(2.0))
    _escribir_mes(carpeta, "merra_202003.nc", "2020-03-01", _mesh())

    with pytest.raises(ValueError) as error:
        cargar_merra2(carpeta, ["PRECTOTCORR"])

    mensaje = str(error.value)
    assert "duplicados" in mensaje
    assert "2020-02" in mensaje


def test_cargar_merra2_ordena_por_fecha(tmp_path: Path) -> None:
    """El cubo se entrega ordenado cronológicamente."""

    carpeta = tmp_path / "merra2_flx"
    _escribir_mes(carpeta, "merra_202002.nc", "2020-02-01", _mesh(2.0))
    _escribir_mes(carpeta, "merra_202001.nc", "2020-01-01", _mesh(1.0))
    _escribir_mes(carpeta, "merra_202003.nc", "2020-03-01", _mesh(3.0))

    ds = cargar_merra2(carpeta, ["PRECTOTCORR"])

    assert ds.sizes["time"] == 3
    assert ds["time"].values[0] < ds["time"].values[1] < ds["time"].values[2]
    assert float(ds["PRECTOTCORR"].values[0, 0, 0]) == pytest.approx(1.0)
    assert float(ds["PRECTOTCORR"].values[2, 0, 0]) == pytest.approx(3.0)


def test_cargar_merra2_ignora_merra2_legacy(tmp_path: Path) -> None:
    """La carpeta `merra2_legacy` no se lee."""

    _escribir_mes(tmp_path / "merra2_flx", "flx_202001.nc", "2020-01-01", _mesh(1.0))
    _escribir_mes(tmp_path / "merra2_slv", "slv_202001.nc", "2020-01-01", _mesh(280.0), "T2M", "K")
    _escribir_mes(tmp_path / "merra2_legacy" / "flx", "flx_202002.nc", "2020-02-01", _mesh(9.0))

    ds = cargar_merra2(tmp_path, ["PRECTOTCORR", "T2M"])

    assert set(ds.data_vars) == {"PRECTOTCORR", "T2M"}
    assert ds.sizes["time"] == 1
    assert float(ds["PRECTOTCORR"].values[0, 0, 0]) == pytest.approx(1.0)


def test_cargar_merra2_rechaza_merra2_legacy(tmp_path: Path) -> None:
    """Pedir explícitamente la carpeta legacy es un error."""

    _escribir_mes(tmp_path / "merra2_legacy" / "flx", "flx_202001.nc", "2020-01-01", _mesh(1.0))

    with pytest.raises(ValueError, match="merra2_legacy"):
        cargar_merra2(tmp_path / "merra2_legacy", ["PRECTOTCORR"])


def test_cargar_merra2_avisa_de_variable_inexistente(tmp_path: Path) -> None:
    """Una variable que no existe en los datos produce un error claro."""

    carpeta = tmp_path / "merra2_flx"
    _escribir_mes(carpeta, "merra_202001.nc", "2020-01-01", _mesh())

    with pytest.raises(ValueError, match="T2M"):
        cargar_merra2(carpeta, ["T2M"])


# --- Promedio regional --------------------------------------------------------


def test_promedio_regional_calcula_el_promedio_de_la_malla() -> None:
    """El promedio regional usa solo los píxeles dentro del bbox."""

    valores = np.arange(1.0, 7.0).reshape(3, 2)  # filas: lat 13, 14, 15
    serie = xr.DataArray(
        valores,
        dims=("lat", "lon"),
        coords={"lat": LATITUDES, "lon": LONGITUDES},
    )

    promedio = promedio_regional(serie, (-88.0, 13.0, -87.0, 14.0))

    # Solo las filas de latitud 13 y 14 y la columna de longitud -88: 1 y 3.
    assert float(promedio.values) == pytest.approx(2.0)


def test_promedio_regional_devuelve_una_serie_temporal() -> None:
    """El promedio regional conserva la dimensión temporal."""

    fechas = pd.date_range("2020-01-01", periods=3, freq="MS")
    valores = np.arange(1.0, 19.0).reshape(3, 3, 2)
    serie = _serie_mensual(fechas, valores)

    promedio = promedio_regional(serie, (-88.0, 13.0, -87.0, 15.0))

    assert promedio.dims == ("time",)
    assert promedio.sizes["time"] == 3
    # Todas las latitudes y solo la columna de longitud -88: 1, 3 y 5.
    assert float(promedio.values[0]) == pytest.approx(3.0)


def test_promedio_regional_falla_si_el_bbox_no_intersecta() -> None:
    """Un bbox fuera de la malla produce un error claro."""

    serie = xr.DataArray(
        np.zeros((3, 2)),
        dims=("lat", "lon"),
        coords={"lat": LATITUDES, "lon": LONGITUDES},
    )

    with pytest.raises(ValueError, match="no intersecta"):
        promedio_regional(serie, (100.0, 13.0, 101.0, 14.0))
