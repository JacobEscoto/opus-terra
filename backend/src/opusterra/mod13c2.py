"""Carga y control de calidad del NDVI mensual de MODIS MOD13C2 v061.

El producto MOD13C2 entrega tres campos por celda y mes: el índice de
vegetación `ndvi`, el campo de bits `ndvi_quality` y el rango de fiabilidad
`ndvi_reliability`. Los dos últimos son la documentación del propio producto
sobre la confianza de cada valor: el atributo `Legend` de cada variable
describe qué estados son confiables y qué estados obligan a descartar el dato.

Este módulo concentrate la carga del cubo mensual y la construcción de la
máscara de calidad; el resto del pipeline (anomalía, ENSO, serie anual,
Mann-Kendall, Sen y FDR) es el mismo que se usa para MERRA-2.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

VARIABLE_NDVI = "ndvi"
VARIABLE_CALIDAD = "ndvi_quality"
VARIABLE_FIABILIDAD = "ndvi_reliability"

# Bits de `ndvi_quality`, contados de derecha a izquierda según la leyenda:
#   [0-1]   MODLAND_QA      00 good quality, 01 check QA, 10 cloudy, 11 no producido
#   [2-5]   VI usefulness   0000..1011 calidad decreciente, 1100+ no real o inservible
#   [11-13] Land/Water flag 001 = land
MASCARA_MODLAND = 0b11
MASCARA_UTILIDAD = 0b1111
MASCARA_TIERRA = 0b111
DESPLAZAMIENTO_UTILIDAD = 2
DESPLAZAMIENTO_TIERRA = 11

# Estados aceptados, tomados literalmente de la leyenda del producto.
MODLAND_ACEPTADOS = (0, 1)
UTILIDAD_MAXIMA = 11
TIERRA_ACEPTADA = 1
FIABILIDAD_ACEPTADA = (0, 1)

DESCRIPCION_CRITERIO = (
    "Se descarta la celda-mes si el NDVI no fue producido (valor de relleno), "
    "si la fiabilidad no es buena o marginal (rango 0 o 1; se excluyen nieve/hielo, "
    "nubosidad y valores estimados de la serie histórica), si MODLAND_QA no es "
    "buena o revisable (00 o 01; se excluye nubosidad probable y no producido), "
    "si la utilidad del VI es 1100 o superior (dato interpolado, no real, "
    "inservible o no procesado) o si la bandera tierra/agua no indica tierra."
)


def mes_de_archivo(nombre: str) -> pd.Period:
    """Extrae el mes calendario del nombre `MOD13C2.AYYYYDDD.<coleccion>.<fecha>.nc`."""

    coincidencia = re.search(r"\.A(\d{7})\.", nombre)
    if not coincidencia:
        raise ValueError(f"El nombre no corresponde a un archivo MOD13C2: {nombre}")
    digitos = coincidencia.group(1)
    inicio = pd.Timestamp(f"{digitos[:4]}-01-01")
    return (inicio + pd.Timedelta(days=int(digitos[4:]) - 1)).to_period("M")


def cargar_cubo(
    directorio: str | Path,
    inicio: pd.Period,
    fin: pd.Period,
) -> xr.Dataset:
    """Carga el cubo mensual `(tiempo, lat, lon)` del periodo indicado.

    Cada archivo MOD13C2 cubre un mes. Se exige que todos los meses del
    intervalo estén presentes; si falta alguno se lanza un error, porque el
    resto del pipeline asume una serie mensual continua.
    """

    directorio = Path(directorio)
    por_mes: dict[pd.Period, Path] = {}
    for ruta in sorted(directorio.glob("*.nc")):
        mes = mes_de_archivo(ruta.name)
        if inicio <= mes <= fin:
            por_mes[mes] = ruta
    esperados = pd.period_range(inicio, fin, freq="M")
    faltantes = [str(mes) for mes in esperados if mes not in por_mes]
    if faltantes:
        raise RuntimeError(
            f"Faltan meses MOD13C2 en la ventana efectiva: {', '.join(faltantes)}"
        )
    partes = []
    for mes in esperados:
        with xr.open_dataset(por_mes[mes]) as dataset:
            partes.append(
                dataset[[VARIABLE_NDVI, VARIABLE_CALIDAD, VARIABLE_FIABILIDAD]].load()
            )
    cubo = xr.concat(partes, dim="time")
    return cubo.assign_coords(time=esperados.to_timestamp())


def mascara_confiable(cubo: xr.Dataset) -> tuple[np.ndarray, dict]:
    """Construye la máscara de calidad `(tiempo, lat, lon)` y sus conteos.

    Devuelve la máscara verdadera en las celda-mes confiables y un diccionario
    con el desglose de exclusiones por criterio.
    """

    ndvi = np.asarray(cubo[VARIABLE_NDVI].values, dtype=float)
    calidad = np.asarray(cubo[VARIABLE_CALIDAD].values, dtype=float)
    fiabilidad = np.asarray(cubo[VARIABLE_FIABILIDAD].values, dtype=float)

    bits = np.where(np.isnan(calidad), -1, calidad).astype(np.int64)
    modland = bits & MASCARA_MODLAND
    utilidad = (bits >> DESPLAZAMIENTO_UTILIDAD) & MASCARA_UTILIDAD
    tierra = (bits >> DESPLAZAMIENTO_TIERRA) & MASCARA_TIERRA

    producido = np.isfinite(ndvi)
    fiabilidad_ok = np.isfinite(fiabilidad) & np.isin(fiabilidad, FIABILIDAD_ACEPTADA)
    modland_ok = np.isin(modland, MODLAND_ACEPTADOS)
    utilidad_ok = utilidad <= UTILIDAD_MAXIMA
    tierra_ok = tierra == TIERRA_ACEPTADA

    mascara = producido & fiabilidad_ok & modland_ok & utilidad_ok & tierra_ok
    conteos = {
        "ndvi_no_producido": int((~producido).sum()),
        "fiabilidad_no_confiable": int((~fiabilidad_ok).sum()),
        "modland_no_confiable": int((~modland_ok).sum()),
        "utilidad_inservible": int((~utilidad_ok).sum()),
        "no_vegetacion_tierra": int((~tierra_ok).sum()),
        "celda_meses_excluidos": int((~mascara).sum()),
        "celda_meses_validos": int(mascara.sum()),
    }
    return mascara, conteos


def resumen_calidad(mascara: np.ndarray, conteos: dict, tiempos: pd.DatetimeIndex) -> dict:
    """Resume el efecto de la máscara de calidad sobre la malla y el tiempo."""

    por_mes = mascara.reshape(mascara.shape[0], -1)
    celdas_totales = por_mes.shape[1]
    celdas_completas = por_mes.all(axis=0)
    excluidas_por_mes = (~por_mes).sum(axis=1)
    return {
        "criterio": DESCRIPCION_CRITERIO,
        "celdas_malla": int(celdas_totales),
        "celdas_conservadas": int(celdas_completas.sum()),
        "celdas_excluidas": int(celdas_totales - celdas_completas.sum()),
        "celda_meses_totales": int(mascara.size),
        "celda_meses_validos": int(conteos["celda_meses_validos"]),
        "celda_meses_excluidos": int(conteos["celda_meses_excluidos"]),
        "exclusiones_por_criterio": {
            "ndvi_no_producido": conteos["ndvi_no_producido"],
            "fiabilidad_no_confiable": conteos["fiabilidad_no_confiable"],
            "modland_no_confiable": conteos["modland_no_confiable"],
            "utilidad_inservible": conteos["utilidad_inservible"],
            "no_vegetacion_tierra": conteos["no_vegetacion_tierra"],
        },
        "meses_afectados": int((excluidas_por_mes > 0).sum()),
        "meses_totales": int(len(tiempos)),
        "exclusiones_por_mes_maximo": {
            str(tiempos[i].to_period("M")): int(excluidas_por_mes[i])
            for i in np.argsort(excluidas_por_mes)[::-1][:5]
        },
    }


def ndvi_mascarado(cubo: xr.Dataset, mascara: np.ndarray) -> xr.DataArray:
    """Devuelve el NDVI con NaN en las celda-mes que no son confiables."""

    return cubo[VARIABLE_NDVI].where(xr.DataArray(mascara, dims=cubo[VARIABLE_NDVI].dims))
