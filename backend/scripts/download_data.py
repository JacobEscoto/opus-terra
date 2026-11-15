#!/usr/bin/env python3
"""Descarga, convierte y verifica mallas mensuales de NASA."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse

import earthaccess
import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "backend" / "config" / "datasets.toml"
DEFAULT_OUTPUT = ROOT / "data" / "raw"


def cargar_entorno() -> None:
    """Carga un .env local sin imprimir ni persistir sus valores."""

    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for linea in env_path.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            import os

            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def cargar_config() -> dict:
    """Lee el catálogo TOML."""

    import tomllib

    with CONFIG_PATH.open("rb") as archivo:
        return tomllib.load(archivo)


def fecha_iso(valor: str, nombre: str) -> date:
    """Convierte una fecha ISO con un error en español."""

    try:
        return date.fromisoformat(valor)
    except ValueError as exc:
        raise ValueError(f"{nombre} no es una fecha ISO válida: {valor}") from exc


def nombre_remoto(granule) -> str:
    """Obtiene el nombre de archivo del primer enlace CMR."""

    enlaces = granule.data_links()
    if not enlaces:
        raise ValueError("La granula no tiene enlace de descarga")
    return Path(urlparse(enlaces[0]).path).name


def formato_salida(ruta: Path) -> str:
    """Clasifica una extensión nativa para el resumen."""

    extension = ruta.suffix.lower()
    return {
        ".nc": "NetCDF",
        ".nc4": "NetCDF4",
        ".hdf": "HDF4",
        ".h5": "HDF5",
        ".hdf5": "HDF5",
    }.get(extension, extension)


def mostrar_tamano_mb(mb: float) -> str:
    """Formatea tamaños pequeños y grandes sin ocultar los KB."""

    return f"{mb * 1024:.1f} KB" if mb < 1 else f"{mb:.2f} MB"


def recortar_cobertura(producto: dict, inicio: date, fin: date) -> tuple[date, date]:
    """Recorta el intervalo solicitado a la cobertura verificada."""

    efectivo_inicio = max(
        inicio, fecha_iso(producto["coverage_start"], "coverage_start")
    )
    efectivo_fin = min(fin, fecha_iso(producto["coverage_end"], "coverage_end"))
    if efectivo_inicio > efectivo_fin:
        raise ValueError("El rango solicitado no intersecta la cobertura del producto")
    return efectivo_inicio, efectivo_fin


def meses_esperados(inicio: date, fin: date) -> set[tuple[int, int]]:
    """Devuelve los meses del rango mensual efectivo."""

    meses = set()
    actual = date(inicio.year, inicio.month, 1)
    while actual <= fin:
        meses.add((actual.year, actual.month))
        actual = date(actual.year + actual.month // 12, actual.month % 12 + 1, 1)
    return meses


def mes_del_nombre(nombre: str) -> tuple[int, int] | None:
    """Extrae YYYY-MM de nombres MERRA, GPM o MODIS."""

    match = re.search(r"\.(19|20)(\d{2})(\d{2})\.(?:nc4|HDF5)$", nombre, re.I)
    if match:
        return int(match.group(1) + match.group(2)), int(match.group(3))
    match = re.search(r"\.(19|20)(\d{2})(\d{2})\d{2}-", nombre)
    if match:
        return int(match.group(1) + match.group(2)), int(match.group(3))
    match = re.search(r"\.A(20\d{2})(\d{3})\.", nombre)
    if match:
        fecha = date(int(match.group(1)), 1, 1) + timedelta(
            days=int(match.group(2)) - 1
        )
        return fecha.year, fecha.month
    return None


def mostrar_busqueda(
    granules: list, producto: dict, inicio: date, fin: date, usa_opendap: bool = False
) -> None:
    """Muestra el resultado de búsqueda y su cobertura efectiva."""

    nombres = [nombre_remoto(g) for g in granules]
    print(f"Archivos encontrados: {len(granules)}")
    print(f"Formato nativo detectado: {formato_salida(Path(nombres[0]))}")
    print(f"Cobertura efectiva: {inicio} a {fin}")
    print(f"Primer archivo: {nombres[0]}")
    print(f"Último archivo: {nombres[-1]}")
    if usa_opendap:
        total_mb = len(granules) * producto["estimated_opendap_kb_per_file"] / 1024
        print(
            f"Tamaño OPeNDAP estimado: {mostrar_tamano_mb(total_mb)} (recorte regional)"
        )
    else:
        total_gb = len(granules) * producto["estimated_file_size_mb"] / 1000
        print(f"Tamaño estimado: {total_gb:.2f} GB")


def guardar_encoding(dataset: xr.Dataset) -> tuple[xr.Dataset, dict]:
    """Prepara una copia y su encoding sin mutar el dataset original."""

    serializable = dataset.copy(deep=False)
    serializable.attrs = dict(dataset.attrs)
    for nombre in serializable.variables:
        serializable[nombre].attrs = dict(dataset[nombre].attrs)
    encoding = {}
    for atributos in [
        serializable.attrs,
        *(variable.attrs for variable in serializable.variables.values()),
    ]:
        for clave, valor in list(atributos.items()):
            if isinstance(valor, dict):
                # OPeNDAP puede devolver metadata DMRPP anidada, que NetCDF
                # no admite como atributo. Se conserva de forma legible.
                atributos[clave] = str(valor)
        if "_FillValue" in atributos:
            # CMR/OPeNDAP entrega a veces missing_value/fmissing_value con
            # otra precisión que _FillValue. Se conserva el valor CF canónico
            # y se eliminan los duplicados que provocan SerializationWarning.
            atributos.pop("missing_value", None)
            atributos.pop("fmissing_value", None)
    for nombre, variable in serializable.variables.items():
        valores = {}
        for clave in ("_FillValue", "scale_factor", "add_offset"):
            if clave in variable.attrs:
                valor = variable.attrs[clave]
                if clave != "add_offset" or valor != 0:
                    valores[clave] = valor
                variable.attrs.pop(clave)
        if valores:
            encoding[nombre] = valores
    return serializable, encoding


def escribir_netcdf(
    dataset: xr.Dataset,
    destino: Path,
    encoding: dict,
    variables: list[str] | None = None,
) -> None:
    """Escribe y valida un NetCDF mediante reemplazo atómico."""

    temporal = destino.with_name(destino.name + ".part")
    temporal.unlink(missing_ok=True)
    dataset.to_netcdf(temporal, engine="netcdf4", encoding=encoding)
    with xr.open_dataset(temporal, engine="netcdf4") as comprobacion:
        if variables and any(
            variable not in comprobacion.variables for variable in variables
        ):
            raise ValueError(
                f"El NetCDF no contiene todas las variables esperadas: {variables}"
            )
    temporal.replace(destino)


def recortar_malla(
    dataset: xr.Dataset, bbox: tuple[float, ...], margen: float
) -> xr.Dataset:
    """Recorta una malla 1-D usando sus coordenadas reales."""

    latitud = np.asarray(dataset["lat"].values)
    longitud = np.asarray(dataset["lon"].values)
    lon_min, lat_min, lon_max, lat_max = bbox
    if longitud.min() >= 0 and lon_min < 0:
        lon_min, lon_max = lon_min % 360, lon_max % 360
    lat_min, lat_max = lat_min - margen, lat_max + margen
    lon_min, lon_max = lon_min - margen, lon_max + margen
    lat_slice = (
        slice(lat_min, lat_max) if latitud[0] < latitud[-1] else slice(lat_max, lat_min)
    )
    lon_slice = (
        slice(lon_min, lon_max)
        if longitud[0] < longitud[-1]
        else slice(lon_max, lon_min)
    )
    resultado = dataset.sel(lat=lat_slice, lon=lon_slice).load()
    if not resultado.sizes.get("lat") or not resultado.sizes.get("lon"):
        raise ValueError("El bounding box no intersecta la malla")
    return resultado


def convertir_hdf5(
    origen: Path,
    destino: Path,
    bbox: tuple[float, ...] | None = None,
    margen: float = 0.0,
) -> None:
    """Convierte IMERG desde su grupo NetCDF4 interno a NetCDF."""

    with xr.open_dataset(
        origen, engine="netcdf4", group="Grid", decode_cf=False
    ) as dataset:
        dataset = dataset.load()
        if bbox is not None:
            dataset = recortar_malla(dataset, bbox, margen)
        dataset, encoding = guardar_encoding(dataset)
        escribir_netcdf(dataset, destino, encoding)


def convertir_modis(
    origen: Path, destino: Path, bbox: tuple[float, ...] | None = None
) -> None:
    """Convierte HDF-EOS2 MODIS a un NetCDF con todas sus SDS."""

    from pyhdf.SD import SD, SDC

    archivo = SD(str(origen), SDC.READ)
    datasets = {}
    encoding = {}
    nombres_modis = {
        "CMG 0.05 Deg Monthly NDVI": "ndvi",
        "CMG 0.05 Deg Monthly VI Quality": "ndvi_quality",
        "CMG 0.05 Deg Monthly pixel reliability": "ndvi_reliability",
    }
    for nombre in archivo.datasets():
        sds = archivo.select(nombre)
        info = sds.info()
        attrs = dict(sds.attributes())
        valores = np.asarray(sds[:])
        attrs_salida = dict(attrs)
        variable_encoding = {}
        for clave in ("_FillValue", "scale_factor", "add_offset"):
            if clave in attrs_salida:
                valor = attrs_salida.pop(clave)
                if clave != "add_offset" or valor != 0:
                    variable_encoding[clave] = valor
        if "scale_factor" in variable_encoding:
            # xarray escribe valores físicos y conserva el factor para que el
            # NetCDF almacene los valores crudos originales.
            relleno = variable_encoding.get("_FillValue")
            valores = valores.astype(np.float32)
            if relleno is not None:
                valores[valores == relleno] = np.nan
            valores /= variable_encoding["scale_factor"]
            variable_encoding["dtype"] = "float32"
        nombre_salida = nombres_modis.get(nombre, nombre)
        attrs_salida["original_name"] = nombre
        datasets[nombre_salida] = xr.DataArray(
            valores, dims=("lat", "lon"), attrs=attrs_salida
        )
        if variable_encoding:
            encoding[nombre_salida] = variable_encoding
        sds.endaccess()
    archivo.end()

    lat = 89.975 - np.arange(3600) * 0.05
    lon = -179.975 + np.arange(7200) * 0.05
    if bbox is not None:
        lon_min, lat_min, lon_max, lat_max = bbox
        filas = np.where((lat >= lat_min) & (lat <= lat_max))[0]
        columnas = np.where((lon >= lon_min) & (lon <= lon_max))[0]
        if not len(filas) or not len(columnas):
            raise ValueError("El bounding box no intersecta la malla MOD13C2")
        for nombre, variable in list(datasets.items()):
            if variable.ndim != 2:
                raise ValueError(f"SDS MODIS no espacial: {variable.name}")
            datasets[nombre] = xr.DataArray(
                variable.values[np.ix_(filas, columnas)],
                dims=("lat", "lon"),
                attrs=variable.attrs,
            )
        lat = lat[filas]
        lon = lon[columnas]
    dataset = xr.Dataset(datasets, coords={"lat": lat, "lon": lon})
    dataset.lat.attrs["units"] = "degrees_north"
    dataset.lon.attrs["units"] = "degrees_east"
    dataset.attrs = {
        clave: str(valor) if isinstance(valor, dict) else valor
        for clave, valor in dataset.attrs.items()
    }
    escribir_netcdf(dataset, destino, encoding)


def convertir(
    origen: Path, destino: Path, producto: dict, bbox: tuple[float, ...] | None = None
) -> None:
    """Convierte una granula no NetCDF según su formato configurado."""

    if producto["native_format"] == "HDF5":
        convertir_hdf5(
            origen, destino, bbox, float(producto.get("crop_margin_degrees", 0.0))
        )
    elif producto["native_format"] == "HDF-EOS2":
        convertir_modis(origen, destino, bbox)
    else:
        raise ValueError(
            f"No hay conversor configurado para {producto['native_format']}"
        )


def abrir_netcdf(ruta: Path, producto: dict) -> xr.Dataset:
    """Abre un NetCDF normalizado, incluyendo grupos IMERG ya convertidos."""

    return xr.open_dataset(ruta, engine="netcdf4", decode_cf=False)


def netcdf_valido(ruta: Path, producto: dict) -> bool:
    """Comprueba que un NetCDF terminado contiene la variable principal."""

    try:
        with xr.open_dataset(ruta, engine="netcdf4") as dataset:
            return ruta.is_file() and producto["main_variable"] in dataset.variables
    except Exception:
        return False


def geotiff_valido(ruta: Path) -> bool:
    """Comprueba que un GeoTIFF terminado se puede abrir."""

    try:
        import rioxarray

        with rioxarray.open_rasterio(ruta, masked=True) as raster:
            return ruta.is_file() and raster.rio.crs is not None and raster.size > 0
    except Exception:
        return False


def url_opendap(granule) -> str:
    """Obtiene la URL USE SERVICE API de la granula."""

    enlaces = granule.get("umm", {}).get("RelatedUrls", [])
    for enlace in enlaces:
        url = enlace.get("URL", "")
        if enlace.get("Type") == "USE SERVICE API" and "opendap" in url.lower():
            # El esquema explícito evita la negociación DAP implícita de
            # PyDAP sin pasar argumentos que xarray no acepta en su backend.
            return url.replace("https://", "dap2://", 1)
    tipos = ", ".join(str(enlace.get("Type")) for enlace in enlaces)
    raise ValueError(f"La granula MERRA-2 no publicó una URL OPeNDAP; enlaces: {tipos}")


def recortar_opendap(
    granule, producto: dict, bbox: tuple[float, ...], destino: Path
) -> None:
    """Descarga solo variables y celdas de la región mediante OPeNDAP."""

    variables = [producto["main_variable"], *producto["auxiliary_variables"]]
    try:
        remoto = xr.open_dataset(
            url_opendap(granule),
            engine="pydap",
            decode_cf=False,
            backend_kwargs={"session": earthaccess.get_requests_https_session()},
        )
    except ImportError as exc:
        raise RuntimeError("Falta la dependencia pydap para OPeNDAP") from exc
    try:
        latitud = np.asarray(remoto["lat"].values)
        longitud = np.asarray(remoto["lon"].values)
        margen = float(producto.get("opendap_margin_degrees", 0.5))
        lon_min, lat_min, lon_max, lat_max = bbox
        # Algunas granulas usan [-180, 180] y otras [0, 360].
        if longitud.min() >= 0 and lon_min < 0:
            lon_min, lon_max = lon_min % 360, lon_max % 360
        lat_min, lat_max = lat_min - margen, lat_max + margen
        lon_min, lon_max = lon_min - margen, lon_max + margen
        lat_slice = (
            slice(lat_min, lat_max)
            if latitud[0] < latitud[-1]
            else slice(lat_max, lat_min)
        )
        lon_slice = (
            slice(lon_min, lon_max)
            if longitud[0] < longitud[-1]
            else slice(lon_max, lon_min)
        )
        disponibles = set(remoto.variables)
        faltantes = [variable for variable in variables if variable not in disponibles]
        if faltantes:
            raise ValueError(f"Variables MERRA-2 ausentes en OPeNDAP: {faltantes}")
        subset = remoto[variables].sel(lat=lat_slice, lon=lon_slice).load()
        subset, encoding = guardar_encoding(subset)
        escribir_netcdf(subset, destino, encoding, variables)
    finally:
        remoto.close()


def verificar_coherencia(ruta_nc: Path, ruta_tif: Path, producto: dict) -> None:
    """Compara la celda de Tegucigalpa en NetCDF y GeoTIFF."""

    import rioxarray

    with xr.open_dataset(ruta_nc, engine="netcdf4") as dataset:
        valor_nc = (
            dataset[producto["main_variable"]]
            .sel(lat=14.07, lon=-87.19, method="nearest")
            .values
        )
    with rioxarray.open_rasterio(ruta_tif, masked=True) as raster:
        valor_tif = raster.sel(x=-87.19, y=14.07, method="nearest").values
    valor_nc = float(np.asarray(valor_nc).squeeze())
    valor_tif = float(np.asarray(valor_tif).squeeze())
    minimo, maximo = producto.get("plausible_range", [-np.inf, np.inf])
    coincide = np.isclose(valor_nc, valor_tif, rtol=1e-5, atol=1e-6)
    plausible = minimo <= valor_nc <= maximo and minimo <= valor_tif <= maximo
    print(
        f"Coherencia Tegucigalpa: NetCDF={valor_nc:.6g}, GeoTIFF={valor_tif:.6g}, "
        f"coinciden={'sí' if coincide else 'NO'}, plausibles={'sí' if plausible else 'NO'}"
    )


def verificar_netcdf(ruta: Path, producto: dict) -> None:
    """Muestra variables, dimensiones y atributos científicos de una muestra."""

    print(f"\nVerificación NetCDF: {ruta.name}")
    try:
        with abrir_netcdf(ruta, producto) as dataset:
            print(f"Variables: {list(dataset.data_vars)}")
            print(f"Dimensiones: {dict(dataset.sizes)}")
            print(f"Coordenadas: {list(dataset.coords)}")
            for nombre in [producto["main_variable"], *producto["auxiliary_variables"]]:
                if nombre not in dataset.variables:
                    continue
                variable = dataset[nombre]
                print(
                    f"{nombre}: unidades={variable.attrs.get('units')}, "
                    f"_FillValue={variable.attrs.get('_FillValue')}, "
                    f"scale_factor={variable.attrs.get('scale_factor')}"
                )
            if producto["main_variable"] not in dataset.variables:
                print(
                    f"AVISO: no existe '{producto['main_variable']}'. "
                    f"Disponibles: {list(dataset.variables)}"
                )
            qa = [
                n
                for n in dataset.variables
                if "quality" in n.lower()
                or "qa" in n.lower()
                or "reliability" in n.lower()
            ]
            if qa:
                print(f"Variables QA detectadas: {qa}")
    except Exception as exc:
        print(f"AVISO: no se pudo abrir la muestra NetCDF: {exc}")


def geotiff_desde_netcdf(ruta_nc: Path, ruta_tif: Path, producto: dict) -> None:
    """Genera un GeoTIFF local con rioxarray como respaldo."""

    import rioxarray

    # Para GeoTIFF se escriben valores físicos; esto es importante para NDVI,
    # cuyo NetCDF conserva scale_factor=10000 para los datos crudos.
    with xr.open_dataset(ruta_nc, engine="netcdf4", decode_cf=True) as dataset:
        variable = dataset[producto["main_variable"]]
        if "time" in variable.dims:
            variable = variable.isel(time=0)
        variable = variable.squeeze(drop=True)
        # rioxarray interpreta scale_factor como una nueva transformación;
        # aquí xarray ya decodificó NDVI, por lo que el GeoTIFF debe guardar
        # directamente el valor físico.
        variable.attrs.pop("scale_factor", None)
        variable.attrs.pop("add_offset", None)
        variable.encoding.pop("scale_factor", None)
        variable.encoding.pop("add_offset", None)
        if variable.dims != ("lat", "lon"):
            print(
                f"GeoTIFF: se transpuso el orden espacial {variable.dims} a ('lat', 'lon')"
            )
        variable = variable.transpose("lat", "lon")
        variable = variable.rio.set_spatial_dims(
            x_dim="lon", y_dim="lat", inplace=False
        )
        variable = variable.rio.write_crs("EPSG:4326", inplace=False)
        ruta_tif.parent.mkdir(parents=True, exist_ok=True)
        temporal = ruta_tif.with_name(ruta_tif.stem + ".part.tif")
        temporal.unlink(missing_ok=True)
        variable.rio.to_raster(temporal)
        if not geotiff_valido(temporal):
            raise ValueError(f"GeoTIFF temporal inválido: {temporal.name}")
        temporal.replace(ruta_tif)


def procesar_merra_opendap(
    granules: list,
    nombre: str,
    producto: dict,
    args,
    bbox: tuple[float, ...],
    efectivo_inicio: date,
    efectivo_fin: date,
) -> tuple[int, dict]:
    """Procesa MERRA-2 por granula, sin descargar el archivo global."""

    salida = args.output_dir / producto["output_folder"]
    salida.mkdir(parents=True, exist_ok=True)
    geotiff = salida / "geotiff"
    contadores = {
        "descargados": 0,
        "convertidos": 0,
        "omitidos": 0,
        "fallidos": 0,
        "geotiff": 0,
    }
    encontrados = set()
    muestra = None
    for granule in granules:
        remoto = nombre_remoto(granule)
        mes = mes_del_nombre(remoto)
        destino = salida / f"{Path(remoto).stem}_{args.region}.nc"
        tif = geotiff / f"{destino.stem}.tif"
        nc_ok = netcdf_valido(destino, producto)
        tif_ok = geotiff_valido(tif)
        requiere_nc = args.format in ("nc", "both") or not tif_ok
        requiere_tif = args.format in ("geotiff", "both")
        if (not requiere_nc or nc_ok) and (not requiere_tif or tif_ok):
            contadores["omitidos"] += 1
            muestra = muestra or destino if nc_ok else muestra
            if mes:
                encontrados.add(mes)
            continue
        try:
            if not nc_ok:
                destino.unlink(missing_ok=True)
                recortar_opendap(granule, producto, bbox, destino)
                contadores["descargados"] += 1
                nc_ok = True
            if args.format in ("geotiff", "both"):
                if not tif_ok:
                    geotiff_desde_netcdf(destino, tif, producto)
                    contadores["geotiff"] += 1
                    tif_ok = True
            if nc_ok:
                muestra = muestra or destino
            if mes and ((not requiere_nc or nc_ok) and (not requiere_tif or tif_ok)):
                encontrados.add(mes)
        except Exception as exc:
            contadores["fallidos"] += 1
            print(f"FALLÓ OPeNDAP {remoto}: {exc}")
    faltantes = meses_esperados(efectivo_inicio, efectivo_fin) - encontrados
    estimado_mb = len(granules) * producto["estimated_opendap_kb_per_file"] / 1024
    print(
        f"\nResumen {nombre} OPeNDAP: archivos recortados={contadores['descargados']}, "
        f"omitidos={contadores['omitidos']}, fallidos={contadores['fallidos']}, "
        f"GeoTIFF={contadores['geotiff']}"
    )
    print(f"Tamaño OPeNDAP estimado: {mostrar_tamano_mb(estimado_mb)}")
    print(f"Rango efectivo: {efectivo_inicio} a {efectivo_fin}")
    print(
        "Meses faltantes: "
        + (
            ", ".join(f"{y:04d}-{m:02d}" for y, m in sorted(faltantes))
            if faltantes
            else "ninguno"
        )
    )
    if muestra and args.format in ("nc", "both"):
        verificar_netcdf(muestra, producto)
        if args.format == "both":
            verificar_coherencia(muestra, geotiff / f"{muestra.stem}.tif", producto)
    return (4 if contadores["fallidos"] or faltantes else 0), contadores


def crear_parser() -> argparse.ArgumentParser:
    """Construye la CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", required=True, help="Clave del producto o all")
    parser.add_argument("--region", default="honduras")
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--format", choices=("nc", "geotiff", "both"), default="nc")
    parser.add_argument(
        "--full-download",
        action="store_true",
        help="Descarga global completa de MERRA-2",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def procesar_producto(
    nombre: str, producto: dict, args, inicio: date, fin: date
) -> tuple[int, dict]:
    """Busca y procesa un producto; devuelve código y contadores."""

    efectivo_inicio, efectivo_fin = recortar_cobertura(producto, inicio, fin)
    bbox = tuple(args.config["regions"][args.region]["bbox"])
    granules = earthaccess.search_data(
        short_name=producto["short_name"],
        version=producto["version"],
        temporal=(efectivo_inicio.isoformat(), efectivo_fin.isoformat()),
        bounding_box=bbox,
        count=-1,
    )
    if not granules:
        print(f"ERROR: no hubo resultados para {nombre}", file=sys.stderr)
        return 2, {"fallidos": 1}
    usa_opendap = nombre.startswith("merra2_") and not args.full_download
    mostrar_busqueda(granules, producto, efectivo_inicio, efectivo_fin, usa_opendap)
    if args.dry_run:
        return 0, {"efectivo": (efectivo_inicio, efectivo_fin)}

    salida = args.output_dir / producto["output_folder"]
    salida.mkdir(parents=True, exist_ok=True)
    original = salida / "original"
    geotiff = salida / "geotiff"
    if usa_opendap:
        return procesar_merra_opendap(
            granules, nombre, producto, args, bbox, efectivo_inicio, efectivo_fin
        )
    if producto["native_format"] not in ("NetCDF", "NetCDF4"):
        original.mkdir(exist_ok=True)
    contadores = {
        "descargados": 0,
        "convertidos": 0,
        "omitidos": 0,
        "fallidos": 0,
        "geotiff": 0,
    }
    muestra = None
    encontrados = set()
    for granule in granules:
        remoto = nombre_remoto(granule)
        mes = mes_del_nombre(remoto)
        destino_nc = salida / f"{Path(remoto).stem}.nc"
        destino_tif = geotiff / f"{destino_nc.stem}.tif"
        nc_ok = netcdf_valido(destino_nc, producto)
        tif_ok = geotiff_valido(destino_tif)
        requiere_nc = args.format in ("nc", "both") or not tif_ok
        requiere_tif = args.format in ("geotiff", "both")
        if (not requiere_nc or nc_ok) and (not requiere_tif or tif_ok):
            contadores["omitidos"] += 1
            if nc_ok:
                muestra = muestra or destino_nc
            if mes:
                encontrados.add(mes)
            continue
        destino_original = (
            original / remoto
            if producto["native_format"] not in ("NetCDF", "NetCDF4")
            else None
        )
        try:
            if destino_original and destino_original.exists():
                archivo = destino_original
                contadores["omitidos"] += 1
            else:
                rutas = earthaccess.download(
                    granule,
                    local_path=original if destino_original else salida,
                    threads=1,
                )
                if not rutas:
                    raise ValueError("earthaccess.download no devolvió archivos")
                archivo = Path(rutas[0])
                if not archivo.is_file() or archivo.stat().st_size == 0:
                    raise ValueError(
                        "La descarga produjo un archivo vacío o inexistente"
                    )
                contadores["descargados"] += 1
                if destino_original and archivo != destino_original:
                    archivo.rename(destino_original)
                    archivo = destino_original
            if not nc_ok:
                destino_nc.unlink(missing_ok=True)
                if producto["native_format"] in ("NetCDF", "NetCDF4"):
                    archivo.rename(destino_nc)
                else:
                    convertir(archivo, destino_nc, producto, bbox)
                    contadores["convertidos"] += 1
                nc_ok = netcdf_valido(destino_nc, producto)
                if not nc_ok:
                    raise ValueError(
                        f"NetCDF inválido o sin {producto['main_variable']}"
                    )
            muestra = muestra or destino_nc
            if args.format in ("geotiff", "both"):
                if not tif_ok:
                    geotiff_desde_netcdf(destino_nc, destino_tif, producto)
                    contadores["geotiff"] += 1
                    tif_ok = True
            if mes and ((not requiere_nc or nc_ok) and (not requiere_tif or tif_ok)):
                encontrados.add(mes)
        except Exception as exc:
            contadores["fallidos"] += 1
            print(f"FALLÓ {remoto}: {exc}")
    faltantes = meses_esperados(efectivo_inicio, efectivo_fin) - encontrados
    print(
        f"\nResumen {nombre}: descargados={contadores['descargados']}, convertidos={contadores['convertidos']}, omitidos={contadores['omitidos']}, fallidos={contadores['fallidos']}, GeoTIFF={contadores['geotiff']}"
    )
    print(f"Rango efectivo: {efectivo_inicio} a {efectivo_fin}")
    print(
        "Meses faltantes: "
        + (
            ", ".join(f"{y:04d}-{m:02d}" for y, m in sorted(faltantes))
            if faltantes
            else "ninguno"
        )
    )
    if muestra:
        verificar_netcdf(muestra, producto)
        if args.format == "both":
            verificar_coherencia(muestra, geotiff / f"{muestra.stem}.tif", producto)
    return (4 if contadores["fallidos"] or faltantes else 0), contadores


def main() -> int:
    """Punto de entrada."""

    args = crear_parser().parse_args()
    try:
        cargar_entorno()
        args.config = cargar_config()
        if args.region not in args.config["regions"]:
            raise ValueError(f"Región desconocida: {args.region}")
        inicio = fecha_iso(args.start or args.config["defaults"]["start"], "--start")
        fin = fecha_iso(args.end or args.config["defaults"]["end"], "--end")
        if inicio > fin:
            raise ValueError("--start no puede ser posterior a --end")
        nombres = list(args.config["products"])
        seleccionados = nombres if args.product == "all" else [args.product]
        desconocidos = [n for n in seleccionados if n not in args.config["products"]]
        if desconocidos:
            raise ValueError(f"Productos desconocidos: {', '.join(desconocidos)}")
        earthaccess.login()
        if args.dry_run:
            print("Dry-run: no se descargarán archivos.")
        codigos = []
        for nombre in seleccionados:
            codigo, _ = procesar_producto(
                nombre, args.config["products"][nombre], args, inicio, fin
            )
            codigos.append(codigo)
        return max(codigos, default=0)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
