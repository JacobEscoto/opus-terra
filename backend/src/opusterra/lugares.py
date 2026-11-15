"""Catálogo de lugares y nombres legibles para puntos del análisis."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterable


class LugarCatalogo(list[dict]):
    """Lista de lugares que conserva el bbox de la región de origen."""

    def __init__(
        self,
        lugares: Iterable[dict] = (),
        *,
        bbox: tuple[float, float, float, float] | None = None,
    ) -> None:
        super().__init__(lugares)
        self.bbox = bbox


def cargar_lugares(
    ruta: str | Path,
    bbox: tuple[float, float, float, float] | None = None,
) -> LugarCatalogo:
    """Carga un CSV de GeoNames, ignorando los comentarios de cabecera."""

    with Path(ruta).open(encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(
            linea for linea in archivo if not linea.lstrip().startswith("#")
        )
        lugares = [
            {
                "nombre": fila["nombre"],
                "departamento": fila["departamento"],
                "lat": float(fila["lat"]),
                "lon": float(fila["lon"]),
                "poblacion": int(fila["poblacion"]),
            }
            for fila in lector
        ]
    return LugarCatalogo(lugares, bbox=bbox)


def _distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radio_tierra_km = 6371.0088
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    return 2 * radio_tierra_km * math.asin(math.sqrt(a))


def _bbox_de_lugares(lugares: list[dict]) -> tuple[float, float, float, float]:
    if not lugares:
        return (-180.0, -90.0, 180.0, 90.0)
    lons = [float(lugar["lon"]) for lugar in lugares]
    lats = [float(lugar["lat"]) for lugar in lugares]
    return min(lons), min(lats), max(lons), max(lats)


def _descripcion_zona(lat: float, lon: float, lugares: list[dict]) -> str:
    bbox = getattr(lugares, "bbox", None) or _bbox_de_lugares(lugares)
    lon_min, lat_min, lon_max, lat_max = bbox
    rango_lat = lat_max - lat_min or 1.0
    posicion_lat = (lat - lat_min) / rango_lat
    if posicion_lat < 1 / 3:
        orientacion = "sur"
    elif posicion_lat > 2 / 3:
        orientacion = "norte"
    else:
        orientacion = "centro"

    # El borde norte o sur del bbox representa la franja costera principal.
    # Para una lista normal (sin bbox) esto también ofrece un fallback estable.
    costa = posicion_lat <= 0.2 or posicion_lat >= 0.8
    tipo = "costera" if costa else "interior"
    return f"Zona {orientacion} {tipo}"


def nombrar_punto(
    lat: float,
    lon: float,
    lugares: list[dict],
    radio_km: float = 30,
) -> str:
    """Devuelve el lugar poblado más cercano o una descripción de zona."""

    if radio_km < 0:
        raise ValueError("radio_km debe ser no negativo")
    candidatos = (
        (
            _distancia_haversine(lat, lon, float(lugar["lat"]), float(lugar["lon"])),
            lugar,
        )
        for lugar in lugares
    )
    cercano = min(candidatos, key=lambda par: par[0], default=None)
    if cercano is not None and cercano[0] <= radio_km:
        return f"Cerca de {cercano[1]['nombre']}"
    return _descripcion_zona(lat, lon, lugares)
