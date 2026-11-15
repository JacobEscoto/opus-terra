# Decisión: OPeNDAP con recorte regional en lugar de descarga completa

## Fecha
2026-11-14 (durante la preparación del proyecto NASA Space Apps)

## Contexto
Los datos MERRA-2 son conjuntos globales: cada granula puede tener un tamaño estimado de ~380-400 MB (ver `datasets.toml`). Para una región pequeña como Honduras (bbox ≈ 410 km × 450 km), descargar el archivo global completaría transferencias innecesarias de datos que cubren océanos, continentes y regiones ajenas al interés del proyecto. Además, el tiempo de procesamiento y el consumo de almacenamiento serían multiples mayores al necesario.

## Decisión
Utilizar **OPeNDAP (OpenDAP / DAP2)** para solicitar solo las variables y las celdas de malla que intersectan el bounding box de Honduras (más un margen de 0.5°), en lugar de descargar y después recortar el archivo global. El flujo es:

1. Consultar CMR por la granula MERRA-2.
2. Obtener la URL `USE SERVICE API` con esquema `dap2://`.
3. Abrir el conjunto de datos remotamente mediante `xr.open_dataset(..., engine="pydap")`.
4. Aplicar el recorte espacial (`sel lat/lon`) y seleccionar solo las variables principales y auxiliares.
5. Guardar el subconjunto recortado en NetCDF local.

El tamaño estimado OPeNDAP por archivo es de 2.0 KB (T2M) o 1.5 KB (flux), frente a los ~380-400 MB del archivo global. El margen de 0.5° asegura que las celdas de los bordes no se pierdan durante el recorte (ver decisión sobre margen de bbox).

## Alternativas descartadas
- **Descarga global completa con `earthaccess.download()`:** Funciona pero genera archivos de cientos de MB para después arrojarlos fuera del bbox. Consume ancho de banda y espacio de almacenamiento de forma innecesaria. Además, los archivos globales MERRA-2 son tan grandes que la operación de descarga y después de borrar puede ser lenta en conexiones limitadas.
- **Recorte después de descargar el archivo global (post-procesamiento):** Descargar el archivo global y después aplicar `rioxarray` o `xarray .sel` para recortar. Aunque técnicamente posible, el paso de I/O de leer y volver a escribir un archivo de cientos de MB solo para quedarse con <1% de los datos es ineficiente en tiempo y almacenamiento temporal.

## Consecuencias
- **Ventaja:** Reducción drástica del tiempo de descarga (minutos en lugar de horas) y menor consumo de disco (MB en lugar de GB por producto). El flujo OPeNDAP es el modo por defecto en `download_data.py` cuando `--full-download` no se especifica.
- **Riesgo:** Dependencia de la disponibilidad y estabilidad del servicio OPeNDAP de CMR. Si el servicio OPeNDAP falla o está saturado, el flujo cae al modo de descarga global (cuando se usa `--full-download`).
- **Complejidad añadida:** Se requiere la dependencia `pydap` y se debe manejar el caso de excepción cuando `ImportError` ocurre (ver `recortar_opendap` en `download_data.py`). Se añade el margen de 0.5° que, aunque útil, incluye celdas fuera de la región estrictamente hondureña (mar adentro, países vecinos), lo que debe considerarse al interpretar la procedencia de los datos.
