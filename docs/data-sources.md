# Fuentes de datos

Tabla con los productos principales utilizados en el análisis. Los datos verificados provienen de la configuración `backend/config/datasets.toml` y de los metadatos CMR asociados a cada short name. Si algún campo no fue verificado contra CMR, está marcado como **pendiente**.

| Producto | Nombre corto CMR | Versión | Cobertura real | Resolución | Centro de distribución | Formato nativo | Cita requerida |
|----------|-----------------|---------|---------------|------------|------------------------|----------------|----------------|
| GPM IMERG v07 | GPM_3IMERGM | 07 | 1998-01-01 a 2025-09-30 | 0.1 x 0.1 grados | GES DISC | HDF5 | [1] |
| MERRA-2 flux (PRECTOTCORR) | M2TMNXFLX | 5.12.4 | 1996-01-01 a 2026-09-30 | 0.625° lon x 0.5° lat | GES DISC | NetCDF4 | [2] |
| MERRA-2 superficie (T2M) | M2TMNXSLV | 5.12.4 | 1996-01-01 a 2026-09-30 | 0.625° lon x 0.5° lat | GES DISC | NetCDF4 | [2] |
| MODIS MOD13C2 v061 | MOD13C2 | 061 | 2000-02-01 a 2026-10-31 | 0.05 x 0.05 grados | GES DISC | HDF-EOS2 | [3] |

### Leyenda y notas

- **[1]** GPM_3IMERGM: Precipitación observada por el satélite GPM. La cobertura real fue verificada contra el metadato CMR `coverage_start`/`coverage_end`. El tamaño estimado de archivo es de ~30 MB por granula (global).
- **[2]** M2TMNXFLX y M2TMNXSLV: Ambos forman parte del conjunto MERRA-2 (Modern-Era Retrospective analysis for Research and Applications, versión 5.12.4). El centro de distribución es GES DISC (NASA). La resolución de 0.625° x 0.5° es la resolución nativa de la malla. Los datos OPeNDAP usan un margen de 0.5° alrededor del bbox de la región. *Cobertura y resolución verificadas en la configuración del proyecto; la cita estándar es la del conjunto MERRA-2.*
- **[3]** MOD13C2: NDVI mensual del satélite Terra/MODIS. La resolución de 0.05 x 0.05 grados es la resolución nativa de los productos CMG (Comprehensive Modification). La cobertura se extiende desde febrero de 2000 (lanzamiento de Terra) hasta la fecha más reciente disponible en CMR. *Algunos campos marcados como pendientes hasta que se pueda cruzar con el catálogo CMR oficial.*

### Referencias

> [1] NASA GPM IMERG. GPM_3IMERGM. Versión 07. Goddard Space Flight Center. <https://cmr.earthdata.nasa.gov/search/granules?short_name=GPM_3IMERGM>
>
> [2] NASA MERRA-2. M2TMNXFLX y M2TMNXSLV. Versión 5.12.4. Goddard Space Flight Center. <https://cmr.earthdata.nasa.gov/search/granules?short_name=M2TMNXFLX>
>
> [3] NASA MODIS. MOD13C2. Versión 061. Goddard Space Flight Center. <https://cmr.earthdata.nasa.gov/search/granules?short_name=MOD13C2>

### Pendientes de verificación CMR

Lo siguiente no fue verificado directamente contra el catálogo CMR y está marcado para revisión:

- Fechas exactas de actualización mensual en CMR para cada producto.
- Descripción completa de las variables auxiliares en CMR.
- Formato de metadatos DMRPP vs CF-conformante.
- Atributos de escala y desplazamiento (`scale_factor`, `add_offset`) en los archivos nativos.