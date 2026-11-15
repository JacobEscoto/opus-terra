# OpusTerra - Frontend

Aplicación web interactiva para visualizar tendencias climáticas contrastantes en regiones de Honduras. El proyecto forma parte del NASA Space Apps 2026 y muestra en un globo 3D cómo cambian variables como precipitación, temperatura y vegetación (NDVI) a lo largo del tiempo, junto con pares de regiones con tendencias opuestas.

## Qué es la app

Esta es una aplicación de página única (SPA) construida con **Svelte 5**, **TypeScript** y **Vite**. El centro de la interfaz es un **globo terráqueo 3D** (usando la librería `three.js`) que muestra el estado actual de las variables climáticas. La aplicación permite:

- Cargar un análisis de tendencias desde un archivo JSON.
- Navegar por una **línea de tiempo** para ver cómo evolucionan los datos año a año.
- Seleccionar **pares de regiones** con cambios opuestos (ej. una región donde la precipitación sube y otra donde baja).
- Ver un **panel de comparación** lado a lado que explica, en palabras sencillas, por qué dos regiones distintas comportan de forma diferente.
- Filtrar por período y ver la confiabilidad de los datos (se marca como "no confiable" si la señal no es estadísticamente significativa).

La app no requiere instalación: se abre directamente en el navegador (`pnpm run dev` durante el desarrollo, o `pnpm run build` para un build de producción).

## Cómo ejecutarla

```bash
# 1. Entra en el directorio frontend
cd frontend

# 2. Instala las dependencias (solo la primera vez)
pnpm install

# 3. Inicia el servidor de desarrollo
pnpm run dev
```

El servidor estará disponible en http://localhost:5173 (la puerto estándar de Vite). La aplicación se recarga automáticamente cuando cambian los archivos (`HMR`).

### Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `pnpm run dev` | Inicia el servidor de desarrollo con HMR (Hot Module Replacement). |
| `pnpm run build` | Genera una versión de producción estática en `dist/`. |
| `pnpm run preview` | Previsualiza el build de producción localmente. |
| `pnpm run check` | Ejecuta TypeScript y Svelte type-checking para validar el código. |

## Datos de prueba: `mock.json`

La aplicación está diseñada para cargar datos de análisis desde un archivo JSON. Por defecto, cuando la app se inicia y no hay datos reales disponibles, lee el archivo `mock.json` que contiene datos de ejemplo estructurados como si provinieran del análisis posterior.

El archivo de datos de prueba se encuentra en:

```
frontend/src/lib/data/mock.json
```

Estructura del `mock.json`:

- **`fuente`**: Identificador de dónde provienen los datos (`"mock"` en este caso).
- **`variable`**: Nombre de la variable simulada (ej. `"clorofila_a"`).
- **`nombre_variable`**: Nombre legible mostrado en la UI.
- **`unidad`**: Unidad de medida (ej. `"mg/m³"`).
- **`periodo`**: Intervalo de años cubierto por los datos `{ inicio, fin }`.
- **`contexto_oms`**: Texto de contexto sobre salud, según guías de la Organización Mundial de la Salud. Esto se muestra en el panel lateral cuando se selecciona un par.
- **`pares`**: Array de pares de regiones con tendencias contrastantes. Cada par tiene:
  - `id`: identificador único para seleccionar el par.
  - `region_a` y `region_b`: objetos con `nombre`, `lat`, `lon`, `tendencia` ( `"alza"` o `"bajada"`), `cambio_porcentual`, `significativa` (booleano) y `explicacion` (texto corto).
  - Los datos de ejemplo incluyen pares ficticios como "Benguela-Guinea" y "Báltico-Adriático", con tendencias opuestas y grados de significancia variables.

### Cómo la app usa los datos

1. Al montar la aplicación, el componente `App.svelte` llama a `cargarAnalisis()` que lee el archivo `mock.json` (mediante la función `cargarAnalisis` en `lib/data/loadAnalysis.ts`).
2. Los datos cargados actualizan el estado global: el estado de carga, los pares de regiones y el período de tiempo.
3. En la vista móvil (columnas únicas), el planeta se centra y el panel muestra el análisis del par seleccionado.
4. En la vista de escritorio, el planeta se desplaza levemente a la izquierda para despejar la columna del panel lateral.
5. Si los datos reales estuvieran disponibles (a través de la API backend), la función `cargarAnalisis` podría reemplazarse para_fetch los datos desde `/api/analysis` u otro endpoint, manteniendo la misma estructura de respuesta JSON.

### Datos reales vs. mock

- **Modo mock (predeterminado):** Carga `mock.json`. Usado para desarrollar la UI, probar componentes y demostrar la funcionalidad durante el hackathon sin necesidad de datos reales ni credenciales de Earthdata.
- **Modo real:** Cuando el backend provee datos procesados, `cargarAnalisis` podría obtener la misma estructura JSON desde el servidor. La UI no necesita cambios: cualquier JSON con la misma estructura (fuente, variable, unidad, periodo, pares) será compatible.

## Desarrollo

El proyecto usa `vite` como bundler y `svelte` como framework. La estructura de componentes es:

- `EarthGlobe.svelte` - El globo 3D con Three.js.
- `AnalysisPanel.svelte` - El panel lateral que muestra la información del par seleccionado.
- `TimelineControl.svelte` - El control de línea de tiempo.
- `lib/data/loadAnalysis.ts` - Funciones para cargar datos (mock o reales).
- `lib/data/mock.json` - Datos de ejemplo para desarrollo y testing.

Los estilos principales están en `app.css` y los estilos de componente en cada archivo `.svelte`. El diseño responsivo adapta la disposición de la grilla (dos columnas en escritorio, una columna en móvil) usando media queries CSS.
