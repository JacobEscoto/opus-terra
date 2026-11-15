# Contrato de los JSON de análisis

Los archivos públicos se generan con `backend/scripts/generate_analysis.py` y
se escriben en `frontend/public/data/`:

- `merra2_t2m.json`
- `merra2_precipitacion.json`
- `imerg_precipitacion.json`
- `mod13c2_ndvi.json`

## Estructura común

```json
{
  "fuente": "identificador del producto",
  "variable": "identificador estable",
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
  "metodologia": {}
}
```

`periodo.inicio` y `periodo.fin` representan los años efectivos de la serie
anual. `mes_inicio` y `mes_fin` conservan la ventana mensual usada antes de
descartar los años incompletos. `anios_completos` enumera exactamente los años
que entraron en la serie anual.

`pixeles_probados` es el número de celdas con una serie anual válida sobre las
que se ejecutó Mann-Kendall y Theil-Sen. `pixeles_significativos_fdr` es el
número de esas celdas que quedaron significativas después de aplicar
Benjamini-Hochberg sobre el conjunto completo de p-valores válidos.

Cada elemento de `resultados_pixeles` contiene `lat`, `lon`,
`mann_kendall_z`, `p_valor`, `direccion`, `sen_unidad_por_anio`,
`intercepto_sen`, `coeficiente_enso`, `r2_enso`, `n_anios`, los valores anual
inicial y final, `cambio_porcentual` y `significativa_fdr`.

## Pares

`pares` es una lista de contrastes. Cada par contiene `id`, `region_a` y
`region_b`; cada región contiene `nombre`, `lat`, `lon`, `tendencia`,
`cambio_porcentual`, `significativa` y `explicacion`.

Un par solo se forma con un píxel significativo tras FDR con dirección
`creciente` y otro píxel significativo tras FDR con dirección `decreciente`.
Si no existen ambos signos, la lista es vacía. Nunca se fabrican pares para
rellenar la interfaz.

## Precipitación

Los JSON de precipitación disponibles actualmente son **promedios de área**,
no mallas de píxeles. Sus archivos NetCDF no tienen dimensiones `lat` y `lon`
para la variable temporal. Por esta razón declaran:

```json
{
  "pixeles_probados": 0,
  "pixeles_significativos_fdr": 0,
  "periodo": {"anios_completos": []},
  "pares": [],
  "fdr": {"estado": "no_aplicable_sin_malla"}
}
```

No se interpretan los promedios de área como píxeles y no se reportan
significancias espaciales a partir de ellos.

## NDVI de MOD13C2

`mod13c2_ndvi.json` sigue la estructura común y añade dos bloques:

```json
{
  "calidad": {
    "criterio": "criterio de máscara aplicado, celdas conservadas y excluidas",
    "celdas_malla": 9324,
    "celdas_conservadas": 5538,
    "celdas_excluidas": 3786,
    "celda_meses_excluidos": 890844,
    "exclusiones_por_criterio": {}
  },
  "limitacion": "texto de advertencia"
}
```

El bloque `calidad` documenta la máscara de calidad de MOD13C2 aplicada antes
del análisis (ver `docs/decisions/0008-mascara-calidad-mod13c2.md`) para que
el resultado sea auditable. Todos los píxeles probados tienen 24 años completos
(2001-2024), igual que en `merra2_t2m.json`.
