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

El acceso a los datos de NASA requiere autenticación en **Earthdata**. El proyecto usa el archivo `.env` local para cargar las credenciales sin que se commiteen en el repositorio.

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

   **Importante:** No escribas el token en ningún archivo del repositorio (ni en `.env`, ni en `config/`, ni en ningún otro archivo versionado). El valor debe proporcionarse únicamente a través del entorno del sistema.

3. **Alternativa: archivo `.env` local** (solo para desarrollo):
   - Copia el modelo: `cp .env.example .env` (o crea el archivo manualmente).
   - Añade tus credenciales:
     ```
     EARTHDATA_TOKEN=tu-token-aquí
     ```
   - El script `download_data.py` carga este archivo al iniciar con `cargar_entorno()`, que lee el `.env` y establece las variables de entorno sin imprimirlas ni persistirlas fuera del proceso.

   **No compartas el archivo `.env`** ni lo incluyas en el control de versiones.

## Uso

### Comandos disponibles (definidos en `download_data.py`)

```bash
# Ver ayuda general
uv run python scripts/download_data.py --help
```

| Opción | Descripción | Valor por defecto |
|--------|-------------|-------------------|
| `--product` | Clave del producto a procesar (o `all`). Requerido. | — |
| `--region` | Región a analizar. El catálogo define `honduras`. | `honduras` |
| `--start` | Fecha de inicio (formato ISO: `YYYY-MM-DD`). | `1996-01-01` (del config) |
| `--end` | Fecha de fin (formato ISO: `YYYY-MM-DD`). | `2026-11-01` (del config) |
| `--output-dir` | Directorio donde se guardarán los resultados. | `data/raw` |
| `--format` | Formato de salida: `nc` (NetCDF), `geotiff` o `both`. | `nc` |
| `--full-download | Descargar el archivo global completo en lugar de usar OPeNDAP con recorte. | `False` |
| `--dry-run | Ejecutar una simulación sin descargar ni guardar archivos. | `False` |

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
- Genera un GeoTIFF de respaldo (ya que `format` es `nc`, el GeoTIFF no se genera a menos que se especifique `both`).

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

## Flujo de trabajo típico

1. **Explorar en Giovanni** (https://giovanni.gsfc.nasa.gov) para decidir la variable y el período.
2. **Ejecutar un dry-run** para validar que los parámetros de búsqueda (fecha, región) devuelven resultados.
3. **Ejecutar la descarga definitiva** con el formato deseado (`nc` o `both`).
4. **Ver los resultados** en `data/raw/` (NetCDF) y `data/raw/geotiff/` (GeoTIFF).
5. **Continuar al análisis** con los scripts de procesamiento o el frontend web.