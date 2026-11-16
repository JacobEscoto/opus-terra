"""Fronteras de países para limitar el análisis a un solo país.

Cuando el usuario elige un país (por ejemplo Honduras), las comparaciones solo
deben incluir celdas dentro de ese país. Los recortes de datos incluyen un
margen alrededor del bbox, así que traen celdas de países vecinos y del mar:
aquí se descartan usando la frontera de Natural Earth (dominio público).
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

RUTA_PAISES_POR_DEFECTO = Path(
    "data/external/natural-earth/ne_50m_admin_0_countries.geojson"
)
CAMPOS_NOMBRE = ("ADMIN", "NAME", "NAME_EN")


def _normalizar(texto: str) -> str:
    sin_acentos = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    )
    return sin_acentos.casefold().strip()


@lru_cache(maxsize=8)
def _cargar_frontera(ruta: str, pais: str) -> BaseGeometry:
    archivo = Path(ruta)
    if not archivo.is_file():
        raise FileNotFoundError(
            f"No existe el archivo de fronteras: {archivo}. Descarga "
            "ne_50m_admin_0_countries.geojson de Natural Earth y guárdalo ahí."
        )
    objetivo = _normalizar(pais)
    with archivo.open(encoding="utf-8") as f:
        paises = json.load(f)["features"]
    geometrias = [
        shape(p["geometry"])
        for p in paises
        if any(
            _normalizar(str(p["properties"].get(campo, ""))) == objetivo
            for campo in CAMPOS_NOMBRE
        )
    ]
    if not geometrias:
        raise ValueError(f'El país "{pais}" no existe en {archivo.name}.')
    frontera = unary_union(geometrias)
    shapely.prepare(frontera)  # acelera contains_xy en miles de puntos
    return frontera


def cargar_frontera(
    pais: str, ruta: str | Path = RUTA_PAISES_POR_DEFECTO
) -> BaseGeometry:
    """Devuelve la frontera del país (polígono o multipolígono)."""

    return _cargar_frontera(str(ruta), pais)


def celdas_en_pais(lat, lon, frontera: BaseGeometry) -> np.ndarray:
    """Máscara booleana: True si el centro de la celda queda dentro del país."""

    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    lon = np.where(lon > 180, lon - 360, lon)  # mallas 0-360 → -180-180
    return shapely.contains_xy(frontera, lon, lat)


def filtrar_columnas_en_pais(
    ancha: pd.DataFrame, frontera: BaseGeometry, pais: str
) -> tuple[pd.DataFrame, dict]:
    """Conserva solo las columnas `(lat, lon)` dentro del país.

    Devuelve la tabla filtrada y un bloque `alcance` auditable para el JSON.
    """

    dentro = celdas_en_pais(
        ancha.columns.get_level_values("lat"),
        ancha.columns.get_level_values("lon"),
        frontera,
    )
    if not dentro.any():
        raise ValueError(f"Ninguna celda de la malla cae dentro de {pais}.")
    alcance = {
        "tipo": "pais",
        "pais": pais,
        "criterio": "centro de la celda dentro de la frontera (Natural Earth 1:50m)",
        "celdas_malla": int(dentro.size),
        "celdas_dentro": int(dentro.sum()),
        "celdas_fuera": int((~dentro).sum()),
    }
    return ancha.loc[:, dentro], alcance
