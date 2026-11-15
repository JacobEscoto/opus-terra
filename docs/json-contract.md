# Contrato de los JSON de análisis

[`backend/scripts/generate_analysis.py`](../backend/scripts/generate_analysis.py)
genera estos archivos y los escribe en `frontend/public/data/<región>/`; para la
región de ejemplo, `frontend/public/data/honduras/`:

- `merra2_t2m.json`
- `merra2_aer.json`
- `merra2_precipitacion.json`
- `imerg_precipitacion.json`
- `mod13c2_ndvi.json`

La aplicación lee la región activa en `/data/<región>/<variable>.json`. Los
bloques de ejemplo de este documento muestran las claves con valores recortados
o de muestra; los valores completos están en los archivos.

## Estructura común

```json
{
  "fuente": "identificador del producto",
  "variable": "identificador estable",
  "region": "honduras",
  "region_nombre": "Honduras",
  "nombre_variable": "nombre legible",
  "unidad": "unidad de los valores",
  "periodo": {
    "inicio": 2001,
    "fin": 2024,
    "mes_inicio": "2000-02",
    "mes_fin": "2025-09",
    "meses": 308,
    "anios_completos": [2001, 2002]
  },
  "contexto_oms": "texto de contexto ambiental",
  "pixeles_probados": 110,
  "pixeles_significativos_fdr": 45,
  "fdr": {
    "metodo": "Benjamini-Hochberg",
    "alfa": 0.05,
    "universo": "píxeles de Honduras",
    "p_valores_probados": 110
  },
  "resultados_pixeles": [],
  "pares": [],
  "metodologia": {
    "anomalia": "anomalía mensual respecto a la climatología del periodo efectivo",
    "enso": "remoción lineal mediante ONI mensual",
    "serie_anual": "promedio de residuos mensuales; solo años con 12 meses",
    "tendencia": "Mann-Kendall original y pendiente de Theil-Sen por píxel"
  }
}
```

### Identificación y periodo

- `fuente`: producto y versión de origen, por ejemplo `NASA MERRA-2 M2TMNXSLV
  v5.12.4`.
- `variable`: identificador estable que usa la aplicación para elegir el archivo
  (`merra2_t2m`, `mod13c2_ndvi`, etc.).
- `region` y `region_nombre`: identificador y nombre de la región analizada. La
  interfaz comprueba que `region` coincida con la carpeta desde la que leyó el
  archivo.
- `nombre_variable`: nombre legible que se muestra en la interfaz.
- `unidad`: unidad de los valores de esa variable. En las precipitaciones es una
  tasa (`kg m-2 s-1` en MERRA-2 y `mm/hr` en IMERG), no una lámina acumulada.
- `periodo.inicio` y `periodo.fin`: años que cubre la serie analizada. En las
  mallas son los años efectivos de la serie anual (2001 a 2024).
- `periodo.mes_inicio` y `periodo.mes_fin`: ventana mensual de la que se partió
  antes de descartar los años incompletos (2000-02 a 2025-09).
- `periodo.meses`: número de meses de esa ventana (308).
- `periodo.anios_completos`: años que tienen los 12 meses y entraron en la serie
  anual, en orden. La lista real de las mallas va de 2001 a 2024, con una entrada
  por año; en los promedios de área queda vacía porque no hay serie anual.
- `contexto_oms`: texto fijo que recuerda que el análisis es ambiental y no un
  diagnóstico de salud. La interfaz no lo muestra.

### Conteos y corrección por comparaciones múltiples

- `pixeles_probados`: celdas con una serie anual válida sobre las que se ejecutó
  la prueba de tendencia. Es 0 cuando el archivo no tiene malla.
- `pixeles_significativos_fdr`: celdas que quedaron con cambio claro después de
  la corrección por comparaciones múltiples.
- `fdr.metodo`: nombre del procedimiento de corrección aplicado
  (`Benjamini-Hochberg`).
- `fdr.alfa`: umbral de esa corrección, 0.05. Es la proporción de falsas alarmas
  que se acepta entre las celdas declaradas claras.
- `fdr.universo`: conjunto de pruebas que se corrigió en bloque, por ejemplo
  `píxeles de Honduras`.
- `fdr.p_valores_probados`: número de p-valores válidos que entraron en la
  corrección. En las mallas coincide con `pixeles_probados`.
- `fdr.estado`: solo aparece cuando no hay malla; vale
  `no_aplicable_sin_malla` y avisa de que la corrección no se aplicó. En ese caso
  los conteos de píxeles quedan en 0.

La corrección por comparaciones múltiples existe porque se prueban cientos o
miles de celdas a la vez: aunque nada estuviera cambiando, unas pocas parecerían
claras por puro azar. Benjamini-Hochberg ajusta el listón para que, entre todas
las celdas declaradas claras, la proporción esperada de falsas alarmas no supere
`fdr.alfa`. Por eso una celda puede tener un `p_valor` bajo y aun así quedar con
`significativa_fdr` en `false`.

### Metodología declarada

`metodologia` no es texto libre: repite en frases fijas los pasos que se
aplicaron, para que el archivo se explique sin abrir el código.

- `anomalia`: a cada mes se le resta el promedio de ese mismo mes en el periodo.
  Así se quita el ciclo anual y queda la diferencia respecto a lo habitual.
- `enso`: a esa anomalía se le resta la parte que se explica por el índice ONI,
  es decir, por El Niño y La Niña. Lo que queda es el residuo que se analiza.
- `serie_anual`: el valor de cada año es el promedio de sus residuos mensuales.
  Solo entran años con los 12 meses presentes.
- `tendencia`: por cada celda se aplica la prueba de Mann-Kendall para saber si
  hay cambio y la pendiente de Theil-Sen para medir cuánto por año.
- `mascara_calidad`: solo en la vegetación; repite el criterio de calidad
  aplicado antes del análisis (ver más abajo).
- `conversion_unidades`: solo en PM2.5; deja constancia de la conversión de
  unidades aplicada antes de analizar (ver más abajo).

`limitacion`, cuando aparece, es una frase que advierte qué no se puede concluir
del archivo. Está en la vegetación y en las dos precipitaciones; no está en
temperatura ni en PM2.5.

## Resultados por celda

Cada elemento de `resultados_pixeles` es una celda de la malla con su serie
anual y su prueba de tendencia. Cuando el contenido sin recortar supera los
3 MB, esta lista trae solo las celdas significativas para no pesar de más;
`pixeles_probados` y `pixeles_significativos_fdr` siguen contando el análisis
completo. Así ocurre con la vegetación de Honduras: 5538 celdas probadas y 2747
elementos en la lista.

```json
{
  "lat": 16.57499999999999,
  "lon": -89.37499999999999,
  "mann_kendall_z": -4.191944108175889,
  "p_valor": 2.7657414247039824e-05,
  "direccion": "decreciente",
  "sen_unidad_por_anio": -0.002691315142631449,
  "intercepto_sen": 0.02390726809847524,
  "coeficiente_enso": -0.001434045882269508,
  "r2_enso": 0.001418523722381937,
  "n_anios": 24,
  "valores_anuales": [0.0354, -0.0218],
  "valor_anual_inicial": 0.035406960839897895,
  "valor_anual_final": -0.021758110138588457,
  "cambio_porcentual": -161.45150451340237,
  "significativa_fdr": true
}
```

- `lat` y `lon`: centro de la celda en grados decimales.
- `mann_kendall_z`: medida de cuánto domina un sentido del cambio. Si es
  positiva, las subidas de un año al siguiente son más frecuentes que las
  bajadas; si es negativa, al revés. Cuanto más lejos de cero, más consistente
  es el patrón.
- `p_valor`: probabilidad de ver un patrón tan marcado como el observado si la
  serie solo variara al azar. Cuanto más pequeño, menos creíble es que sea
  casualidad.
- `direccion`: sentido del cambio según esa prueba: `creciente`, `decreciente` o
  `sin tendencia`.
- `sen_unidad_por_anio`: pendiente anual típica, en unidades de la variable por
  año. Se calcula con la mediana de las pendientes entre todos los pares de años,
  así que un año extremo no la arrastra. En temperatura, por ejemplo, son grados
  Celsius por año.
- `intercepto_sen`: valor donde arranca la recta de esa pendiente. Sirve para
  reconstruir la recta; no es un valor medido en la celda.
- `coeficiente_enso`: cuánto cambia el valor mensual por cada unidad del índice
  ONI. Indica el peso que tuvo El Niño o La Niña en esa celda antes de descontarlo.
- `r2_enso`: proporción de la variación mensual que explica el ONI en esa celda,
  de 0 a 1. Cerca de 0 significa que El Niño o La Niña explican poco; cerca de 1,
  que explican casi todo.
- `n_anios`: número de años completos usados en la prueba.
- `valores_anuales`: un valor por año completo, en orden cronológico y
  redondeado a cuatro decimales. Aquí se muestran solo el primero y el último;
  el archivo trae los 24.
- `valor_anual_inicial` y `valor_anual_final`: esos mismos extremos, con todos
  sus decimales.
- `cambio_porcentual`: diferencia entre el último y el primer valor anual,
  expresada como porcentaje del valor absoluto del primero. En las series de
  residuos, que rondan cero, un valor inicial diminuto produce porcentajes enormes
  o de signo contrario al de la tendencia; no debe leerse como cambio de cobertura
  o de magnitud.
- `significativa_fdr`: `true` si la celda superó la corrección por comparaciones
  múltiples; es decir, si su cambio se declara claro.

## Pares

`pares` es una lista de contrastes. Cada par contiene `id`, `region_a` y
`region_b`; cada región contiene `nombre`, `lat`, `lon`, `tendencia`,
`cambio_porcentual`, `significativa`, `explicacion`, `pais` y `ciudad`:

```json
{
  "id": "pixel-1",
  "region_a": {
    "nombre": "Belice",
    "lat": 16.57499999999999,
    "lon": -88.92499999999998,
    "tendencia": "alza",
    "cambio_porcentual": -525.7596768913194,
    "significativa": true,
    "explicacion": "La tendencia anual supera el umbral FDR de Benjamini-Hochberg.",
    "pais": "Belice",
    "ciudad": null
  },
  "region_b": {
    "nombre": "Cerca de Dolores, Peten, Guatemala",
    "lat": 16.57499999999999,
    "lon": -89.37499999999999,
    "tendencia": "bajada",
    "cambio_porcentual": -161.45150451340237,
    "significativa": true,
    "explicacion": "La tendencia anual supera el umbral FDR de Benjamini-Hochberg.",
    "pais": "Guatemala",
    "ciudad": "Dolores"
  }
}
```

`tendencia` usa `alza` o `bajada`, mientras que `direccion` en la celda usa
`creciente` o `decreciente`. `pais` y `ciudad` son la ubicación aproximada de la
celda; `ciudad` puede ser `null` cuando el punto no está cerca de una ciudad del
catálogo. `significativa` siempre es `true`, porque los pares solo se forman con
celdas que ya pasaron la corrección.

Un par solo se forma con una celda significativa con dirección `creciente` y otra
con dirección `decreciente`. Las celdas se emparejan en el orden en que vienen en
el archivo: la primera que sube con la primera que baja, la segunda con la
segunda, y así. Por eso el número de pares es el menor de los dos conteos.

Nunca se fabrican pares para rellenar la interfaz. La lista puede quedar vacía
aunque haya celdas significativas: la temperatura de Honduras tiene 45 celdas con
cambio claro y ningún par, porque todas van en la misma dirección y falta el
signo contrario.

## Precipitación: promedios de área

Los JSON de precipitación disponibles actualmente son **promedios de área**, no
mallas de píxeles. Sus archivos NetCDF no tienen dimensiones `lat` y `lon` para
la variable temporal. Por esta razón declaran:

```json
{
  "pixeles_probados": 0,
  "pixeles_significativos_fdr": 0,
  "periodo": {"anios_completos": []},
  "pares": [],
  "limitacion": "El insumo disponible es una serie area-promedio sin dimensiones lat/lon; no se fabricaron píxeles ni pruebas de significancia.",
  "fuente_periodo_disponible": {"inicio": 1996, "fin": 1996},
  "fdr": {"estado": "no_aplicable_sin_malla"}
}
```

- `periodo.inicio` y `periodo.fin` son la ventana común del proyecto (2000-2025),
  no la serie que trae el insumo.
- `fuente_periodo_disponible` dice qué años cubre realmente el archivo descargado.
  No es la serie publicada: en el insumo actual de MERRA-2 el archivo trae un solo
  año (1996), por eso `inicio` y `fin` coinciden, mientras IMERG trae 1998.
- `fdr.estado` explica por qué no hay significancias: no hay malla sobre la que
  probar.

No se interpretan los promedios de área como píxeles y no se reportan
significancias espaciales a partir de ellos.

## NDVI de MOD13C2

`mod13c2_ndvi.json` sigue la estructura común y añade el bloque `calidad` y una
`limitacion`:

```json
{
  "calidad": {
    "criterio": "criterio de máscara aplicado",
    "celdas_malla": 9324,
    "celdas_conservadas": 5538,
    "celdas_excluidas": 3786,
    "celda_meses_totales": 2871792,
    "celda_meses_validos": 1980948,
    "celda_meses_excluidos": 890844,
    "exclusiones_por_criterio": {},
    "meses_afectados": 308,
    "meses_totales": 308,
    "exclusiones_por_mes_maximo": {},
    "celdas_descartadas_por_calidad": 3786
  },
  "limitacion": "texto de advertencia",
  "metodologia": {"mascara_calidad": "criterio de máscara aplicado"}
}
```

El bloque `calidad` documenta la máscara aplicada antes del análisis para que el
resultado sea auditable. El criterio vive en
[`backend/src/opusterra/mod13c2.py`](../backend/src/opusterra/mod13c2.py), que
también produce estos conteos:

- `criterio`: la regla completa, en palabras: qué estados de calidad del producto
  se descartan (NDVI no producido, fiabilidad baja, MODLAND_QA no confiable,
  utilidad del VI inservible o bandera que no indica tierra).
- `celdas_malla`: celdas que trae la malla descargada, antes de la máscara.
- `celdas_conservadas`: celdas que tienen los 308 meses confiables y entran al
  análisis.
- `celdas_excluidas`: celdas de la malla que no se conservan.
- `celda_meses_totales`: celdas de la malla multiplicadas por meses.
- `celda_meses_validos`: celdas-mes que pasaron la máscara.
- `celda_meses_excluidos`: celdas-mes descartadas por la máscara.
- `exclusiones_por_criterio`: cuántas celdas-mes falla cada criterio por
  separado, con una entrada por criterio: `ndvi_no_producido`,
  `fiabilidad_no_confiable`, `modland_no_confiable`, `utilidad_inservible` y
  `no_vegetacion_tierra`. Una misma celda-mes puede fallar varios, así que la
  suma de estos conteos supera a `celda_meses_excluidos`.
- `meses_afectados` y `meses_totales`: meses con al menos una exclusión y meses
  de la ventana.
- `exclusiones_por_mes_maximo`: los cinco meses con más celdas-mes excluidas y su
  conteo.
- `celdas_descartadas_por_calidad`: celdas que el paso de análisis descartó por
  tener algún mes sin dato confiable. Hoy coincide con `celdas_excluidas`.

`metodologia.mascara_calidad` repite el `criterio` para que la metodología quede
completa sin abrir el bloque `calidad`. `limitacion` advierte que la serie
analizada es el residuo mensual sin estacionalidad ni ENSO: `cambio_porcentual`
se calcula sobre valores residuales cercanos a cero y no debe leerse como cambio
de cobertura vegetal. El recorte incluye celdas de países vecinos y del mar.

Todos los píxeles probados tienen 24 años completos (2001-2024), igual que en
`merra2_t2m.json`.

## PM2.5 de MERRA-2

`merra2_aer.json` usa la misma estructura de malla que la temperatura, con la
unidad `µg/m³`. Añade una entrada a `metodologia`:

```json
{
  "metodologia": {
    "conversion_unidades": "DUSMASS25 convertida de kg m-3 a µg/m³ multiplicando por 1e9"
  }
}
```

`conversion_unidades` deja constancia de que el valor original del producto venía
en `kg m-3` y de qué conversión se aplicó antes de analizarlo. Con los datos
actuales de Honduras el archivo tiene 110 celdas probadas, ninguna significativa
y ninguna pareja.

## Ejemplos reales

| Caso | Archivo | Qué muestra |
|------|---------|-------------|
| Malla con pares | `frontend/public/data/honduras/mod13c2_ndvi.json` | 5538 celdas probadas, 2747 significativas y 1119 pares porque hay celdas en ambos sentidos. |
| Malla sin pares | `frontend/public/data/honduras/merra2_t2m.json` | 110 celdas probadas y 45 significativas, todas crecientes, así que `pares` queda vacío. |
| Promedio de área | `frontend/public/data/honduras/merra2_precipitacion.json` | 0 celdas, `fdr.estado` en `no_aplicable_sin_malla` y `fuente_periodo_disponible` con un solo año, 1996. |
