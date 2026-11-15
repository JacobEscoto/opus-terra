"""Pruebas de alineación y remoción lineal del ONI."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from opusterra.enso import (
    RUTA_ONI_POR_DEFECTO,
    alinear_mensual,
    cargar_oni,
    remover_enso,
)

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[2]
RUTA_ONI_REAL = RAIZ_REPOSITORIO / RUTA_ONI_POR_DEFECTO


def _oni_sintetico(fechas: pd.DatetimeIndex) -> pd.Series:
    """Genera un ONI sintético con variación suficiente para una regresión."""

    return pd.Series(np.linspace(-1.5, 1.5, len(fechas)), index=fechas, name="ONI")


@pytest.mark.skipif(
    not RUTA_ONI_REAL.is_file(),
    reason=f"Falta el NetCDF ONI descargado en {RUTA_ONI_REAL}",
)
def test_cargar_oni_lee_el_archivo_real_y_reporta_metadatos() -> None:
    """El archivo entregado tiene variable, dimensiones y cobertura esperadas."""

    oni = cargar_oni(RUTA_ONI_REAL)

    assert oni.name == "Nino3.4"
    assert len(oni) == 372
    assert oni.index.freqstr == "MS"
    assert oni.index[0] == pd.Timestamp("1996-01-01")
    assert oni.index[-1] == pd.Timestamp("2026-12-01")
    assert oni.attrs["dimensiones"] == ("time",)
    assert oni.attrs["resolucion_temporal"] == "mensual"
    assert oni.attrs["unidades"] == "K"


def test_alinear_mensual_usa_año_mes_y_descarta_oni_excedente() -> None:
    """La alineación no depende del día exacto de cada timestamp."""

    fechas_serie = pd.to_datetime(["2001-01-15", "2001-02-20", "2001-03-10"])
    fechas_oni = pd.to_datetime(
        ["2000-12-01", "2001-01-01", "2001-02-01", "2001-03-01"]
    )
    serie = pd.Series([10.0, 20.0, 30.0], index=fechas_serie)
    oni = pd.Series([99.0, 1.0, 2.0, 3.0], index=fechas_oni)

    serie_alineada, oni_alineado = alinear_mensual(serie, oni)

    pd.testing.assert_index_equal(
        serie_alineada.index, pd.date_range("2001-01-01", periods=3, freq="MS")
    )
    np.testing.assert_allclose(oni_alineado, [1.0, 2.0, 3.0])


def test_alinear_mensual_falla_si_falta_un_mes() -> None:
    """Un mes sin pareja en el ONI se reporta explícitamente."""

    serie = pd.Series([1.0, 2.0], index=pd.to_datetime(["2001-01-01", "2001-02-01"]))
    oni = pd.Series([1.0], index=pd.to_datetime(["2001-01-01"]))

    with pytest.raises(ValueError, match="2001-02"):
        alinear_mensual(serie, oni)


def test_remover_enso_recupera_coeficiente_y_deja_residuos_sin_enso() -> None:
    """Una señal construida como 4 + 2*ONI + ruido recupera el efecto conocido."""

    fechas = pd.date_range("2000-01-01", periods=24, freq="MS")
    oni = _oni_sintetico(fechas)
    serie = pd.Series(4.0 + 2.0 * oni.to_numpy(), index=fechas, name="T2M")

    residuos, coeficiente, r2 = remover_enso(serie, oni)

    assert coeficiente == pytest.approx(2.0, abs=1e-2)
    assert r2 > 0.99
    # La correlación numérica de una serie casi exactamente nula no es estable;
    # comprobamos directamente que no queda amplitud residual.
    assert np.max(np.abs(residuos.to_numpy())) < 1e-12
    np.testing.assert_allclose(residuos.to_numpy(), 0.0, atol=1e-12)


def test_remover_enso_funciona_para_varias_series_y_reporta_cada_coeficiente() -> None:
    """Un DataFrame devuelve residuos, coeficientes y R² por columna."""

    fechas = pd.date_range("2000-01-01", periods=12, freq="MS")
    oni = _oni_sintetico(fechas)
    tabla = pd.DataFrame(
        {"a": 1.0 + oni, "b": 3.0 - 0.5 * oni},
        index=fechas,
    )

    residuos, coeficientes, r2 = remover_enso(tabla, oni)

    assert list(residuos.columns) == ["a", "b"]
    assert coeficientes["a"] == pytest.approx(1.0)
    assert coeficientes["b"] == pytest.approx(-0.5)
    assert r2["a"] == pytest.approx(1.0)
    assert r2["b"] == pytest.approx(1.0)
    np.testing.assert_allclose(residuos, 0.0, atol=1e-12)


def test_cargar_oni_rechaza_variable_no_esperada(tmp_path: Path) -> None:
    """Un archivo sin Nino3.4 produce un error comprensible."""

    ruta = tmp_path / "sin_oni.nc"
    xr.Dataset({"otra": ("time", [1.0, 2.0])}, coords={"time": [0, 1]}).to_netcdf(ruta)

    with pytest.raises(ValueError, match="Nino3.4"):
        cargar_oni(ruta)
