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

## Qué hace la app hoy

- **Globo 3D interactivo.** Muestra sobre la superficie de la Tierra las zonas donde el cambio es claro.
- **Menú flotante de variables.** Permite elegir entre temperatura del aire, precipitación MERRA-2, precipitación IMERG y vegetación (NDVI) sin abrir el panel de resultados.
- **Selección de países en el globo.** Al pulsar el territorio de un país, el globo lo resalta, muestra su nombre y su disponibilidad de datos, y cambia de región cuando el punto pulsado cae dentro de su recuadro de datos.
- **Controles plegables.** La leyenda y la línea de tiempo se guardan detrás de un botón para dejar el globo despejado.
- **Capa de marcadores que se puede mostrar u ocultar.** El botón «Ocultar» / «Mostrar» quita y devuelve los puntos del globo sin recargar los datos.
- **Solo se dibujan las tendencias al alza.** El globo y la lista «Celdas significativas» dejan fuera las zonas que van a la baja, aunque el archivo de datos las contenga (ver [`docs/known-bugs.md`](docs/known-bugs.md)).
- **Lista de pares cuando existen.** Cuando hay zonas con cambio claro en las dos direcciones, el panel lista pares de zonas con tendencias opuestas y permite abrir cada par. Hoy solo la vegetación forma pares.
- **Tarjetas de región con marca de significancia.** Cada zona del par muestra su nombre, la marca «Alza» o «Bajada», el cambio acumulado en el periodo y sus coordenadas bajo «Ver detalles técnicos».
- **Línea de tiempo.** Aparece desactivada con el aviso «Esta variable no incluye una serie anual por zona» en las variables que no traen serie anual por zona. Hoy solo temperatura y vegetación la activan, y entonces cambia el año de la capa.
- **Panel de resultados.** Reúne la frase resumen, la fuente, la unidad, el periodo y la cantidad de zonas analizadas. En el celular se pliega y se abre con «Abrir panel» / «Cerrar panel».
- **Páginas informativas.** Incluye metodología, fuentes de datos, glosario y la información del proyecto y sus integrantes.
- **Diseño adaptable.** La interfaz funciona en pantallas de escritorio y en dispositivos móviles.

La aplicación no ofrece diagnósticos, alertas ni recomendaciones de salud.

---

## Cómo leer un resultado

1. **Elige la variable y la región.** La variable se cambia en el menú flotante de arriba a la izquierda; la región, en el selector del mismo menú o pulsando un país del globo. En el celular, los controles quedan arriba y el panel de resultados se abre con «Ver análisis».
2. **Empieza por la frase resumen.** Dice cuántas zonas de la región muestran un cambio claro sobre cuántas se analizaron. En las precipitaciones avisa de que el producto es un promedio de área y no hay zonas que dibujar.
3. **Cada punto del globo es una zona.** El color va de cambio leve a cambio fuerte, como indica la leyenda del globo. Hoy solo se dibujan las zonas que van al alza; las que van a la baja no aparecen.
4. **«Alza» y «Bajada» indican la dirección del cambio.** La marca que las acompaña señala que el cambio es lo bastante consistente como para que no parezca casualidad; es la marca de significancia.
5. **La cifra grande de una tarjeta es el cambio acumulado en el periodo**, por ejemplo una cifra como «+0.7 °C en 24 años». No es el valor del último año ni una predicción: resume cuánto cambió la medida a lo largo de los años completos analizados.
6. **La lista de pares solo aparece cuando hay zonas claras en las dos direcciones.** Cada par enfrenta una zona que sube con otra que baja para compararlas. Si no hay pares, el panel muestra «Sin pares de tendencias opuestas claras». Hoy solo la vegetación forma pares.
7. **La línea de tiempo solo se activa cuando hay serie anual por zona.** Hoy la activan temperatura y vegetación; con ellas cambia el año de la capa. En las precipitaciones aparece desactivada con el aviso «Esta variable no incluye una serie anual por zona».
8. **Los detalles técnicos están plegados.** «Ver detalles técnicos» muestra coordenadas y códigos para quien los necesite; no hacen falta para leer el resultado.

---

## Glosario breve

- **Tendencia.** Dirección general en la que cambia una medida a lo largo de varios años.
- **Cambio claro.** Cambio suficientemente consistente como para que sea poco probable que se deba al azar; la app lo marca con «Alza» o «Bajada».
- **Alza / Bajada.** La medida sube o baja con el paso de los años. Hoy el globo solo dibuja las que van al alza.
- **Serie anual.** Un valor por cada año completo, usado para comparar cómo cambia una zona.
- **Años completos.** Años con los 12 meses dentro de la ventana mensual. La ventana actual, 2000-02 → 2025-09, deja 2001–2024 como años completos.
- **Ventana mensual.** Periodo de meses que se usa antes de descartar los años incompletos.
- **Zona o celda.** Una parte del territorio dentro de una cuadrícula; cada una se analiza como unidad.
- **Promedio de área.** Un solo valor para toda la región en lugar de una cuadrícula; por eso las precipitaciones no tienen puntos ni pares.
- **NDVI.** Medida de la vegetación a partir de la luz que reflejan las plantas.
- **MERRA-2, GPM IMERG y MODIS.** Productos de la NASA: un modelo atmosférico, una estimación de lluvia por satélite y un instrumento que observa la superficie.

---

## Datos utilizados

Los datos públicos de la aplicación corresponden a Honduras y a Centroamérica. Los números que muestra la app no se calculan en el navegador: [`backend/scripts/download_data.py`](backend/scripts/download_data.py) descarga los productos de NASA y [`backend/scripts/generate_analysis.py`](backend/scripts/generate_analysis.py) escribe los archivos `frontend/public/data/*.json`. La app solo lee esos archivos.

| Variable | Producto | Versión | Resolución | Ventana mensual usada | Años completos usados |
|----------|----------|---------|------------|-----------------------|-----------------------|
| Precipitación observada | GPM IMERG | 07 | 0.1° × 0.1° | 2000-02 → 2025-09 | — (promedio de área) |
| Precipitación modelada | MERRA-2 flux (M2TMNXFLX) | 5.12.4 | 0.625° lon × 0.5° lat | 2000-02 → 2025-09 | — (promedio de área) |
| Temperatura del aire a 2 m | MERRA-2 superficie (M2TMNXSLV) | 5.12.4 | 0.625° lon × 0.5° lat | 2000-02 → 2025-09 | 2001–2024 |
| Vegetación (NDVI) | MODIS MOD13C2 | 061 | 0.05° × 0.05° | 2000-02 → 2025-09 | 2001–2024 |

La ventana mensual es común a los cuatro productos y va de 2000-02 a 2025-09, según `PERIODO_COMUN` en [`backend/src/opusterra/config.py`](backend/src/opusterra/config.py). Como 2000 y 2025 no llegan a 12 meses, la serie anual efectiva usa 2001–2024. Las dos precipitaciones son promedios de área: no tienen malla de celdas ni serie anual por zona.

La cobertura disponible de cada producto está en [`backend/config/datasets.toml`](backend/config/datasets.toml): GPM IMERG 1998-01-01 → 2025-09-30; MERRA-2 1996-01-01 → 2026-09-30; MODIS MOD13C2 2000-02-01 → 2026-10-31.

Los archivos de resultados se encuentran en [`frontend/public/data/honduras/`](frontend/public/data/honduras/) y [`frontend/public/data/centroamerica/`](frontend/public/data/centroamerica/).

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

Nota técnica: el análisis usa la prueba de Mann-Kendall y la pendiente de Theil-Sen por celda, con corrección de Benjamini-Hochberg; el detalle está en [`docs/json-contract.md`](docs/json-contract.md).
