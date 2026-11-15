from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from opusterra.lugares import _distancia_haversine

RUTA_PAISES = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "external"
    / "naturalearth"
    / "ne_10m_admin_0_countries.shp"
)

RADIO_CIUDAD_KM = 25.0


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
    if pais is None and _paises() is None:
        pais = _nombre_pais(cercano["cc"])

    return {
        "ciudad": (cercano["name"] or None) if cerca else None,
        "departamento": (cercano["admin1"] or None) if cerca else None,
        "pais": pais,
    }


def etiqueta(datos: dict) -> str:
    """Texto legible: «Cerca de Danlí, El Paraíso, Honduras»."""

    ciudad = datos.get("ciudad")
    partes = [datos.get("departamento"), datos.get("pais")]
    if ciudad:
        partes.insert(0, f"Cerca de {ciudad}")
    texto = ", ".join(parte for parte in partes if parte)
    return texto or "Zona sin nombre de lugar"
