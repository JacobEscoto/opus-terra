# OpusTerra — Frontend

Aplicación web de una sola página (Svelte 5, TypeScript y Vite) que muestra en un globo 3D las zonas donde el cambio ambiental es claro, para Honduras y Centroamérica, y compara pares de zonas con tendencias opuestas.

La app no calcula estadística en el navegador: lee los resultados que genera el backend, publicados como archivos JSON estáticos en `frontend/public/data/`. El detalle del contrato está en [`docs/json-contract.md`](../docs/json-contract.md) y los errores y límites conocidos en [`docs/known-bugs.md`](../docs/known-bugs.md).

## Cómo ejecutarla

```bash
# 1. Entra en el directorio frontend
cd frontend

# 2. Instala las dependencias (solo la primera vez)
pnpm install

# 3. Inicia el servidor de desarrollo
pnpm run dev
```

El servidor queda en http://localhost:5173 (el puerto estándar de Vite). Los cambios en los archivos se recargan solos (`HMR`).

### Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `pnpm run dev` | Inicia el servidor de desarrollo con HMR (Hot Module Replacement). |
| `pnpm run build` | Genera una versión de producción estática en `dist/`. |
| `pnpm run preview` | Previsualiza el build de producción localmente. |
| `pnpm run check` | Ejecuta TypeScript y Svelte type-checking para validar el código. |

## De dónde salen los datos

El recorrido real de los datos es este:

1. `frontend/src/App.svelte` arranca con la región `honduras` y la variable `merra2_t2m`. Al montar llama a `cargarVariable("merra2_t2m", "honduras")` y a `cargarRegiones()`, las dos de `frontend/src/lib/data/loadAnalysis.ts`. Cada cambio de variable o de región vuelve a llamar a `cargarVariable`.
2. `cargarVariable` pide el archivo por `fetch`, con la ruta `/data/<región>/<variable>.json`. Los archivos viven en `frontend/public/data/` y son:

   ```text
   frontend/public/data/
   ├── regiones.json          # regiones disponibles para el selector
   ├── honduras/
   │   ├── merra2_t2m.json
   │   ├── merra2_precipitacion.json
   │   ├── imerg_precipitacion.json
   │   └── mod13c2_ndvi.json
   └── centroamerica/
       ├── merra2_t2m.json
       ├── merra2_precipitacion.json
       ├── imerg_precipitacion.json
       └── mod13c2_ndvi.json
   ```

   El selector de variables usa el catálogo `CATALOGO` de `loadAnalysis.ts`: temperatura (T2M), precipitación MERRA-2, precipitación IMERG y vegetación (NDVI). `frontend/public/data/honduras/merra2_aer.json` y `frontend/public/data/centroamerica/merra2_aer.json` existen en disco, pero no se ofrecen porque no están en ese catálogo.
3. Antes de dibujar nada, `validarAnalisis` revisa la estructura del JSON: variable, unidad, región, periodo, celdas probadas y significativas, pares y resultados por celda. Si falta un campo o un valor no es válido, lanza un mensaje claro en lugar de mostrar datos a medias.
4. El resultado validado se guarda en memoria (un `Map` en `loadAnalysis.ts`) antes de dibujarse: la interfaz no vuelve a calcular nada a partir del JSON.
5. `cargarRegiones` lee `/data/regiones.json`: la lista de regiones con su nombre, su recuadro (`bbox`) y las variables declaradas para cada una. El selector de región del panel se llena con esa lista.

### Si los datos no llegan

El panel muestra el mensaje que devuelve la validación, por ejemplo:

```text
El JSON de análisis no se pudo leer (HTTP 404): /data/honduras/merra2_t2m.json.
```

Debajo aparece el botón **Reintentar**, que vuelve a pedir el mismo archivo. El mensaje cambia según la causa: `No se pudo conectar para leer …`, `El JSON de análisis no es válido: …` o `… declara la región "centroamerica", no honduras.` Para repararlo, comprueba que el archivo exista en `frontend/public/data/<región>/<variable>.json` y, si falta o está incompleto, vuelve a generarlo con `backend/scripts/generate_analysis.py` (ver [`backend/README.md`](../backend/README.md)) antes de pulsar **Reintentar**.

### `mock.json` no se usa

`frontend/src/lib/data/mock.json` es un archivo de ejemplo que **no se usa**: ninguna parte de `frontend/src` lo importa ni lo pide por red. La aplicación no tiene modo de ejemplo ni arranca con datos falsos: siempre pide los JSON de `frontend/public/data/`. Si te lo encuentras, no lo edites pensando que cambia la pantalla; está anotado en [`docs/known-bugs.md`](../docs/known-bugs.md).

## La capa del globo

Los marcadores del globo se arman en tres pasos:

1. **Qué se dibuja — `frontend/src/lib/data/capa.ts`.** `prepararCapa` se queda con las celdas que el JSON marca como significativas y cuya pendiente es positiva: **solo se dibujan las tendencias al alza**, las que van a la baja quedan fuera del globo aunque el archivo las contenga. Las ordena por magnitud de la pendiente y recorta la lista al tope `MAXIMO_CELDAS_CAPA` (2500 marcadores). También calcula la escala de color fija (`escalaMaxima`) y los textos del panel (`fraseResumen`, `unidadLegible`, `escalaCelda`). `tieneValoresAnuales` indica si el JSON trae un valor por año y por celda.
2. **Cómo se dibuja — `frontend/src/lib/three/tendenciaLayer.ts`.** `agregarCapa` crea un punto por celda sobre la esfera, en su latitud y longitud; `actualizarColores` recolorea esos puntos con el valor del año elegido; `quitarCapa` los retira.
3. **Quién lo conecta — `frontend/src/lib/components/EarthGlobe.svelte`.** Crea la escena (`EarthScene`), le pasa las celdas a la capa, la vuelve a armar cuando cambian los datos, actualiza los colores cuando cambia el año, la quita cuando se oculta y entrega a `App.svelte` los controles de cámara (`focusOn`, `setAutoRotate`) que usa el recorrido por las zonas.

## Estructura

`frontend/src/App.svelte` es el punto de entrada: guarda la región y la variable activas, el estado de carga, el par seleccionado, el año y la visibilidad de la capa, y reparte esos datos entre el globo y el panel.

### `frontend/src/lib/components/`

- `AnalysisPanel.svelte` — panel de análisis: resumen, selector de región y de variable, control de los marcadores, leyenda, lista de pares, tarjetas de zona y lista de celdas; en pantallas pequeñas se pliega con «Abrir panel» / «Cerrar panel».
- `EarthGlobe.svelte` — monta la escena 3D, la capa de marcadores y muestra el progreso de carga de las texturas.
- `GlobeLegend.svelte` — leyenda del globo, de cambio leve a cambio fuerte, con el año activo cuando la variable trae serie anual.
- `Legend.svelte` — escala anual de colores del panel, con el año y la escala fija.
- `PairList.svelte` — lista de pares de zonas con tendencias opuestas, que muestra los primeros ochenta y amplía por tramos.
- `RegionCard.svelte` — tarjeta de una zona del par: nombre, marca de tendencia, cambio acumulado y coordenadas.
- `TimelineControl.svelte` — control de línea de tiempo por año; se desactiva cuando la variable no trae serie anual por celda.
- `TrendMark.svelte` — marca de tendencia: «Alza», «Bajada» o «Sin señal clara».
- `VariableSelector.svelte` — botones de variable; señala las que todavía no se han leído.
- `paginas/Glosario.svelte` — página del glosario de términos.
- `paginas/AcercaDe.svelte` — página del proyecto, sus fuentes, integrantes y licencia.

### `frontend/src/lib/three/`

- `earthScene.ts` — escena, cámara, órbita, texturas del planeta y enfoque sobre un punto.
- `tendenciaLayer.ts` — marcadores de la capa de tendencias y sus colores por año.
- `textures.ts` — carga de texturas y las que se generan por código (nubes, halo, estrellas).

### `frontend/src/lib/data/` y `frontend/src/lib/types/`

- `loadAnalysis.ts` — catálogo de variables y lectura y validación de los JSON.
- `capa.ts` — qué celdas se dibujan y qué textos las explican.
- `textos.ts` — textos fijos de la interfaz: menú, glosario, leyenda y avisos.
- `mock.json` — archivo de ejemplo sin uso (ver arriba).
- `types/analysis.ts` — tipos TypeScript del contrato que consumen los componentes.

## Qué se ve en pantalla

- **Escritorio.** El panel de análisis ocupa una columna a la derecha y el planeta se desplaza hacia la izquierda para despejarla (el desplazamiento se activa a partir de 1000 px de ancho). El panel se ve completo, sin botón de plegado.
- **Pantallas pequeñas.** La disposición pasa a una sola columna por debajo de 900 px: el globo arriba y el panel debajo, plegado. El botón «Abrir panel» / «Cerrar panel» muestra u oculta su contenido. Por debajo de 650 px la línea de tiempo se pega al borde inferior del globo y la leyenda queda arriba.
- **Línea de tiempo.** Aparece activa con temperatura y vegetación: cambiar el año cambia el color de los puntos. Aparece desactivada en las dos precipitaciones, con el aviso «Esta variable no incluye una serie anual por zona.», porque esos archivos son promedios de área y no traen serie anual por celda.
- **Marcadores.** Solo se dibujan las tendencias al alza. El botón «Ocultar» / «Mostrar» del panel quita y devuelve los puntos sin volver a pedir los datos.
- **Pares de zonas.** La lista aparece solo cuando hay zonas claras en las dos direcciones; hoy solo la vegetación forma pares. Si no hay, el panel dice «Sin pares de tendencias opuestas claras». Con pares, el botón «Ver recorrido» / «Detener» pasea la cámara par por par.
- **Páginas informativas.** El menú (☰) abre el glosario y la página «Acerca de» sin salir de la aplicación.

Los errores conocidos de la aplicación y los límites de los datos están en [`docs/known-bugs.md`](../docs/known-bugs.md); las fuentes y sus identificadores, en [`docs/data-sources.md`](../docs/data-sources.md).
