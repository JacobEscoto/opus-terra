"""Genera los JSON de tendencias que consume la capa pública del frontend."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from opusterra.enso import cargar_oni, remover_enso
from opusterra.tendencia import fdr_benjamini_hochberg, mann_kendall, pendiente_sen


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "frontend" / "public" / "data"
INICIO = pd.Period("2000-02", freq="M")
FIN = pd.Period("2025-09", freq="M")
ALFA = 0.05


def _periodos_completos(index: pd.DatetimeIndex) -> list[int]:
    meses = pd.Series(index.to_period("M"), index=index).groupby(index.year).nunique()
    return [int(year) for year, count in meses.items() if count == 12]


def _base(
    fuente: str,
    variable: str,
    nombre: str,
    unidad: str,
    periodo: tuple[int, int],
    *,
    limitacion: str | None = None,
) -> dict:
    resultado = {
        "fuente": fuente,
        "variable": variable,
        "nombre_variable": nombre,
        "unidad": unidad,
        "periodo": {"inicio": periodo[0], "fin": periodo[1]},
        "contexto_oms": "Análisis ambiental; no constituye un diagnóstico de salud.",
        "pares": [],
        "pixeles_probados": 0,
        "pixeles_significativos_fdr": 0,
        "fdr": {"metodo": "Benjamini-Hochberg", "alfa": ALFA, "universo": "píxeles de Honduras"},
        "resultados_pixeles": [],
        "metodologia": {
            "anomalia": "anomalía mensual respecto a la climatología del periodo efectivo",
            "enso": "remoción lineal mediante ONI mensual",
            "serie_anual": "promedio de residuos mensuales; solo años con 12 meses",
            "tendencia": "Mann-Kendall original y pendiente de Theil-Sen por píxel",
        },
    }
    if limitacion:
        resultado["limitacion"] = limitacion
    return resultado


def _crear_pares(registros: list[dict]) -> list[dict]:
    crecientes = [r for r in registros if r["significativa_fdr"] and r["direccion"] == "creciente"]
    decrecientes = [r for r in registros if r["significativa_fdr"] and r["direccion"] == "decreciente"]
    pares = []
    for indice, (creciente, decreciente) in enumerate(zip(crecientes, decrecientes, strict=False), 1):
        def region(registro: dict, tendencia: str) -> dict:
            return {
                "nombre": f"Píxel {registro['lat']:.2f}, {registro['lon']:.2f}",
                "lat": registro["lat"],
                "lon": registro["lon"],
                "tendencia": tendencia,
                "cambio_porcentual": registro["cambio_porcentual"],
                "significativa": True,
                "explicacion": "La tendencia anual supera el umbral FDR de Benjamini-Hochberg.",
            }

        pares.append({
            "id": f"pixel-{indice}",
            "region_a": region(creciente, "alza"),
            "region_b": region(decreciente, "bajada"),
        })
    return pares


def _cargar_malla_t2m() -> xr.DataArray:
    rutas = sorted((RAW / "merra2_slv").glob("*.nc"))
    por_mes: dict[pd.Period, Path] = {}
    for ruta in rutas:
        coincidencia = re.search(r"\.(\d{6})_honduras\.nc$", ruta.name)
        if not coincidencia:
            continue
        mes = pd.Period(coincidencia.group(1), freq="M")
        if INICIO <= mes <= FIN:
            anterior = por_mes.get(mes)
            if anterior is None or ruta.name.split(".")[0] > anterior.name.split(".")[0]:
                por_mes[mes] = ruta
    esperados = pd.period_range(INICIO, FIN, freq="M")
    faltantes = [str(mes) for mes in esperados if mes not in por_mes]
    if faltantes:
        raise RuntimeError(f"Faltan meses MERRA-2 T2M en la ventana efectiva: {', '.join(faltantes)}")
    partes = []
    for mes in esperados:
        with xr.open_dataset(por_mes[mes]) as dataset:
            partes.append(dataset["T2M"].load())
    return xr.concat(partes, dim="time").assign_coords(time=esperados.to_timestamp())


def _analizar_malla(da: xr.DataArray, nombre: str, unidad: str, fuente: str) -> dict:
    if nombre[0] == "merra2_t2m":
        da = da - 273.15
        da.attrs["units"] = "degC"
    da = da.sel(time=slice(INICIO.start_time, FIN.end_time))
    climatologia = da.groupby("time.month").mean("time")
    anomalia = da.groupby("time.month") - climatologia
    fechas = pd.DatetimeIndex(anomalia.time.values)
    ancha = anomalia.to_series().unstack(["lat", "lon"])
    oni = cargar_oni(ROOT / "data" / "external" / "nino-3.4" / "iersst_nino3.4a_1996_2026.nc")
    residuos, coeficientes, r2 = remover_enso(ancha, oni)
    anios = _periodos_completos(pd.DatetimeIndex(residuos.index))
    completos = residuos[residuos.index.year.isin(anios)]
    anual = completos.groupby(completos.index.year).mean()

    registros: list[dict] = []
    pvalores: list[float] = []
    claves: list[tuple[float, float]] = []
    for lat, lon in anual.columns:
            serie = anual[(lat, lon)].to_numpy(dtype=float)
            if not np.isfinite(serie).all() or len(serie) < 3:
                continue
            z, p, direccion = mann_kendall(serie)
            sen, intercepto = pendiente_sen(serie)
            registro = {
                "lat": float(lat),
                "lon": float(lon),
                "mann_kendall_z": z,
                "p_valor": p,
                "direccion": direccion,
                "sen_unidad_por_anio": sen,
                "intercepto_sen": intercepto,
                "coeficiente_enso": float(coeficientes[(lat, lon)]),
                "r2_enso": float(r2[(lat, lon)]),
                "n_anios": int(len(serie)),
                "valor_anual_inicial": float(serie[0]),
                "valor_anual_final": float(serie[-1]),
                "cambio_porcentual": float(
                    (serie[-1] - serie[0]) / abs(serie[0]) * 100 if serie[0] else 0.0
                ),
                "significativa_fdr": False,
            }
            registros.append(registro)
            pvalores.append(p)
            claves.append((float(lat), float(lon)))

    mascara = fdr_benjamini_hochberg(np.asarray(pvalores), alfa=ALFA)
    for registro, significativa in zip(registros, mascara, strict=True):
        registro["significativa_fdr"] = bool(significativa)
    significativos = [registro for registro in registros if registro["significativa_fdr"]]
    resultado = _base(fuente, nombre[0], nombre[1], unidad, (anios[0], anios[-1]))
    resultado["pixeles_probados"] = len(registros)
    resultado["pixeles_significativos_fdr"] = len(significativos)
    resultado["resultados_pixeles"] = registros
    resultado["pares"] = _crear_pares(registros)
    resultado["periodo"]["mes_inicio"] = str(INICIO)
    resultado["periodo"]["mes_fin"] = str(FIN)
    resultado["periodo"]["meses"] = int(len(fechas))
    resultado["periodo"]["anios_completos"] = anios
    resultado["fdr"]["p_valores_probados"] = len(pvalores)
    return resultado


def _sin_malla_precipitacion(
    ruta: Path, variable: str, nombre: str, fuente: str, unidad: str
) -> dict:
    with xr.open_dataset(ruta, decode_times=True) as dataset:
        inicio = int(str(dataset.time.values[0])[:4])
        fin = int(str(dataset.time.values[-1])[:4])
    resultado = _base(
        fuente,
        variable,
        nombre,
        unidad,
        (INICIO.year, FIN.year),
        limitacion=(
            "El insumo disponible es una serie area-promedio sin dimensiones lat/lon; "
            "no se fabricaron píxeles ni pruebas de significancia."
        ),
    )
    resultado["fuente_periodo_disponible"] = {"inicio": inicio, "fin": fin}
    resultado["periodo"]["mes_inicio"] = str(INICIO)
    resultado["periodo"]["mes_fin"] = str(FIN)
    resultado["periodo"]["anios_completos"] = []
    resultado["fdr"]["estado"] = "no_aplicable_sin_malla"
    return resultado


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    t2m = _analizar_malla(
        _cargar_malla_t2m(),
        ("merra2_t2m", "Temperatura del aire a 2 m"),
        "degC",
        "NASA MERRA-2 M2TMNXSLV v5.12.4",
    )
    precipitacion_merra = _sin_malla_precipitacion(
        RAW / "precipitation" / "g4.areaAvgTimeSeries.M2TMNXFLX_5_12_4_PRECTOTCORR.19960101-20260131.180W_90S_180E_90N.nc",
        "merra2_precipitacion",
        "Precipitación MERRA-2 PRECTOTCORR",
        "NASA MERRA-2 M2TMNXFLX v5.12.4",
        "kg m-2 s-1",
    )
    imerg = _sin_malla_precipitacion(
        RAW / "precipitation" / "g4.areaAvgTimeSeries.GPM_3IMERGM_07_precipitation.19960101-20260131.180W_90S_180E_90N.nc",
        "imerg_precipitacion",
        "Precipitación GPM IMERG",
        "NASA GPM IMERG v07",
        "mm/hr",
    )
    for nombre, contenido in (
        ("merra2_t2m.json", t2m),
        ("merra2_precipitacion.json", precipitacion_merra),
        ("imerg_precipitacion.json", imerg),
    ):
        (OUTPUT / nombre).write_text(json.dumps(contenido, ensure_ascii=False, indent=2) + "\n")
        print(f"{nombre}: {contenido['pixeles_probados']} píxeles probados, {contenido['pixeles_significativos_fdr']} significativos FDR")


if __name__ == "__main__":
    main()
