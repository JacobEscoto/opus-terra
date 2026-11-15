"""Pruebas del nombrado geográfico de los puntos."""

from opusterra.lugares import cargar_lugares, nombrar_punto


def test_tegucigalpa_devuelve_lugar_de_francisco_morazan() -> None:
    lugares = cargar_lugares(
        "config/lugares_honduras.csv",
        bbox=(-89.4, 12.9, -83.1, 16.6),
    )

    nombre = nombrar_punto(14.07, -87.19, lugares)

    assert nombre.startswith("Cerca de ")
    tegucigalpa = next(lugar for lugar in lugares if lugar["nombre"] == "Tegucigalpa")
    assert tegucigalpa["departamento"] == "Francisco Morazán Department"


def test_un_punto_en_el_mar_devuelve_una_zona() -> None:
    lugares = cargar_lugares(
        "config/lugares_honduras.csv",
        bbox=(-89.4, 12.9, -83.1, 16.6),
    )

    nombre = nombrar_punto(13.0, -88.8, lugares)

    assert nombre.startswith("Zona ")
    assert "costera" in nombre


def test_el_radio_se_respeta() -> None:
    lugares = [{"nombre": "Referencia", "lat": 14.0, "lon": -87.0}]

    assert nombrar_punto(14.0, -87.0, lugares, radio_km=0) == "Cerca de Referencia"
    assert nombrar_punto(14.5, -87.0, lugares, radio_km=30).startswith("Zona ")
