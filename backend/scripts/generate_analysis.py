"""Genera los JSON de tendencias que consume la capa pública del frontend."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from opusterra import mod13c2
from opusterra.config import PERIODO_COMUN, gpm_mm_h_a_mm_mes
from opusterra.enso import cargar_oni, remover_enso
from opusterra.geocodificacion import etiqueta, ubicacion
import opusterra.merra2
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
        raise ValueError(
            f'La región "{region_id}" no existe. Disponibles: {disponibles}.'
        )
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
    return Region(
        region_id,
        nombre,
        (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
    )


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
    contexto: str | None = None,
) -> dict:
    resultado = {
        "fuente": fuente,
        "variable": variable,
        "region": region.id,
        "region_nombre": region.nombre,
        "nombre_variable": nombre,
        "unidad": unidad,
        "periodo": {"inicio": periodo[0], "fin": periodo[1]},
        "contexto_oms": contexto
        or "Análisis ambiental; no constituye un diagnóstico de salud.",
        "pares": [],
        "pixeles_probados": 0,
        "pixeles_significativos_fdr": 0,
        "fdr": {
            "metodo": "Benjamini-Hochberg",
            "alfa": ALFA,
            "universo": f"píxeles de {region.nombre}",
        },
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
    crecientes = [
        r for r in registros if r["significativa_fdr"] and r["direccion"] == "creciente"
    ]
    decrecientes = [
        r
        for r in registros
        if r["significativa_fdr"] and r["direccion"] == "decreciente"
    ]
    pares = []
    for indice, (creciente, decreciente) in enumerate(
        zip(crecientes, decrecientes, strict=False), 1
    ):

        def region(registro: dict, tendencia: str) -> dict:
            lugar = ubicacion(registro["lat"], registro["lon"])
            nombre = etiqueta(lugar)
            return {
                "nombre": nombre,
                "lat": registro["lat"],
                "lon": registro["lon"],
                "tendencia": tendencia,
                "cambio_porcentual": registro["cambio_porcentual"],
                "significativa": True,
                "explicacion": "La tendencia anual supera el umbral FDR de Benjamini-Hochberg.",
                "pais": lugar["pais"],
                "ciudad": lugar["ciudad"],
            }

        pares.append(
            {
                "id": f"pixel-{indice}",
                "region_a": region(creciente, "alza"),
                "region_b": region(decreciente, "bajada"),
            }
        )
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
    directorio = raw / "merra2_slv"
    if not directorio.is_dir():
        raise FileNotFoundError(f"No existe el directorio de MERRA-2 T2M en {directorio}")
    rutas = sorted(directorio.glob("*.nc"))
    if not rutas:
        raise FileNotFoundError(f"No se encontraron archivos .nc en {directorio}")
    por_mes: dict[pd.Period, Path] = {}
    for ruta in rutas:
        coincidencia = re.search(r"\.(\d{6})(?:_[^.]+)?\.nc$", ruta.name)
        if not coincidencia:
            continue
        mes = pd.Period(coincidencia.group(1), freq="M")
        if INICIO <= mes <= FIN:
            anterior = por_mes.get(mes)
            if (
                anterior is None
                or ruta.name.split(".")[0] > anterior.name.split(".")[0]
            ):
                por_mes[mes] = ruta
    esperados = pd.period_range(INICIO, FIN, freq="M")
    faltantes = [str(mes) for mes in esperados if mes not in por_mes]
    if faltantes:
        raise RuntimeError(
            f"Faltan meses MERRA-2 T2M en la ventana efectiva: {', '.join(faltantes)}"
        )
    partes = []
    for mes in esperados:
        with xr.open_dataset(por_mes[mes]) as dataset:
            partes.append(dataset["T2M"].load())
    return xr.concat(partes, dim="time").assign_coords(time=esperados.to_timestamp())


def _cargar_malla_aer(raw: Path) -> xr.DataArray:
    directorio = raw / "merra2_aer"
    if not directorio.is_dir():
        raise FileNotFoundError(f"No existe el directorio de MERRA-2 AER en {directorio}")
    rutas = sorted(directorio.glob("*.nc"))
    if not rutas:
        raise FileNotFoundError(f"No se encontraron archivos .nc en {directorio}")
    por_mes: dict[pd.Period, Path] = {}
    for ruta in rutas:
        coincidencia = re.search(r"\.(\d{6})(?:_[^.]+)?\.nc$", ruta.name)
        if not coincidencia:
            continue
        mes = pd.Period(coincidencia.group(1), freq="M")
        if INICIO <= mes <= FIN:
            anterior = por_mes.get(mes)
            if (
                anterior is None
                or ruta.name.split(".")[0] > anterior.name.split(".")[0]
            ):
                por_mes[mes] = ruta
    esperados = pd.period_range(INICIO, FIN, freq="M")
    faltantes = [str(mes) for mes in esperados if mes not in por_mes]
    if faltantes:
        raise RuntimeError(
            f"Faltan meses MERRA-2 DUSMASS25 en la ventana efectiva: {', '.join(faltantes)}"
        )
    partes = []
    for mes in esperados:
        with xr.open_dataset(por_mes[mes]) as dataset:
            if "DUSMASS25" not in dataset.variables:
                raise ValueError(f"No se encontró DUSMASS25 en {por_mes[mes].name}")
            partes.append(dataset["DUSMASS25"].load())
    return xr.concat(partes, dim="time").assign_coords(time=esperados.to_timestamp())


def _analizar_malla(
    da: xr.DataArray,
    nombre: str,
    unidad: str,
    fuente: str,
    region: Region,
    calidad: dict | None = None,
    limitacion: str | None = None,
    contexto: str | None = None,
) -> dict:
    if nombre[0] == "merra2_t2m":
        da = da - 273.15
        da.attrs["units"] = "degC"
    elif nombre[0] == "merra2_aer":
        unidad_original = da.attrs.get("units", "")
        if unidad_original == "kg m-3":
            da = da * 1e9
            da.attrs["units_original"] = unidad_original
            da.attrs["conversion"] = "multiplicación por 1e9: kg m-3 a µg/m³"
            da.attrs["units"] = "µg/m³"
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
    oni = cargar_oni(
        ROOT / "data" / "external" / "nino-3.4" / "iersst_nino3.4a_1996_2026.nc"
    )
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
    significativos = [
        registro for registro in registros if registro["significativa_fdr"]
    ]
    resultado = _base(
        fuente,
        nombre[0],
        nombre[1],
        unidad,
        (anios[0], anios[-1]),
        region,
        limitacion=limitacion,
        contexto=contexto,
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
    if nombre[0] == "merra2_aer":
        resultado["metodologia"]["conversion_unidades"] = (
            "DUSMASS25 convertida de kg m-3 a µg/m³ multiplicando por 1e9"
        )
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
    directorio = raw / "mod13c2"
    if not directorio.is_dir():
        raise FileNotFoundError(f"No existe el directorio de MOD13C2 en {directorio}")
    rutas = sorted(directorio.glob("*.nc"))
    if not rutas:
        raise FileNotFoundError(f"No se encontraron archivos de MOD13C2 en {directorio}")

    cubo = mod13c2.cargar_cubo(directorio, INICIO, FIN)
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


def _cargar_malla_merra2_precipitacion(raw: Path) -> xr.DataArray:
    directorio = raw / "merra2_flx"
    if not directorio.is_dir():
        raise FileNotFoundError(f"No existe el directorio de MERRA-2 FLX en {directorio}")
    rutas = sorted(directorio.glob("*.nc"))
    if not rutas:
        raise FileNotFoundError(f"No se encontraron archivos de MERRA-2 FLX en {directorio}")
    por_mes: dict[pd.Period, Path] = {}
    for ruta in rutas:
        coincidencia = re.search(r"\.(\d{6})(?:_[^.]+)?\.nc$", ruta.name)
        if not coincidencia:
            continue
        mes = pd.Period(coincidencia.group(1), freq="M")
        if INICIO <= mes <= FIN:
            anterior = por_mes.get(mes)
            if (
                anterior is None
                or ruta.name.split(".")[0] > anterior.name.split(".")[0]
            ):
                por_mes[mes] = ruta
    esperados = pd.period_range(INICIO, FIN, freq="M")
    faltantes = [str(mes) for mes in esperados if mes not in por_mes]
    if faltantes:
        raise RuntimeError(
            f"Faltan meses MERRA-2 FLX en la ventana efectiva: {', '.join(faltantes)}"
        )
    partes = []
    for mes in esperados:
        with xr.open_dataset(por_mes[mes]) as dataset:
            if "PRECTOTCORR" not in dataset.variables:
                raise ValueError(f"No se encontró PRECTOTCORR en {por_mes[mes].name}")
            partes.append(dataset["PRECTOTCORR"].load())
    da = xr.concat(partes, dim="time").assign_coords(time=esperados.to_timestamp())
    return opusterra.merra2.precipitacion.mm_mes(da)


def _cargar_malla_imerg_precipitacion(raw: Path, region: Region) -> xr.DataArray:
    directorio = raw / "gpm_imerg"
    if not directorio.is_dir():
        if region.id == "honduras" and (ROOT / "data" / "raw" / "gpm_imerg").is_dir():
            directorio = ROOT / "data" / "raw" / "gpm_imerg"
        else:
            raise FileNotFoundError(f"No existe el directorio de GPM IMERG en {directorio}")
    rutas = sorted(directorio.glob("3B-MO*.nc"))
    if not rutas:
        raise FileNotFoundError(f"No se encontraron archivos de GPM IMERG en {directorio}")
    por_mes: dict[pd.Period, Path] = {}
    for ruta in rutas:
        coincidencia = re.search(r"\.(\d{4})(\d{2})\d{2}-", ruta.name)
        if not coincidencia:
            continue
        mes = pd.Period(f"{coincidencia.group(1)}-{coincidencia.group(2)}", freq="M")
        if INICIO <= mes <= FIN:
            por_mes[mes] = ruta
    esperados = pd.period_range(INICIO, FIN, freq="M")
    faltantes = [str(mes) for mes in esperados if mes not in por_mes]
    if faltantes:
        raise RuntimeError(
            f"Faltan meses GPM IMERG en la ventana efectiva: {', '.join(faltantes)}"
        )
    partes = []
    for mes in esperados:
        with xr.open_dataset(por_mes[mes]) as dataset:
            if "precipitation" not in dataset.variables:
                raise ValueError(f"No se encontró precipitation en {por_mes[mes].name}")
            p = dataset["precipitation"].load()
            unidad = p.attrs.get("units")
            if unidad != "mm/hr":
                raise ValueError(
                    f"Unidad inesperada en {por_mes[mes].name}: se esperaba 'mm/hr', pero se encontró '{unidad}'"
                )
            conv = gpm_mm_h_a_mm_mes(p.values, mes.year, mes.month)
            p_mes = p.copy(data=conv)
            p_mes.attrs["units"] = "mm/mes"
            p_mes.attrs["units_original"] = unidad
            p_mes.attrs["conversion"] = "opusterra.config.gpm_mm_h_a_mm_mes: mm/hr -> mm/mes"
            partes.append(p_mes)
    return (
        xr.concat(partes, dim="time")
        .assign_coords(time=esperados.to_timestamp())
        .transpose("time", "lat", "lon")
    )


def _actualizar_regiones(region: Region, variables: list[str]) -> None:
    ruta = OUTPUT / "regiones.json"
    if ruta.exists():
        contenido = json.loads(ruta.read_text(encoding="utf-8"))
        if not isinstance(contenido, list):
            raise ValueError(
                "frontend/public/data/regiones.json debe contener una lista."
            )
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
    ruta.write_text(
        json.dumps(actualizado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--region",
        default="honduras",
        help="Identificador de la región en datasets.toml",
    )
    args = parser.parse_args()
    region = _cargar_region(args.region)
    raw = ROOT / "data" / "raw" / region.id
    output = OUTPUT / region.id
    output.mkdir(parents=True, exist_ok=True)

    cuatro_variables = [
        "merra2_t2m",
        "merra2_precipitacion",
        "imerg_precipitacion",
        "mod13c2_ndvi",
    ]

    tareas = [
        (
            "merra2_t2m",
            "merra2_t2m.json",
            lambda: _analizar_malla(
                _cargar_malla_t2m(raw),
                ("merra2_t2m", "Temperatura del aire a 2 m"),
                "degC",
                "NASA MERRA-2 M2TMNXSLV v5.12.4",
                region=region,
            ),
        ),
        (
            "merra2_precipitacion",
            "merra2_precipitacion.json",
            lambda: _analizar_malla(
                _cargar_malla_merra2_precipitacion(raw),
                ("merra2_precipitacion", "Precipitación MERRA-2 PRECTOTCORR"),
                "mm/mes",
                "NASA MERRA-2 M2TMNXFLX v5.12.4",
                region=region,
            ),
        ),
        (
            "imerg_precipitacion",
            "imerg_precipitacion.json",
            lambda: _analizar_malla(
                _cargar_malla_imerg_precipitacion(raw, region),
                ("imerg_precipitacion", "Precipitación GPM IMERG"),
                "mm/mes",
                "NASA GPM IMERG v07",
                region=region,
            ),
        ),
        (
            "mod13c2_ndvi",
            "mod13c2_ndvi.json",
            lambda: _analizar_malla_mod13c2(raw, region),
        ),
        (
            "merra2_aer",
            "merra2_aer.json",
            lambda: _analizar_malla(
                _cargar_malla_aer(raw),
                ("merra2_aer", "Partículas en suspensión PM2.5 en superficie"),
                "µg/m³",
                "NASA MERRA-2 M2TMNXAER v5.12.4 (DUSMASS25)",
                region=region,
                contexto="Partículas en suspensión estimadas por el modelo MERRA-2; no es una medición de salud",
            ),
        ),
    ]

    generados: list[tuple[str, str, dict]] = []
    fallos: dict[str, str] = {}

    for var_id, nombre, generador in tareas:
        try:
            contenido = generador()
            generados.append((var_id, nombre, contenido))
        except (FileNotFoundError, RuntimeError, ValueError) as err:
            print(
                f"Aviso: Insumo no disponible o incompleto para {var_id} en {region.nombre} ({err}). Se omite esta variable."
            )
            fallos[var_id] = str(err)
        except Exception as err:
            print(
                f"Aviso: Error inesperado al procesar {var_id} en {region.nombre} ({err}). Se omite esta variable."
            )
            fallos[var_id] = str(err)

    variables_generadas = [var_id for var_id, _, _ in generados]
    _actualizar_regiones(region, variables_generadas)

    for var_id, nombre, contenido in generados:
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
        print(
            f"{nombre}: {contenido['pixeles_probados']} píxeles probados, {contenido['pixeles_significativos_fdr']} significativos FDR"
        )

    if region.id == "honduras":
        faltantes = [v for v in cuatro_variables if v not in variables_generadas]
        if faltantes:
            for f in faltantes:
                print(
                    f"FALLO HONDURAS: Variable {f} no se pudo generar. Motivo: {fallos.get(f, 'Desconocido')}"
                )
        else:
            print("Honduras: Las cuatro variables se generaron exitosamente.")


if __name__ == "__main__":
    main()
