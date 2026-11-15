# Backend - Análisis de tendencias contrastantes

## Requisitos previos

- **Python >= 3.12** (el proyecto usa typing y características de Python 3.12).
- **`uv`** como gestor de paquetes y entorno virtual (recomendado). `uv` maneja la creación de entornos, la instalación de dependencias y la fijación de versiones.
- Las dependencias del proyecto están definidas en `backend/pyproject.toml` e incluyen:
  - `earthaccess` (autenticación y descarga de datos NASA)
  - `netcdf4` y `h5netcdf` (lectura/escritura de NetCDF)
  - `xarray` (manejo de mallas etiquetadas)
  - `numpy` y `pandas` (procesamiento de datos)
  - `pydap` (acceso OPeNDAP)
  - `pyhdf` (lectura de archivos HDF-EOS2, para MODIS)
  - `rioxarray` (generación de GeoTIFF y operaciones SIG)
  - `scipy` (estadística y señales)

## Instalación

```bash
# 1. Clona el repositorio y entra en el directorio backend
cd backend

# 2. Sincroniza el entorno e instala las dependencias
uv sync
```

El comando `uv sync` leerá `pyproject.toml`, creará un entorno virtual aislado e instalará todas las dependencias listadas (incluyendo las de dev opcionales). No es necesario usar `pip` directamente.

## Configuración de credenciales NASA Earthdata

El acceso a los datos de NASA requiere autenticación en **Earthdata**. Las credenciales se leen del entorno del proceso; en desarrollo también de un archivo `.env` en la raíz del repositorio, que no se commitea.

### Flujo de trabajo

1. **Obtén tu token de Earthdata:**
   - Ve a https://urs.earthdata.nasa.gov/ y crea una cuenta gratuita (o usa una existente).
   - Genera un token de acceso en la configuración de la cuenta, o usa tu nombre de usuario y contraseña.

2. **Configura la variable de entorno** (recomendado, no requiere tocar archivos del repositorio):

   ```bash
   export EARTHDATA_TOKEN="tu-token-aquí"
   ```

   O, en Windows PowerShell:

   ```powershell
   $env:EARTHDATA_TOKEN="tu-token-aquí"
   ```

   **Importante:** No commitees el token ni lo escribas en archivos versionados. El valor se proporciona por el entorno del proceso o, en desarrollo, por el `.env` local descrito abajo.

3. **Alternativa: archivo `.env` en la raíz del repositorio** (solo para desarrollo):
   - Crea el archivo `.env` en la raíz del repositorio, al mismo nivel que `backend/`, `frontend/` y `docs/`. No va dentro de `backend/`.
   - Añade tus credenciales:
     ```
     EARTHDATA_TOKEN=tu-token-aquí
     ```
   - `download_data.py` llama a `cargar_entorno()` al iniciar, y esa función lee exactamente `<raíz del repositorio>/.env`: define las variables en el proceso sin imprimirlas ni persistirlas en otro sitio. Si el archivo no existe, el script sigue y usa las variables del entorno.

   El `.env` está en `.gitignore`. **No lo compartas** ni lo incluyas en el control de versiones.

Si la descarga responde `ERROR: {"errors":["Token does not exist"]}`, el token no es válido: genera otro en https://urs.earthdata.nasa.gov/, vuelve a exportarlo (o actualiza el `.env`) y ejecuta el comando de nuevo.

## Uso

Todos los comandos se ejecutan desde `backend/`, pero los scripts resuelven sus rutas desde la raíz del repositorio: `backend/config/datasets.toml`, `data/raw/`, `frontend/public/data/` y el `.env`.

### Comandos disponibles (definidos en `download_data.py`)

```bash
# Ver ayuda general
uv run python scripts/download_data.py --help
```

| Opción | Descripción | Valor por defecto |
|--------|-------------|-------------------|
| `--product` | Clave del producto a procesar (`gpm_imerg`, `merra2_flx`, `merra2_slv`, `merra2_aer`, `mod13c2`) o `all`. Requerido. | — |
| `--region` | Región a analizar; debe existir en `backend/config/datasets.toml` (hoy `honduras` y `centroamerica`). | `honduras` |
| `--start` | Fecha de inicio (formato ISO: `YYYY-MM-DD`). | `1996-01-01` (de `[defaults]` en `datasets.toml`) |
| `--end` | Fecha de fin (formato ISO: `YYYY-MM-DD`). | `2026-11-01` (de `[defaults]` en `datasets.toml`) |
| `--output-dir` | Directorio donde se guardarán los resultados. | `data/raw` |
| `--format` | Formato de salida: `nc` (NetCDF), `geotiff` o `both`. | `nc` |
| `--full-download` | Descargar el archivo global completo en lugar de usar OPeNDAP con recorte. Solo afecta a los productos MERRA-2. | `False` |
| `--dry-run` | Ejecutar una simulación sin descargar ni guardar archivos. | `False` |

### Ejemplos prácticos

#### 1. Dry-run (ver qué se encontraría sin descargar)

```bash
uv run python scripts/download_data.py --product gpm_imerg --region honduras --start 2020-01-01 --end 2020-12-31 --dry-run
```

Resultado esperado (resumen):
```
Dry-run: no se descargarán archivos.
...
Resumen GPM_3IMERGM: archivos recortados=0, omitidos=0, fallidos=0, GeoTIFF=0
Tamaño OPeNDAP estimado: 0 KB
Rango efectivo: 2020-01-01 a 2020-12-31
Meses faltantes: ninguno
```

Esto busca las granulas que coincidirían con el rango y el bbox, pero se detiene antes de descargar nada. Útil para validar que los parámetros de búsqueda son correctos antes de consumir ancho de banda.

#### 2. Descarga con formato NetCDF (modo OPeNDAP, recorte regional)

```bash
uv run python scripts/download_data.py --product merra2_slv --region honduras --start 2000-02-01 --end 2025-09-30 --format nc
```

 Flujo:
- Busca granulas MERRA-2 en CMR para el período y bbox de Honduras.
- Usa OPeNDAP para descargar solo las variables `T2M` y celdas dentro del bbox (más un margen de 0.5°).
- Guarda un archivo NetCDF con la variable `T2M` recortado.

Con `--format nc` solo se escribe el NetCDF. Los GeoTIFF aparecen únicamente con `--format geotiff` o `--format both`.

#### 3. Descarga con formato ambos (NetCDF + GeoTIFF)

```bash
uv run python scripts/download_data.py --product all --region honduras --start 2000-02-01 --end 2025-09-30 --format both
```

- Descarga (u OPeNDAP recorta) las tres variables principales (precipitación, T2M, NDVI).
- Para cada una, genera ambos archivos: `.nc` (NetCDF) y `.tif` (GeoTIFF).
- Al final, imprime un resumen por producto con el conteo de archivos descargados, convertidos, omitidos, fallidos y GeoTIFF generados.

#### 4. Descarga global completa (ignorar OPeNDAP, descargar todos los archivos)

```bash
uv run python scripts/download_data.py --product all --region honduras --full-download
```

- Descarga las granulas completas desde CMR sin usar OPeNDAP.
- Útil para validar el pipeline con datos sin recortar o cuando el servicio OPeNDAP no está disponible.
- **Advertencia:** Generará muchos GB de datos (cada granula MERRA-2 es ~380-400 MB, y pueden ser cientos de granulas para un período largo).

## Cadena de análisis: de la descarga a los JSON

El backend son dos pasos, siempre en este orden:

1. **Descarga.** `backend/scripts/download_data.py` busca los productos en CMR y escribe los NetCDF recortados en `data/raw/<carpeta del producto>/` (por ejemplo `data/raw/merra2_slv/`). Con `--format geotiff` o `both` añade los `.tif` en `data/raw/<carpeta del producto>/geotiff/`.
2. **Generación de los JSON.** `backend/scripts/generate_analysis.py` lee los NetCDF de `data/raw/<región>/<carpeta del producto>/` (por ejemplo `data/raw/honduras/merra2_slv/`) para MERRA-2 y MOD13C2, y de `data/raw/gpm_imerg/` para GPM IMERG; escribe en `frontend/public/data/<región>/` los JSON que consume la app; por ejemplo `frontend/public/data/honduras/`. Contrato de esos archivos: [`docs/json-contract.md`](../docs/json-contract.md).

La descarga tiene que dejar los archivos en esas carpetas. El `--output-dir` por defecto es `<raíz del repositorio>/data/raw`, pero una ruta pasada a mano se resuelve desde el directorio donde se ejecuta el comando: desde `backend/`, la carpeta de la región se escribe `../data/raw/<región>`.

```bash
cd backend

# MERRA-2 y MOD13C2: generate_analysis.py los lee de data/raw/honduras/
uv run python scripts/download_data.py --product merra2_slv --region honduras --start 2000-02-01 --end 2025-09-30 --output-dir ../data/raw/honduras
uv run python scripts/download_data.py --product merra2_flx --region honduras --start 2000-02-01 --end 2025-09-30 --output-dir ../data/raw/honduras
uv run python scripts/download_data.py --product merra2_aer --region honduras --start 2000-02-01 --end 2025-09-30 --output-dir ../data/raw/honduras
uv run python scripts/download_data.py --product mod13c2 --region honduras --start 2000-02-01 --end 2025-09-30 --output-dir ../data/raw/honduras

# GPM IMERG: generate_analysis.py lo lee de data/raw/gpm_imerg/ (el --output-dir por defecto)
uv run python scripts/download_data.py --product gpm_imerg --region honduras --start 2000-02-01 --end 2025-09-30

# JSON del frontend
uv run python scripts/generate_analysis.py --region honduras
```

La generación exige los meses completos de la ventana configurada: `PERIODO_COMUN` en `backend/src/opusterra/config.py` fija 2000-02 → 2025-09, 308 meses. Si falta un mes, el script se detiene con un error que indica cuántos o cuáles meses faltan (por ejemplo `Faltan meses MERRA-2 T2M en la ventana efectiva: ...`); hay que descargar esos meses y volver a ejecutarlo. Además de los NetCDF, la generación necesita la serie ONI en `data/external/nino-3.4/iersst_nino3.4a_1996_2026.nc`; ninguno de los dos pasos la crea y, si falta, el script se detiene con `FileNotFoundError: No existe el archivo ONI`.

## Flujo de trabajo típico

1. **Explorar en Giovanni** (https://giovanni.gsfc.nasa.gov) para decidir la variable y el período.
2. **Ejecutar un dry-run** para validar que los parámetros de búsqueda (fecha, región) devuelven resultados.
3. **Ejecutar la descarga definitiva** con el formato deseado (`nc` o `both`) y el `--output-dir` que espera la generación (ver la cadena de análisis).
4. **Ver los resultados** en `data/raw/<carpeta del producto>/` o, si descargaste a la carpeta de la región, `data/raw/<región>/<carpeta del producto>/` (NetCDF) y su subcarpeta `geotiff/` (GeoTIFF).
5. **Generar los JSON** con `backend/scripts/generate_analysis.py` (ver la cadena de análisis arriba) y **verlos** en el frontend web.

## Módulos de `backend/src/opusterra/`

| Módulo | Qué hace |
|--------|----------|
| `config.py` | Región y periodos: bbox de Honduras, ventanas de cada producto (`PERIODO_MERRA2`, `PERIODO_GPM`, `PERIODO_NDVI`, `PERIODO_COMUN`) y conversiones de unidades. |
| `enso.py` | Índice Niño 3.4: carga la serie ONI mensual y elimina su componente lineal de las series climáticas. |
| `merra2.py` | Carga y preparación de MERRA-2 (FLX y SLV) a partir de los `.nc` ya descargados. |
| `mod13c2.py` | NDVI mensual de MOD13C2 y máscara de calidad: descarta las celdas cuyos campos de calidad del producto no son fiables. |
| `tendencia.py` | Prueba de tendencia (Mann-Kendall y pendiente de Theil-Sen) y corrección por comparaciones múltiples (Benjamini-Hochberg). |

## Pruebas

```bash
cd backend
uv run pytest
```

`pytest` está en el grupo `dev` de `backend/pyproject.toml`, así que lo instala `uv sync`. La configuración de pytest en ese mismo archivo fija `testpaths = ["tests"]`: `uv run pytest` ejecuta `backend/tests/`.

## Referencias

- [`docs/data-sources.md`](../docs/data-sources.md): productos de NASA/NOAA, identificadores CMR y distribución.
- [`docs/json-contract.md`](../docs/json-contract.md): contrato de los JSON que consume el frontend.
- [`docs/known-bugs.md`](../docs/known-bugs.md): errores conocidos y límites de los datos.
