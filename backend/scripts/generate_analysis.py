"""Genera los JSON de tendencias que consume la capa pública del frontend."""

from __future__ import annotations

import json
import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import tomllib

import numpy as np
import pandas as pd
import xarray as xr

from opusterra import mod13c2
from opusterra.config import PERIODO_COMUN
from opusterra.enso import cargar_oni, remover_enso
from opusterra.tendencia import fdr_benjamini_hochberg, mann_kendall, pendiente_sen


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "frontend" / "public" / "data"
DATASETS = ROOT / "backend" / "config" / "datasets.toml"
INICIO = pd.Period(PERIODO_COMUN[0], freq="M")
FIN = pd.Period(PERIODO_COMUN[1], freq="M")
ALFA = 0.05


@dataclass(frozen=True)
class Region:
    id: str
    nombre: str
    bbox: tuple[float, float, float, float]


def _cargar_region(region_id: str) -> Region:
    with DATASETS.open("rb") as archivo:
        regiones = tomllib.load(archivo).get("regions", {})
    datos = regiones.get(region_id)
    if not isinstance(datos, dict):
        disponibles = ", ".join(sorted(regiones)) or "ninguna"
        raise ValueError(f'La región "{region_id}" no existe. Disponibles: {disponibles}.')
    bbox = datos.get("bbox")
    nombre = datos.get("nombre")
    if (
        not isinstance(nombre, str)
        or not nombre
        or not isinstance(bbox, list)
        or len(bbox) != 4
        or not all(isinstance(valor, (int, float)) for valor in bbox)
    ):
        raise ValueError(f'La región "{region_id}" no tiene nombre o bbox válidos.')
    return Region(region_id, nombre, tuple(float(valor) for valor in bbox))


def _periodos_completos(index: pd.DatetimeIndex) -> list[int]:
    meses = pd.Series(index.to_period("M"), index=index).groupby(index.year).nunique()
    return [int(year) for year, count in meses.items() if count == 12]


def _base(
    fuente: str,
    variable: str,
    nombre: str,
    unidad: str,
    periodo: tuple[int, int],
    region: Region,
    *,
    limitacion: str | None = None,
) -> dict:
    resultado = {
        "fuente": fuente,
        "variable": variable,
        "region": region.id,
        "region_nombre": region.nombre,
        "nombre_variable": nombre,
        "unidad": unidad,
        "periodo": {"inicio": periodo[0], "fin": periodo[1]},
        "contexto_oms": "Análisis ambiental; no constituye un diagnóstico de salud.",
        "pares": [],
        "pixeles_probados": 0,
        "pixeles_significativos_fdr": 0,
        "fdr": {"metodo": "Benjamini-Hochberg", "alfa": ALFA, "universo": f"píxeles de {region.nombre}"},
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


def _serializar_resultado(contenido: dict) -> str:
    """Mantiene legible el JSON, pero evita indentar la lista de píxeles."""
    marcador = "__RESULTADOS_PIXELES_COMPACTOS__"
    copia = {**contenido, "resultados_pixeles": marcador}
    texto = json.dumps(copia, ensure_ascii=False, indent=2, allow_nan=False)
    compactos = json.dumps(
        contenido["resultados_pixeles"],
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )
    reemplazo = json.dumps(marcador, ensure_ascii=False)
    if texto.count(reemplazo) != 1:
        raise RuntimeError("No se pudo compactar resultados_pixeles de forma segura")
    return texto.replace(reemplazo, compactos) + "\n"


def _cargar_malla_t2m(raw: Path) -> xr.DataArray:
    rutas = sorted((raw / "merra2_slv").glob("*.nc"))
    por_mes: dict[pd.Period, Path] = {}
    for ruta in rutas:
        coincidencia = re.search(r"\.(\d{6})(?:_[^.]+)?\.nc$", ruta.name)
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


def _analizar_malla(
    da: xr.DataArray,
    nombre: str,
    unidad: str,
    fuente: str,
    region: Region,
    calidad: dict | None = None,
    limitacion: str | None = None,
) -> dict:
    if nombre[0] == "merra2_t2m":
        da = da - 273.15
        da.attrs["units"] = "degC"
    da = da.sel(time=slice(INICIO.start_time, FIN.end_time))
    climatologia = da.groupby("time.month").mean("time")
    anomalia = da.groupby("time.month") - climatologia
    fechas = pd.DatetimeIndex(anomalia.time.values)
    ancha = anomalia.to_series().unstack(["lat", "lon"])
    # Una celda con algún mes no confiable no puede sostener la serie anual
    # completa que exige el resto del pipeline, así que se descarta entera.
    completas = ancha.notna().all(axis=0)
    celdas_descartadas = int((~completas).sum())
    if celdas_descartadas:
        ancha = ancha.loc[:, completas]
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
                "valores_anuales": [round(float(valor), 4) for valor in serie],
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
    resultado = _base(
        fuente, nombre[0], nombre[1], unidad, (anios[0], anios[-1]), region, limitacion=limitacion
    )
    resultado["pixeles_probados"] = len(registros)
    resultado["pixeles_significativos_fdr"] = len(significativos)
    resultado["resultados_pixeles"] = registros
    resultado["pares"] = _crear_pares(registros)
    resultado["periodo"]["mes_inicio"] = str(INICIO)
    resultado["periodo"]["mes_fin"] = str(FIN)
    resultado["periodo"]["meses"] = int(len(fechas))
    resultado["periodo"]["anios_completos"] = anios
    resultado["fdr"]["p_valores_probados"] = len(pvalores)
    if calidad is not None:
        calidad = {**calidad, "celdas_descartadas_por_calidad": celdas_descartadas}
        resultado["calidad"] = calidad
        resultado["metodologia"]["mascara_calidad"] = mod13c2.DESCRIPCION_CRITERIO
    return resultado


def _analizar_malla_mod13c2(raw: Path, region: Region) -> dict:
    """Analiza el NDVI de MOD13C2 con la misma cadena que MERRA-2.

    La única diferencia es el paso previo de control de calidad: el NDVI solo
    entra al pipeline en las celda-mes que MOD13C2 marca como confiables.
    """

    cubo = mod13c2.cargar_cubo(raw / "mod13c2", INICIO, FIN)
    mascara, conteos = mod13c2.mascara_confiable(cubo)
    ndvi = mod13c2.ndvi_mascarado(cubo, mascara)
    resumen = mod13c2.resumen_calidad(
        mascara, conteos, pd.DatetimeIndex(cubo.time.values)
    )
    return _analizar_malla(
        ndvi,
        ("mod13c2_ndvi", "Índice de vegetación de diferencia normalizada (NDVI)"),
        "NDVI (adimensional)",
        "NASA MODIS MOD13C2 v061 (CMG 0.05° mensual)",
        calidad=resumen,
        region=region,
        limitacion=(
            "La serie analizada es el residuo mensual sin estacionalidad ni ENSO, por lo que "
            "cambio_porcentual se calcula sobre valores residuales cercanos a cero y no debe "
            "leerse como cambio de cobertura vegetal. El recorte MOD13C2 corresponde al bbox de "
            f"{region.nombre} con margen e incluye celdas de países vecinos y del mar."
        ),
    )


def _sin_malla_precipitacion(
    ruta: Path, variable: str, nombre: str, fuente: str, unidad: str, region: Region
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
        region,
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


def _buscar_precipitacion(raw: Path, patron: str) -> Path:
    rutas = sorted((raw / "precipitation").glob(patron))
    if not rutas:
        raise FileNotFoundError(f"No se encontró el archivo de precipitación {patron} en {raw / 'precipitation'}.")
    return rutas[0]


def _actualizar_regiones(region: Region, variables: list[str]) -> None:
    ruta = OUTPUT / "regiones.json"
    if ruta.exists():
        contenido = json.loads(ruta.read_text(encoding="utf-8"))
        if not isinstance(contenido, list):
            raise ValueError("frontend/public/data/regiones.json debe contener una lista.")
    else:
        contenido = []
    entrada = {
        "id": region.id,
        "nombre": region.nombre,
        "bbox": list(region.bbox),
        "variables": variables,
    }
    reemplazado = False
    actualizado = []
    for item in contenido:
        if isinstance(item, dict) and item.get("id") == region.id:
            actualizado.append(entrada)
            reemplazado = True
        else:
            actualizado.append(item)
    if not reemplazado:
        actualizado.append(entrada)
    ruta.write_text(json.dumps(actualizado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default="honduras", help="Identificador de la región en datasets.toml")
    args = parser.parse_args()
    region = _cargar_region(args.region)
    raw = ROOT / "data" / "raw" / region.id
    output = OUTPUT / region.id
    output.mkdir(parents=True, exist_ok=True)
    t2m = _analizar_malla(
        _cargar_malla_t2m(raw),
        ("merra2_t2m", "Temperatura del aire a 2 m"),
        "degC",
        "NASA MERRA-2 M2TMNXSLV v5.12.4",
        region=region,
    )
    precipitacion_merra = _sin_malla_precipitacion(
        _buscar_precipitacion(raw, "*M2TMNXFLX*PRECTOTCORR*.nc"),
        "merra2_precipitacion",
        "Precipitación MERRA-2 PRECTOTCORR",
        "NASA MERRA-2 M2TMNXFLX v5.12.4",
        "kg m-2 s-1",
        region,
    )
    imerg = _sin_malla_precipitacion(
        _buscar_precipitacion(raw, "*GPM_3IMERGM*precipitation*.nc"),
        "imerg_precipitacion",
        "Precipitación GPM IMERG",
        "NASA GPM IMERG v07",
        "mm/hr",
        region,
    )
    ndvi = _analizar_malla_mod13c2(raw, region)
    _actualizar_regiones(region, [
        "merra2_t2m",
        "merra2_precipitacion",
        "imerg_precipitacion",
        "mod13c2_ndvi",
    ])
    for nombre, contenido in (
        ("merra2_t2m.json", t2m),
        ("merra2_precipitacion.json", precipitacion_merra),
        ("imerg_precipitacion.json", imerg),
        ("mod13c2_ndvi.json", ndvi),
    ):
        ruta_salida = output / nombre
        tamano_anterior = ruta_salida.stat().st_size if ruta_salida.exists() else 0
        contenido_exportado = contenido
        texto = _serializar_resultado(contenido_exportado)
        limitado_a_significativos = False
        if len(texto.encode("utf-8")) > 3_000_000 and contenido["resultados_pixeles"]:
            contenido_exportado = {
                **contenido,
                "resultados_pixeles": [
                    registro
                    for registro in contenido["resultados_pixeles"]
                    if registro["significativa_fdr"]
                ],
            }
            texto = _serializar_resultado(contenido_exportado)
            limitado_a_significativos = True
        ruta_salida.write_text(texto, encoding="utf-8")
        tamano_nuevo = ruta_salida.stat().st_size
        print(
            f"{nombre}: tamaño {tamano_anterior / 1_000_000:.2f} MB -> "
            f"{tamano_nuevo / 1_000_000:.2f} MB"
            + (" (solo celdas significativas)" if limitado_a_significativos else "")
        )
        print(f"{nombre}: {contenido['pixeles_probados']} píxeles probados, {contenido['pixeles_significativos_fdr']} significativos FDR")


if __name__ == "__main__":
    main()
