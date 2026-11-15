"""Carga del ONI y eliminación lineal de su componente en series climáticas."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr


RUTA_ONI_POR_DEFECTO = Path("data/external/nino-3.4/iersst_nino3.4a_1996_2026.nc")
NOMBRE_VARIABLE_ONI = "Nino3.4"


def cargar_oni(ruta: str | Path = RUTA_ONI_POR_DEFECTO) -> pd.Series:
    """Lee el índice ONI mensual y devuelve una serie indexada por mes.

    El NetCDF usado por el proyecto declara ``months since`` con calendario
    gregoriano, una combinación que xarray no decodifica de forma automática.
    Por ello se abre en modo crudo y se construye el índice mensual desde el
    primer mes declarado.
    """

    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el archivo ONI: {ruta}")
    with xr.open_dataset(ruta, decode_times=False) as dataset:
        if NOMBRE_VARIABLE_ONI not in dataset:
            raise ValueError(
                f"El archivo ONI no contiene '{NOMBRE_VARIABLE_ONI}'. "
                f"Variables disponibles: {list(dataset.data_vars)}"
            )
        variable = dataset[NOMBRE_VARIABLE_ONI]
        if variable.dims != ("time",):
            raise ValueError(
                f"La variable ONI debe ser 1D sobre 'time'; dimensiones recibidas: {variable.dims}"
            )
        tiempo = dataset["time"]
        unidades_tiempo = str(tiempo.attrs.get("units", ""))
        if not unidades_tiempo.startswith("months since "):
            raise ValueError(f"Unidades temporales ONI no reconocidas: {unidades_tiempo}")
        inicio = pd.Timestamp(unidades_tiempo.removeprefix("months since ")).to_period("M")
        fechas = pd.period_range(inicio, periods=variable.sizes["time"], freq="M").to_timestamp()
        valores = np.asarray(variable.values, dtype=float)
        attrs = dict(variable.attrs)

    serie = pd.Series(valores, index=fechas, name=NOMBRE_VARIABLE_ONI)
    serie.attrs = {
        "variable": NOMBRE_VARIABLE_ONI,
        "dimensiones": variable.dims,
        "resolucion_temporal": "mensual",
        "rango_fechas": f"{fechas[0]:%Y-%m} a {fechas[-1]:%Y-%m}",
        "unidades": attrs.get("units", ""),
    }
    return serie


def _a_indice_mensual(serie: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Normaliza el índice de una serie a timestamps al comienzo del mes."""

    resultado = serie.copy()
    indice = pd.DatetimeIndex(pd.to_datetime(resultado.index)).to_period("M").to_timestamp()
    if indice.has_duplicates:
        raise ValueError("La serie contiene meses duplicados")
    resultado.index = indice
    return resultado.sort_index()


def alinear_mensual(
    serie_ancha: pd.Series | pd.DataFrame,
    oni: pd.Series,
) -> tuple[pd.Series | pd.DataFrame, pd.Series]:
    """Alinea una serie o tabla y el ONI por año-mes.

    Devuelve `(serie_alineada, oni_alineado)`. Se exige correspondencia para
    todos los meses del rango de la serie analizada; los meses adicionales del
    ONI se descartan.
    """

    serie = _a_indice_mensual(serie_ancha)
    indice_oni = _a_indice_mensual(oni)
    faltantes = serie.index.difference(indice_oni.index)
    if len(faltantes):
        meses = ", ".join(str(mes) for mes in faltantes.to_period("M"))
        raise ValueError(f"El ONI no tiene correspondencia para estos meses: {meses}")
    oni_alineado = indice_oni.reindex(serie.index)
    if oni_alineado.isna().any():
        raise ValueError("El ONI contiene NaN en meses necesarios para el análisis")
    return serie, oni_alineado


def remover_enso(
    serie: pd.Series | pd.DataFrame,
    oni: pd.Series,
) -> tuple[pd.Series | pd.DataFrame, float | pd.Series, float | pd.Series]:
    """Quita por regresión lineal el componente explicado por el ONI.

    Devuelve `(residuos, coeficiente, r2)`. Para un `DataFrame`, coeficiente y
    R² son series indexadas por columna; para una `Series`, son escalares.
    """

    serie_alineada, oni_alineado = alinear_mensual(serie, oni)
    x = oni_alineado.to_numpy(dtype=float)
    if not np.isfinite(x).all():
        raise ValueError("El ONI contiene valores no finitos")

    es_serie = isinstance(serie_alineada, pd.Series)
    tabla = serie_alineada.to_frame() if es_serie else serie_alineada
    residuos = pd.DataFrame(index=tabla.index)
    coeficientes: dict[str, float] = {}
    r2s: dict[str, float] = {}
    for nombre in tabla.columns:
        y = tabla[nombre].to_numpy(dtype=float)
        if not np.isfinite(y).all():
            raise ValueError(f"La serie '{nombre}' contiene NaN o valores infinitos")
        pendiente, intercepto = np.polyfit(x, y, 1)
        ajustado = intercepto + pendiente * x
        residuos[nombre] = y - ajustado
        coeficientes[nombre] = float(pendiente)
        ss_total = np.sum((y - y.mean()) ** 2)
        ss_residual = np.sum((y - ajustado) ** 2)
        r2s[nombre] = float(1 - ss_residual / ss_total) if ss_total else 0.0

    if es_serie:
        salida = residuos.iloc[:, 0].rename(serie_alineada.name)
        return salida, coeficientes[tabla.columns[0]], r2s[tabla.columns[0]]
    return residuos, pd.Series(coeficientes), pd.Series(r2s)
