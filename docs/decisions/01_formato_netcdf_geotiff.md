# Decisión: Formato NetCDF con GeoTIFF de respaldo

## Fecha
2026-11-14 (durante la preparación del proyecto NASA Space Apps)

## Contexto
El proyecto requiere entregar datos climáticos que puedan ser tanto analizados científicamente como visualizados en herramientas SIG. Se deben elegir formatos que garanticen compatibilidad con herramientas de análisis de series temporales (Python, R) y, al mismo tiempo, permitan ser visualizados en mapas (QGIS, ArcGIS, Earth Viewer). Los datos vienen de fuentes con formatos nativos diversos: HDF5 (GPM), HDF-EOS2 (MODIS), y NetCDF4 (MERRA-2).

## Decisión
- **Formato principal: NetCDF4** (con encoding CF-friendly). Es el formato de intercambio estándar para datos climáticos y meteorológicos, compatible con `xarray`, `cdt`, y la mayoría de librerías de análisis de series temporales. Se preservan metadatos (unidades, _FillValue, scale_factor, add_offset) y las dimensiones temporales y espaciales de forma nativa.
- **Formato de respaldo: GeoTIFF**. Se genera un GeoTIFF por producto a partir del NetCDF resultante, usando `rioxarray` para escribir valores físicos (se descalean los factores de escala). El GeoTIFF permite visualización directa en cualquier software SIG y es el formato de referencia para muchos visores de mapas 3D. Se conserva la CRS EPSG:4326 y las dimensiones espaciales (lat/lon).

## Alternativas descartadas
- **Solo NetCDF:** El GeoTIFF tendría que generarse sobre la marcha por el usuario final, lo que añade complejidad y depende de que el usuario tenga las librerías adecuadas. Se descarta porque el proyecto debería proveer un archivo listo para usar.
- **Solo GeoTIFF:** Se pierde la estructura multidimensional (dimensión `time`) y los metadatos CF son más difíciles de preservar en un raster de una sola banda. Se descarta porque el análisis requiere manipular series temporales en Python.
- **Formato propietario (HDF5/HDF-EOS2):** Mantener los formatos nativos requeriría que el usuario instale librerías específicas (pyhdf) y limitaría la portabilidad. Se descarta por consideraciones de accesibilidad.

## Consecuencias
- Los archivos de salida llevan tanto un `.nc` (NetCDF) como un `.tif` (GeoTIFF) en la misma estructura de carpetas.
- Aumenta el espacio de almacenamiento necesario (aprox. 1.5x por producto, ya que se guardan ambos formatos), pero se gana flexibilidad para el usuario.
- El pipeline de `download_data.py` ya incluye la conversión `geotiff_desde_netcdf` como paso estándar (ver `convertir` → `convertir_hdf5/convertir_modis` y `geotiff_desde_netcdf`).
- Se deben manejar los `scale_factor` y `add_offset` adecuadamente: en el NetCDF se conservan para datos crudos, y se removem para el GeoTIFF (que guarda valores físicos).
