"""Carga y preparación de MERRA-2 (FLX y SLV) a partir de los `.nc` ya descargados.

El módulo trabaja sobre los NetCDF recortados a la región que produce
`scripts/download_data.py`. Solo lee `merra2_flx/` y `merra2_slv/`; la carpeta
`merra2_legacy/` queda excluida de forma explícita porque contiene versiones
anteriores de los mismos meses.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from opusterra.config import KELVIN_TO_CELSIUS_OFFSET, NOMBRES_VARIABLES

# MERRA-2 publica fluxos en kg m-2 s-1; el mes se reconstruye con sus días reales.
SEGUNDOS_POR_DIA = 86400

# Carpetas de datos válidos dentro de `data/raw/`.
CARPETAS_MERRA2 = ("merra2_flx", "merra2_slv")

# Carpeta antigua: no se usa para análisis.
CARPETA_LEGACY = "merra2_legacy"


def _archivos_nc(carpeta: Path) -> list[Path]:
    """Devuelve los `.nc` de la carpeta, sin leer subcarpetas."""

    return sorted(carpeta.glob("*.nc"))


def _carpetas_fuente(carpeta: Path) -> list[Path]:
    """Resuelve qué carpetas MERRA-2 hay que leer a partir de la carpeta dada.

    Acepta tanto la carpeta base (`data/raw/`, que contiene `merra2_flx/` y
    `merra2_slv/`) como una de esas subcarpetas directamente.
    """

    base = Path(carpeta)
    if any(parte == CARPETA_LEGACY for parte in base.parts):
        raise ValueError(
            f"La carpeta '{CARPETA_LEGACY}' no debe usarse: contiene versiones antiguas "
            "de los mismos meses. Usa 'merra2_flx' o 'merra2_slv'."
        )
    if _archivos_nc(base):
        return [base]
    candidatas = [base / nombre for nombre in CARPETAS_MERRA2]
    return [candidata for candidata in candidatas if candidata.is_dir()]


def _variables_de(carpeta: Path) -> set[str]:
    """Lista las variables de datos que contiene la carpeta."""

    archivos = _archivos_nc(carpeta)
    if not archivos:
        raise ValueError(f"No hay archivos .nc en la carpeta {carpeta}")
    with xr.open_dataset(archivos[0]) as dataset:
        return set(dataset.data_vars)


def _meses_duplicados(fechas: pd.DatetimeIndex) -> list[tuple[int, int]]:
    """Devuelve los meses (año, mes) que aparecen más de una vez."""

    conteo = pd.Series(fechas.to_period("M")).value_counts()
    duplicados = conteo[conteo > 1].index
    return sorted((period.year, period.month) for period in duplicados)


def _meses_faltantes(fechas: pd.DatetimeIndex) -> list[tuple[int, int]]:
    """Devuelve los meses que faltan entre el primero y el último disponibles."""

    periodos = fechas.to_period("M")
    esperados = pd.period_range(periodos.min(), periodos.max(), freq="M")
    faltantes = esperados.difference(periodos.unique())
    return [(periodo.year, periodo.month) for periodo in faltantes]


def _validar_cobertura(dataset: xr.Dataset, carpeta: Path) -> None:
    """Falla si hay meses duplicados o faltantes dentro del rango cargado."""

    if "time" not in dataset.dims:
        raise ValueError(f"El dataset de {carpeta} no tiene dimensión temporal 'time'")
    fechas = pd.DatetimeIndex(dataset["time"].values)
    if len(fechas) == 0:
        raise ValueError(f"El dataset de {carpeta} no contiene pasos de tiempo")

    duplicados = _meses_duplicados(fechas)
    if duplicados:
        listado = ", ".join(f"{anio:04d}-{mes:02d}" for anio, mes in duplicados)
        raise ValueError(
            f"MERRA-2 en {carpeta}: hay meses duplicados ({listado}). "
            "Elimina los archivos repetidos antes de cargar."
        )

    faltantes = _meses_faltantes(fechas)
    if faltantes:
        listado = ", ".join(f"{anio:04d}-{mes:02d}" for anio, mes in faltantes)
        rango = f"{fechas.min():%Y-%m} a {fechas.max():%Y-%m}"
        raise ValueError(
            f"MERRA-2 en {carpeta}: faltan meses dentro del rango {rango} ({listado}). "
            "Descarga los meses faltantes antes de cargar."
        )


def _abrir_carpeta(carpeta: Path) -> xr.Dataset:
    """Abre todos los `.nc` de la carpeta y los concatena por tiempo."""

    archivos = _archivos_nc(carpeta)
    if not archivos:
        raise ValueError(f"No hay archivos .nc en la carpeta {carpeta}")
    dataset = xr.open_mfdataset(
        archivos,
        combine="nested",
        concat_dim="time",
        data_vars="all",
    )
    return dataset.sortby("time")


def cargar_merra2(carpeta: Path, variables: Iterable[str] | str) -> xr.Dataset:
    """Carga los NetCDF de MERRA-2 de una o varias carpetas y los une.

    `carpeta` puede ser la carpeta base (`data/raw/`) o directamente
    `merra2_flx/` o `merra2_slv/`. Cada variable se busca en la carpeta que la
    contiene, de modo que pedir `PRECTOTCORR` y `T2M` devuelve un único dataset
    con ambas variables.

    Falla con un mensaje claro si dentro del rango cargado hay meses
    duplicados o meses faltantes.

    El dataset devuelto es perezoso (dask); llama a `.load()` si lo quieres
    en memoria.
    """

    solicitados = [variables] if isinstance(variables, str) else list(variables)
    if not solicitados:
        raise ValueError("Se debe solicitar al menos una variable de MERRA-2")

    carpetas = _carpetas_fuente(carpeta)
    if not carpetas:
        raise ValueError(
            f"No se encontraron carpetas de MERRA-2 en {carpeta}. "
            f"Esperadas: {', '.join(CARPETAS_MERRA2)}."
        )

    # Se cachea el contenido de cada carpeta para no releer los archivos.
    contenido: dict[Path, set[str]] = {candidata: _variables_de(candidata) for candidata in carpetas}

    variables_por_carpeta: dict[Path, set[str]] = {}
    for variable in solicitados:
        for candidata in carpetas:
            if variable in contenido[candidata]:
                variables_por_carpeta.setdefault(candidata, set()).add(variable)
                break
        else:
            disponibles = sorted({v for variables in contenido.values() for v in variables})
            raise ValueError(
                f"La variable '{variable}' no está en {carpeta}. "
                f"Variables disponibles: {', '.join(disponibles)}."
            )

    partes = []
    for carpeta in carpetas:
        if carpeta not in variables_por_carpeta:
            continue
        dataset = _abrir_carpeta(carpeta)
        _validar_cobertura(dataset, carpeta)
        partes.append(dataset)

    if len(partes) == 1:
        resultado = partes[0]
    else:
        resultado = xr.merge(partes)

    return resultado[list(solicitados)]


def precipitacion_mm_mes(ds: xr.Dataset | xr.DataArray) -> xr.Dataset | xr.DataArray:
    """Convierte `PRECTOTCORR` de kg m-2 s-1 a mm acumulados del mes real."""

    if isinstance(ds, xr.DataArray):
        if "time" not in ds.dims:
            raise ValueError("El DataArray no tiene dimensión temporal 'time'")
        dias = pd.DatetimeIndex(ds["time"].values).days_in_month
        factor = xr.DataArray(
            np.asarray(dias, dtype=float) * SEGUNDOS_POR_DIA,
            dims="time",
            coords={"time": ds["time"]},
        )
        convertida = ds * factor
        convertida.attrs = dict(ds.attrs)
        convertida.attrs["units"] = "mm/mes"
        convertida.attrs["units_original"] = ds.attrs.get("units", "kg m-2 s-1")
        convertida.attrs["conversion"] = "kg m-2 s-1 -> mm/mes (86400 s x dias reales del mes)"
        return convertida

    nombre = NOMBRES_VARIABLES.merra2_precipitacion
    if nombre not in ds:
        raise ValueError(f"El dataset no contiene la variable '{nombre}'")
    variable = ds[nombre]
    if "time" not in variable.dims:
        raise ValueError(f"La variable '{nombre}' no tiene dimensión temporal 'time'")

    dias = pd.DatetimeIndex(variable["time"].values).days_in_month
    factor = xr.DataArray(
        np.asarray(dias, dtype=float) * SEGUNDOS_POR_DIA,
        dims="time",
        coords={"time": variable["time"]},
    )
    convertida = variable * factor
    convertida.attrs = dict(variable.attrs)
    convertida.attrs["units"] = "mm/mes"
    convertida.attrs["units_original"] = variable.attrs.get("units", "kg m-2 s-1")
    convertida.attrs["conversion"] = "kg m-2 s-1 -> mm/mes (86400 s x dias reales del mes)"
    return ds.assign(**{nombre: convertida})


class _PrecipitacionNamespace:
    mm_mes = staticmethod(precipitacion_mm_mes)


precipitacion = _PrecipitacionNamespace()


def t2m_celsius(ds: xr.Dataset) -> xr.Dataset:
    """Convierte `T2M` de Kelvin a grados Celsius."""

    nombre = NOMBRES_VARIABLES.merra2_temperatura
    if nombre not in ds:
        raise ValueError(f"El dataset no contiene la variable '{nombre}'")
    variable = ds[nombre]
    convertida = variable - KELVIN_TO_CELSIUS_OFFSET
    convertida.attrs = dict(variable.attrs)
    convertida.attrs["units"] = "degC"
    convertida.attrs["units_original"] = variable.attrs.get("units", "K")
    convertida.attrs["conversion"] = "K -> degC (-273.15)"
    return ds.assign(**{nombre: convertida})


def anomalias_mensuales(da: xr.DataArray) -> tuple[xr.DataArray, xr.DataArray]:
    """Calcula la climatología mensual y la anomalia respecto de ella.

    La climatología tiene un valor por píxel y mes calendario (hasta 12); la
    anomalia conserva las dimensiones de la serie original.
    """

    if "time" not in da.dims:
        raise ValueError("La anomalia mensual requiere una dimensión temporal 'time'")

    climatologia = da.groupby("time.month").mean("time")
    anomalia = da.groupby("time.month") - climatologia

    climatologia = climatologia.rename({"month": "mes"})
    climatologia.attrs = {
        **da.attrs,
        "descripcion": "climatología mensual (12 valores por píxel)",
    }
    anomalia.attrs = {
        **da.attrs,
        "descripcion": "anomalia respecto de la climatología mensual",
    }
    return climatologia, anomalia


def promedio_regional(da: xr.DataArray, bbox: tuple[float, float, float, float]) -> xr.DataArray:
    """Calcula el promedio espacial dentro de un bbox (lon_min, lat_min, lon_max, lat_max)."""

    lon_min, lat_min, lon_max, lat_max = bbox
    if lon_min >= lon_max or lat_min >= lat_max:
        raise ValueError(
            "El bbox debe cumplir lon_min < lon_max y lat_min < lat_max, "
            f"recibido: {bbox}"
        )
    for dim in ("lat", "lon"):
        if dim not in da.dims:
            raise ValueError(f"El array no tiene dimensión '{dim}'")

    longitud = np.asarray(da["lon"].values)
    latitud = np.asarray(da["lat"].values)
    lon_slice = slice(lon_min, lon_max) if longitud[0] <= longitud[-1] else slice(lon_max, lon_min)
    lat_slice = slice(lat_min, lat_max) if latitud[0] <= latitud[-1] else slice(lat_max, lat_min)

    recorte = da.sel(lon=lon_slice, lat=lat_slice)
    if not recorte.sizes.get("lat") or not recorte.sizes.get("lon"):
        raise ValueError(f"El bbox {bbox} no intersecta la malla")
    return recorte.mean(dim=["lat", "lon"])
