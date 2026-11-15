export const NAVEGACION = {
  metodologia: "Metodología",
  glosario: "Glosario",
  acerca: "Acerca de",
  volver: "Volver al mapa",
  comoLeer: "¿Cómo leer este mapa?",
  menu: "Abrir menú",
  cerrarMenu: "Cerrar menú",
} as const;

export const APP = {
  marca: "OpusTerra",
  bienvenida:
    "Explora cómo cambian la temperatura, la lluvia y la vegetación del planeta.",
  ayudaTitulo: "Un mapa para mirar cambios",
  ayudaTexto:
    "OpusTerra reúne observaciones satelitales y modelos climáticos para ayudarte a explorar dónde cambian la temperatura, la lluvia y la vegetación.",
  fuentesPie: "Fuentes: NASA MERRA-2, MODIS, GPM, NOAA/KNMI.",
  avisoSinSerie: "Esta variable no incluye una serie anual por celda.",
  aclaracion: "Información ambiental; no es un diagnóstico de salud.",
} as const;

export const LEYENDA = {
  titulo: "Cambios claros",
  leve: "Cambio leve",
  fuerte: "Cambio fuerte",
  descripcion:
    "Cada punto es una zona donde el cambio es claro y no parece casualidad",
  aria: "De cambio leve a cambio fuerte",
  // Coincide con COLOR_NEUTRO y COLOR_CALIDO en tendenciaLayer.ts.
  colorLeve: "#d9d4c8",
  colorFuerte: "#d99435",
  // pendiente: bajadas
} as const;

export const AYUDA_MAPA = {
  titulo: "Un mapa para mirar cambios",
  enlaces: [
    { href: "#metodologia", texto: NAVEGACION.metodologia },
    { href: "#glosario", texto: NAVEGACION.glosario },
  ],
} as const;

export const METODOLOGIA = {
  titulo: NAVEGACION.metodologia,
  introduccion:
    "Cómo pasamos de muchas mediciones a un mapa que se puede explorar.",
  secciones: [
    {
      titulo: "Qué medimos",
      parrafos: [
        "Medimos la temperatura del aire a 2 metros, la lluvia y la vegetación. La temperatura es el calor del aire cerca de la superficie; la lluvia es el agua que cae; y el índice NDVI es una medida de qué tan verde y activa está la vegetación.",
      ],
    },
    {
      titulo: "Cómo limpiamos los datos",
      parrafos: [
        "Quitamos la variación normal de cada mes del año y el efecto de El Niño y La Niña. Para hacerlo usamos el índice ONI, una medida de la temperatura del océano Pacífico que publican NOAA y KNMI.",
      ],
    },
    {
      titulo: "Cómo buscamos tendencias",
      parrafos: [
        "Usamos un valor por cada año completo, de 2001 a 2024, para cada zona. La prueba de Mann-Kendall comprueba si la dirección del cambio se mantiene de forma constante; el estimador de Sen calcula el ritmo de ese cambio.",
      ],
    },
    {
      titulo: "Cómo evitamos falsas señales",
      parrafos: [
        "Cuando miramos miles de zonas, algunas pueden parecer cambiar por azar. Solo marcamos como «cambio claro» lo que sobrevive una corrección estadística de Benjamini-Hochberg, que controla cuántas señales falsas aceptamos.",
      ],
    },
    {
      titulo: "Qué no hace la app",
      parrafos: [
        "No predice, no emite alertas y no diagnostica problemas de salud ni peligros. Es una herramienta para explorar tendencias de largo plazo.",
      ],
    },
    {
      titulo: "Límites",
      parrafos: [
        "Cada zona de MERRA-2 mide unos 55 × 70 km y cada zona de MODIS unos 5 km. La precipitación solo tiene un promedio de toda el área, sin un mapa por zonas.",
        "En vegetación, descartamos las celdas con nubes o datos no confiables. Un cambio en NDVI no significa necesariamente un cambio de cobertura vegetal.",
        "El análisis termina en 2024 porque GPM no tiene datos completos de 2025. Los nombres de lugares son aproximados: indican algo que está «cerca de» ese lugar.",
      ],
    },
  ],
} as const;

export const GLOSARIO = {
  titulo: NAVEGACION.glosario,
  introduccion:
    "Palabras clave para leer el mapa sin tener que conocer estadística o teledetección.",
  terminos: [
    [
      "Tendencia",
      "Dirección general en la que cambia una medida a lo largo de varios años.",
    ],
    [
      "Cambio claro",
      "Cambio cuya señal es suficientemente consistente para que sea poco probable que se deba al azar, después de la corrección estadística.",
    ],
    [
      "Ritmo de cambio (pendiente)",
      "Cuánto cambia una medida, en promedio, por cada año.",
    ],
    [
      "Anomalía",
      "Diferencia entre una medición y lo que normalmente se espera para ese mes o periodo.",
    ],
    [
      "ENSO / El Niño y La Niña",
      "ENSO es el nombre del ciclo natural del océano y la atmósfera del Pacífico; El Niño y La Niña son sus dos fases principales.",
    ],
    [
      "ONI",
      "Índice que resume el calentamiento o enfriamiento del Pacífico y ayuda a identificar El Niño y La Niña.",
    ],
    [
      "NDVI",
      "Índice de vegetación que usa la luz reflejada por las plantas para estimar qué tan verde y activa está la vegetación.",
    ],
    [
      "Zona o celda",
      "Una parte del territorio dentro de una cuadrícula; cada zona se analiza como una unidad.",
    ],
    [
      "Serie anual",
      "Conjunto de valores, uno por cada año completo, que permite comparar cómo cambia una zona.",
    ],
    [
      "MERRA-2",
      "Modelo de la NASA que combina observaciones y cálculos para describir condiciones de la atmósfera, incluida la temperatura.",
    ],
    [
      "GPM IMERG",
      "Producto de la NASA que estima la precipitación a partir de observaciones de satélites.",
    ],
    [
      "MODIS",
      "Instrumento de los satélites Terra y Aqua que observa la superficie de la Tierra, incluida su vegetación.",
    ],
  ] as const,
} as const;

export const ACERCA = {
  titulo: NAVEGACION.acerca,
  parrafos: [
    "OpusTerra es una herramienta desarrollada por Pegaso-X en Honduras para el reto NASA Space Apps Challenge 2026: «Be An Earth System Trend Detective».",
    "Reúne información ambiental para ayudar a explorar tendencias de largo plazo. La información es ambiental; no es un diagnóstico de salud.",
  ],
  fuentesTitulo: "Fuentes",
  fuentes: [
    "NASA GPM IMERG. GPM_3IMERGM. Versión 07. Goddard Space Flight Center. https://cmr.earthdata.nasa.gov/search/granules?short_name=GPM_3IMERGM",
    "NASA MERRA-2. M2TMNXFLX y M2TMNXSLV. Versión 5.12.4. Goddard Space Flight Center. https://cmr.earthdata.nasa.gov/search/granules?short_name=M2TMNXFLX",
    "NASA MODIS. MOD13C2. Versión 061. Goddard Space Flight Center. https://cmr.earthdata.nasa.gov/search/granules?short_name=MOD13C2",
  ],
  fuenteOni: "NOAA/KNMI (ONI).",
  licencia: "Licencia MIT (ver LICENSE).",
  integrantes: "[Completar: nombres del equipo]",
  integrantesTitulo: "Integrantes",
} as const;
