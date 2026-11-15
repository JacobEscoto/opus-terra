# Fuentes de datos

Productos principales que usa el análisis. Los valores de nombre corto, versión, cobertura, resolución y
formato nativo son los de [`backend/config/datasets.toml`](../backend/config/datasets.toml), que
es la fuente de verdad para cobertura y resolución: el catálogo está verificado contra CMR y con
una granula real. El centro de distribución es el `archive_center` que CMR publica para cada
nombre corto. Lo que todavía no está verificado se enumera en
[Pendientes de verificación](#pendientes-de-verificación).

| Producto | Nombre corto CMR | Versión | Cobertura real | Resolución | Centro de distribución | Formato nativo | Cita requerida |
|----------|-----------------|---------|---------------|------------|------------------------|----------------|----------------|
| GPM IMERG v07 | GPM_3IMERGM | 07 | 1998-01-01 a 2025-09-30 | 0.1 x 0.1 grados | GES DISC | HDF5 | [1] |
| MERRA-2 flux (PRECTOTCORR) | M2TMNXFLX | 5.12.4 | 1996-01-01 a 2026-09-30 | 0.625 grados lon x 0.5 grados lat | GES DISC | NetCDF4 | [2] |
| MERRA-2 superficie (T2M) | M2TMNXSLV | 5.12.4 | 1996-01-01 a 2026-09-30 | 0.625 grados lon x 0.5 grados lat | GES DISC | NetCDF4 | [2] |
| MODIS MOD13C2 v061 | MOD13C2 | 061 | 2000-02-01 a 2026-10-31 | 0.05 x 0.05 grados | LP DAAC | HDF-EOS2 | [3] |
| Índice Niño 3.4 (ONI) | — (no es producto CMR) | — | 1996 a 2026 (serie mensual) | Mensual, un valor por mes (sin malla) | NOAA/KNMI (no NASA) | NetCDF | — |

El índice Niño 3.4 no es un producto de NASA y no se descarga por CMR: entra al análisis como
covariable para descontar el efecto de El Niño y La Niña.

### Leyenda y notas

- **[1]** GPM_3IMERGM: Precipitación observada por el satélite GPM. La cobertura real va de
  1998-01-01 a 2025-09-30 según `datasets.toml`. El tamaño estimado de archivo es de ~30 MB por
  granula (global).
- **[2]** M2TMNXFLX y M2TMNXSLV: Ambos forman parte del conjunto MERRA-2 (Modern-Era Retrospective
  analysis for Research and Applications, versión 5.12.4). El centro de distribución es GES DISC
  (NASA). La resolución de 0.625° x 0.5° es la resolución nativa de la malla. Los datos OPeNDAP
  usan un margen de 0.5° alrededor del bbox de la región. *La cita estándar es la del conjunto
  MERRA-2.*
- **[3]** MOD13C2: NDVI mensual del satélite Terra/MODIS. La resolución de 0.05 x 0.05 grados es
  la resolución nativa de los productos CMG (Comprehensive Modification). La cobertura va de
  2000-02-01 a 2026-10-31 según `datasets.toml`, y el centro de distribución es LP DAAC según
  CMR. El formato nativo es HDF-EOS2; la descarga lo convierte a NetCDF4.
- **Índice Niño 3.4 (ONI):** no es un producto de NASA ni tiene identificador de CMR; la fuente
  es NOAA/KNMI (`FUENTE_NINO_34` en [`backend/src/opusterra/config.py`](../backend/src/opusterra/config.py)).
  La serie mensual vive en `data/external/nino-3.4/iersst_nino3.4a_1996_2026.nc`, con la variable
  `Nino3.4`. El análisis la usa en [`backend/src/opusterra/enso.py`](../backend/src/opusterra/enso.py)
  para quitar por regresión lineal la parte del cambio mensual que explica ese ciclo; las
  tendencias publicadas son el residuo, es decir «cuánto cambia lo que no se explica por El Niño o
  La Niña». Si el archivo falta, `generate_analysis.py` se detiene con
  `FileNotFoundError: No existe el archivo ONI: ...`.

### Insumos en disco: series de precipitación de área

`merra2_precipitacion.json` e `imerg_precipitacion.json` no salen de una malla: son series de
**promedio de área** (`areaAvgTimeSeries`), un solo valor por mes para la región. No tienen
dimensiones de latitud ni de longitud, así que los JSON no llevan celdas: `resultados_pixeles`
vacío, `pixeles_probados` en 0, `pares` vacío y `fdr.estado = "no_aplicable_sin_malla"`. El
contrato completo de esos archivos está en [`docs/json-contract.md`](json-contract.md).

`backend/scripts/generate_analysis.py` los toma del disco con estos patrones:

| JSON | Carpeta | Patrón de archivo |
|------|---------|------------------|
| `imerg_precipitacion.json` | `data/raw/gpm_imerg/` | `3B-MO*.nc` |
| `merra2_precipitacion.json` | `data/raw/<región>/merra2_flx/` | `*tavgM_2d_flx*.nc` |

La serie tiene que cubrir los 308 meses de la ventana común (2000-02 a 2025-09); si no, la
generación se detiene con
`RuntimeError: Precipitación en ...: se encontraron N meses dentro de 2000-02 a 2025-09; se requieren 308.`
Además, si el archivo de IMERG es el mapa global (3600 x 1800 celdas), la generación se detiene con
`ValueError: IMERG en ... es un mapa global (lon=3600, lat=1800); se detiene para no promediar el mundo como si fuera la región.`

### Referencias

> [1] NASA GPM IMERG. GPM_3IMERGM. Versión 07. Goddard Space Flight Center. <https://cmr.earthdata.nasa.gov/search/granules?short_name=GPM_3IMERGM>
>
> [2] NASA MERRA-2. M2TMNXFLX y M2TMNXSLV. Versión 5.12.4. Goddard Space Flight Center. <https://cmr.earthdata.nasa.gov/search/granules?short_name=M2TMNXFLX>
>
> [3] NASA MODIS. MOD13C2. Versión 061. Goddard Space Flight Center. <https://cmr.earthdata.nasa.gov/search/granules?short_name=MOD13C2>

### Pendientes de verificación

El resto de los campos de la tabla ya están en `backend/config/datasets.toml` o comprobados
contra CMR. Lo siguiente sigue sin verificar:

- **Fechas exactas de publicación mensual en CMR.** La configuración fija `coverage_start` y
  `coverage_end` de cada producto, pero no el día del mes en que CMR publica la granula nueva.
  Falta comprobarlo granula a granula.
- **Descripción científica de las variables auxiliares.** `datasets.toml` fija qué variables
  auxiliares se descargan por producto, pero no qué mide cada una. Falta contrastarlas con la
  documentación de cada producto.
