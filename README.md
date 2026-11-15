# 🌍 OpusTerra by Pegaso-X

**Aplicación web para explorar tendencias ambientales en Honduras mediante un globo terráqueo 3D y comparaciones entre zonas.**

NASA Space Apps 2026 · Honduras

---

## Objetivo

OpusTerra presenta cambios ambientales de largo plazo de una forma visual y comprensible. La aplicación ayuda a responder:

- qué variable se está observando;
- en qué zonas aparece un cambio;
- cuál es la dirección y el tamaño aproximado de ese cambio;
- qué zonas muestran comportamientos opuestos.

El proyecto no sustituye una medición directa. Presenta resultados de análisis elaborados a partir de productos ambientales de NASA y NOAA.

---

## Funcionalidades actuales

- **Globo 3D interactivo.** Muestra las zonas con cambios claros sobre la superficie de la Tierra.
- **Selector de variables.** Permite consultar temperatura, precipitación de MERRA-2, precipitación GPM IMERG y vegetación mediante NDVI.
- **Marcadores de tendencia.** Diferencia visualmente los cambios al alza y a la baja.
- **Comparaciones automáticas.** Presenta pares de zonas con tendencias opuestas para facilitar la exploración.
- **Tarjetas comparativas.** Muestran el nombre de cada zona, su dirección de cambio, el cambio acumulado estimado y sus coordenadas técnicas.
- **Línea de tiempo.** Permite consultar los años disponibles cuando la variable incluye una serie anual por zona.
- **Panel de resultados.** Resume el periodo, la fuente, la unidad y la cantidad de zonas analizadas.
- **Páginas informativas.** Incluye un glosario, fuentes de datos y la información del proyecto y sus participantes.
- **Diseño adaptable.** La interfaz funciona en pantallas de escritorio y dispositivos móviles.

La aplicación no ofrece diagnósticos, alertas ni recomendaciones de salud.

---

## Datos utilizados

Los datos públicos de la aplicación corresponden a Honduras y se procesan con una ventana común de análisis cuando la variable lo permite.

| Variable | Producto | Versión | Resolución | Cobertura de referencia |
|----------|----------|---------|------------|-------------------------|
| Precipitación observada | GPM IMERG | 07 | 0.1° × 0.1° | 1998-01 → 2025-09 |
| Precipitación modelada | MERRA-2 flux (M2TMNXFLX) | 5.12.4 | 0.625° lon × 0.5° lat | 1996-01 → 2026-09 |
| Temperatura del aire a 2 m | MERRA-2 superficie (M2TMNXSLV) | 5.12.4 | 0.625° lon × 0.5° lat | 1996-01 → 2026-09 |
| Vegetación (NDVI) | MODIS MOD13C2 | 061 | 0.05° × 0.05° | 2000-02 → 2026-10 |

La ventana común utilizada por los análisis actuales es `2000-02`–`2025-09`. Los archivos de resultados se encuentran en `frontend/public/data/honduras/`.

- **Distribución:** NASA GES DISC, Earthdata Search y OPeNDAP.
- **Procesamiento:** los recortes de MERRA-2 se solicitan para la región de interés, no como archivos globales completos.
- **Formatos de trabajo:** NetCDF4 y GeoTIFF cuando se necesita una capa raster.

Las fuentes y sus identificadores están documentados en [`docs/data-sources.md`](docs/data-sources.md). El contrato de los JSON está descrito en [`docs/json-contract.md`](docs/json-contract.md). Los errores conocidos de la aplicación y los límites de los datos y del método están en [`docs/known-bugs.md`](docs/known-bugs.md).

---

## Tecnología

| Capa | Tecnología |
|------|-----------|
| Interfaz | Svelte 5, TypeScript y Vite |
| Globo 3D | three.js |
| Procesamiento | Python, xarray y rioxarray |
| Acceso a datos | earthaccess y pydap (OPeNDAP) |
| Formatos | NetCDF4 y GeoTIFF |

---

## Empezar

### Interfaz

```bash
cd frontend
pnpm install
pnpm run dev
```

La aplicación estará disponible en `http://localhost:5173`.

Comandos útiles:

```bash
pnpm run check    # Comprueba Svelte y TypeScript
pnpm run build    # Genera la versión de producción
pnpm run preview  # Sirve localmente la versión de producción
```

### Backend

```bash
cd backend
uv sync
```

La guía específica está en [`frontend/README.md`](frontend/README.md) y [`backend/README.md`](backend/README.md).

---

## Licencia

MIT License. Consulta el archivo [`LICENSE`](LICENSE).

---

Made with ❤️ by Pegaso-X from 🇭🇳
