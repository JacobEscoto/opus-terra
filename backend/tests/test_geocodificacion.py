import pytest

from opusterra.geocodificacion import etiqueta


def test_etiqueta_completa():
    datos = {"ciudad": "Danlí", "departamento": "El Paraíso", "pais": "Honduras"}
    assert etiqueta(datos) == "Cerca de Danlí, El Paraíso, Honduras"


def test_etiqueta_sin_ciudad_usa_departamento_y_pais():
    datos = {"ciudad": None, "departamento": "Gracias a Dios", "pais": "Honduras"}
    assert etiqueta(datos) == "Gracias a Dios, Honduras"


def test_etiqueta_sin_ciudad_usa_pais():
    datos = {"ciudad": None, "departamento": None, "pais": "Nicaragua"}
    assert etiqueta(datos) == "Nicaragua"


def test_etiqueta_sin_datos():
    datos = {"ciudad": None, "departamento": None, "pais": None}
    assert etiqueta(datos) == ""


def test_ubicacion_tegucigalpa():
    pytest.importorskip("reverse_geocoder")
    from opusterra.geocodificacion import ubicacion

    resultado = ubicacion(14.0818, -87.2068)
    assert resultado["ciudad"] == "Tegucigalpa"
    assert resultado["pais"] == "Honduras"


def test_ubicacion_sin_ciudad_cercana_conserva_departamento():
    pytest.importorskip("reverse_geocoder")
    from opusterra.geocodificacion import etiqueta, ubicacion

    # Punto en Gracias a Dios a más de 80 km de Puerto Lempira (fuera de los 60 km)
    resultado = ubicacion(16.0, -83.5)
    assert resultado["ciudad"] is None
    assert resultado["departamento"] == "Gracias a Dios"
    assert resultado["pais"] == "Honduras"
    assert etiqueta(resultado) == "Gracias a Dios, Honduras"


def test_ubicacion_lejos_de_todo_no_inventa_ciudad():
    pytest.importorskip("reverse_geocoder")
    from opusterra.geocodificacion import ubicacion

    # Atlántico central: ninguna ciudad dentro de 60 km.
    resultado = ubicacion(30.0, -40.0)
    assert resultado["ciudad"] is None
