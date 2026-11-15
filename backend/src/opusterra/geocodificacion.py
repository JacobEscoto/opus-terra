from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

RUTA_PAISES = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "external"
    / "naturalearth"
    / "ne_10m_admin_0_countries.shp"
)

RADIO_CIUDAD_KM = 60.0


def _distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radio_tierra_km = 6371.0088
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radio_tierra_km * c


@lru_cache(maxsize=1)
def _paises():
    """Carga una sola vez los polígonos de países; `None` si no hay shapefile."""

    if not RUTA_PAISES.is_file():
        return None
    import geopandas as gpd

    tabla = gpd.read_file(RUTA_PAISES)
    columna = "NAME_ES" if "NAME_ES" in tabla.columns else "NAME"
    tabla = tabla[[columna, "geometry"]].rename(columns={columna: "nombre"})
    tabla.sindex  # construye el índice espacial ahora, no en la primera consulta
    return tabla


def pais_de(lat: float, lon: float) -> str | None:
    """País cuyo polígono contiene el punto; `None` en mar abierto o sin shapefile."""

    tabla = _paises()
    if tabla is None:
        return None
    from shapely.geometry import Point

    indices = tabla.sindex.query(Point(lon, lat), predicate="within")
    if len(indices) == 0:
        return None
    return str(tabla.iloc[int(indices[0])]["nombre"])


def _nombre_pais(codigo_iso: str) -> str:
    """Nombre en español de un país a partir de su código ISO de dos letras."""

    try:
        from babel import Locale

        return Locale("es").territories.get(codigo_iso, codigo_iso)
    except Exception:
        return codigo_iso


def ubicacion(lat: float, lon: float, radio_km: float = RADIO_CIUDAD_KM) -> dict:
    """Devuelve `{"ciudad", "departamento", "pais"}`; cada valor puede ser `None`."""

    import reverse_geocoder as rg

    # mode=1 evita el multiproceso, que da problemas en Windows y en pytest.
    cercano = rg.search((lat, lon), mode=1)[0]
    distancia = _distancia_haversine(
        lat, lon, float(cercano["lat"]), float(cercano["lon"])
    )
    cerca = distancia <= radio_km

    pais = pais_de(lat, lon)
    if pais is None:
        pais = _nombre_pais(cercano["cc"])

    return {
        "ciudad": (cercano["name"] or None) if cerca else None,
        "departamento": cercano["admin1"] or None,
        "pais": pais,
    }


def etiqueta(datos: dict) -> str:
    """Texto legible: «Cerca de Danlí, El Paraíso, Honduras» o «Departamento, País»."""

    ciudad = datos.get("ciudad")
    partes = [datos.get("departamento"), datos.get("pais")]
    if ciudad:
        partes.insert(0, f"Cerca de {ciudad}")
    texto = ", ".join(parte for parte in partes if parte)
    return texto
