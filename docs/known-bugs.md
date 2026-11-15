# Errores conocidos y límites de los datos

Esta página reúne lo que hoy funciona mal en la aplicación y lo que los datos
no permiten afirmar. Está escrita para leerse sin conocer el código.

Los conteos citados salen de los archivos de Honduras, la región que abre la
aplicación; al cambiar a Centroamérica los números cambian, pero los mismos
problemas se repiten. Para verlos en pantalla:

```bash
cd frontend
pnpm install
pnpm run dev
```

## Errores conocidos

### 1. El globo solo marca las celdas que suben

**Qué se ve.** En el globo no aparece ninguna zona que vaya a menos. Con la
vegetación hay 2.747 celdas con cambio claro: 1.628 suben y 1.119 bajan, pero
solo se dibujan las 1.628 que suben. El aviso del panel dice «Se muestran 1.628
de las 2.747 celdas significativas (ambos signos), priorizadas por magnitud»,
aunque las que bajan no están en el dibujo.

**Cómo comprobarlo.** Elegir «Vegetación (NDVI)» y comparar los puntos del
globo con las celdas que bajan en el archivo de datos: ninguna de esas celdas
tiene punto propio, porque al globo solo llegan las que suben.

**Dónde se origina.** `frontend/src/lib/data/capa.ts`.

### 2. La lista «Celdas significativas» del panel es parcial

**Qué se ve.** El bloque «Celdas significativas» usa la misma lista que el
globo, así que también deja fuera las celdas que bajan: con la vegetación
muestra 1.628 de las 2.747 celdas con cambio claro, aunque el aviso de encima
hable de «ambos signos».

**Cómo comprobarlo.** Abrir la vegetación y comparar la cantidad de entradas del
bloque con el número de celdas significativas que declara el archivo (2.747).

**Dónde se origina.** `frontend/src/lib/components/AnalysisPanel.svelte`.

### 3. Los pares no son regiones ni vecinos

**Qué se ve.** Los pares de zonas no son regiones ni vecinos: la primera celda
que sube se empareja con la primera que baja en el orden en que vienen en el
archivo. En la vegetación hay 1.119 pares; la mitad separa puntos a más de
274 km y el más lejano, a 614 km. Algunos pares unen «Belice» con «Cerca de
Dolores, Peten, Guatemala», o zonas de El Salvador y Nicaragua con Honduras.
Además, las dos zonas del par comparten exactamente la misma explicación («La
tendencia anual supera el umbral FDR de Benjamini-Hochberg»), que no dice por
qué una sube y la otra baja.

**Cómo comprobarlo.** Abrir la lista de pares con la vegetación y mirar los
nombres y las coordenadas de varios pares seguidos.

**Dónde se origina.** `backend/scripts/generate_analysis.py`.

### 4. Pares que dicen «alza» y guardan un porcentaje negativo

**Qué se ve.** En el archivo de la vegetación hay 60 pares en los que la zona
marcada como «alza» guarda un cambio porcentual negativo; el primero declara
«alza» con −525,76 %. El porcentaje se calcula con el primer y el último valor
de una serie de residuos que ronda cero, así que una diferencia diminuta
produce porcentajes enormes y de signo contrario a la etiqueta. El panel no
muestra ese porcentaje (usa la pendiente), pero el archivo queda contradictorio
para cualquiera que lo lea.

**Cómo comprobarlo.** Buscar en el archivo de la vegetación los pares cuya zona
«alza» tiene `cambio_porcentual` negativo.

**Dónde se origina.** `backend/scripts/generate_analysis.py`.

### 5. La temperatura no produce ningún par

**Qué se ve.** Con la temperatura el panel dice «Sin pares de tendencias
opuestas claras» y «No encontramos zonas con cambios opuestos», pero no explica
el motivo: las 45 celdas con cambio claro van todas en la misma dirección
(suben), así que falta la dirección de bajada para poder formar un par. La
aplicación lo presenta como si no hubiera cambios opuestos, no como un empate de
direcciones.

**Cómo comprobarlo.** Abrir la app con «Temperatura (T2M)»: el resumen habla de
45 zonas con cambio claro y la lista de pares está vacía.

**Dónde se origina.** `frontend/public/data/honduras/merra2_t2m.json`, que no
trae ninguna celda con dirección `decreciente`.

### 6. La precipitación no se dibuja y muestra tasas

**Qué se ve.** La precipitación no se dibuja en el globo y el panel la anuncia
como «promedio de área»: el archivo no tiene celdas (`pixeles_probados` es 0),
solo un promedio para toda la región. La unidad se muestra como tasa, en
`kg m-2 s-1` para MERRA-2 y `mm/hr` para IMERG, sin convertir a milímetros
acumulados. Y el periodo que anuncia el panel, 2000–2025, no coincide con la
serie que el propio archivo declara disponible: un solo año, 1996 en MERRA-2 y
1998 en IMERG.

**Cómo comprobarlo.** Cambiar a cualquiera de las dos precipitaciones: el globo
queda sin puntos y «Ver detalles técnicos» muestra la unidad de tasa y el
periodo.

**Dónde se origina.** `frontend/public/data/honduras/merra2_precipitacion.json`
y `frontend/public/data/honduras/imerg_precipitacion.json`.

### 7. La marca de cambio poco claro nunca aparece

**Qué se ve.** Las tarjetas de zona incluyen una marca para los cambios poco
claros («Sin señal clara»), pero nunca se ve: los pares solo se forman con
celdas que ya pasaron la prueba de significancia y todas llegan marcadas como
significativas. Es una marca que la interfaz conserva y que no se puede
encontrar en pantalla.

**Cómo comprobarlo.** Abrir cualquier par de la vegetación: las dos zonas
muestran «Alza» o «Bajada», nunca «Sin señal clara».

**Dónde se origina.** `frontend/src/lib/components/TrendMark.svelte`.

### 8. Las instrucciones de credenciales no funcionan

**Qué se ve.** Las instrucciones de credenciales de `backend/README.md` mandan
copiar una plantilla que no existe: al ejecutar `cp .env.example .env` dentro de
`backend/`, la terminal responde `cp: cannot stat '.env.example': No such file
or directory`. Aunque se cree el archivo a mano en `backend/`, el script no lo
lee: busca el `.env` en la raíz del repositorio.

**Cómo comprobarlo.** `cd backend && cp .env.example .env` y, después, crear un
`.env` dentro de `backend/` y ver que las credenciales siguen sin cargarse.

**Dónde se origina.** `backend/scripts/download_data.py` y el paso 3 de
`backend/README.md`.

## Límites de los datos y del método

Lo que el resultado no puede afirmar, aunque la pantalla lo parezca.

### La precipitación no tiene mapa

Los dos archivos de precipitación son promedios de toda la región, sin celdas.
Se puede decir cuánto llueve de media y cómo cambia esa media, pero no dónde
llueve más ni dónde cambia más. Por eso el globo no tiene puntos con esta
variable y el panel habla de «promedio de área».

### El porcentaje de cambio de la vegetación no mide cobertura vegetal

La serie del NDVI se analiza como anomalía mensual (la diferencia con lo normal
de cada mes) y sin la parte que explica el ENSO. El porcentaje se calcula sobre
esos residuos, que rondan cero, así que valores como −525 % no significan que la
vegetación se haya reducido: no se pueden leer como pérdida o ganancia de
cobertura.

### El recorte es rectangular y no solo cubre Honduras

Los análisis usan un rectángulo alrededor del país. Por eso entran celdas de
Belice, Guatemala, El Salvador y Nicaragua —aparecen en los pares de la
vegetación— y, en las variables de MERRA-2, celdas sobre el mar. Los resultados
se presentan como «Honduras», pero no son solo Honduras.

### La tendencia se calcula después de descontar El Niño y La Niña

Antes de la prueba de tendencia se quita de cada serie la parte que se explica
por el ENSO (índice ONI). El resultado responde «cambio que no se explica por El
Niño o La Niña», no «cambio causado por el clima»: un cambio por uso del suelo,
por una sequía puntual o por la calidad del dato puede aparecer igual, y parte
de una señal real puede quedar absorbida por ese ajuste.

## Comprobado: dos problemas que ya no ocurren

Estos dos comportamientos se revisaron y hoy no se pueden provocar; quedan
anotados para que nadie los investigue de nuevo.

- **La línea de tiempo ya no está siempre desactivada.** La temperatura y la
  vegetación traen 24 valores anuales por celda, así que el control se activa y
  cambiar el año cambia el color de los puntos. Solo queda desactivado en las
  precipitaciones, que no tienen serie anual, con el aviso «Esta variable no
  incluye una serie anual por zona».
- **El panel ya no dice «sin pares» cuando hay pares.** Con la vegetación la
  lista de pares aparece debajo del resumen. El mensaje de «sin pares» solo
  aparece cuando la lista está realmente vacía, como en la temperatura.
