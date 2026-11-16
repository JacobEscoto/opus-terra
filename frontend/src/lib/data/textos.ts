export const NAVEGACION = {
  glosario: "Glosario",
  fuentes: "Fuentes de datos",
  metodologia: "Metodología",
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
  avisoSinSerie: "Esta variable no incluye una serie anual por zona.",
  controlesTitulo: "Leyenda y línea de tiempo",
  abrirControles: "Mostrar leyenda y línea de tiempo",
  cerrarControles: "Ocultar controles",
  selectorVariable: "Variable",
  selectorRegion: "Región de datos",
} as const;

export const METODOLOGIA = {
  titulo: NAVEGACION.metodologia,
  introduccion:
    "Así se pasa de los productos de la NASA a los cambios que se ven en el globo. Cada paso se declaró en los archivos de resultados.",
  secciones: [
    [
      "Anomalía mensual",
      "A cada mes se le resta el promedio de ese mismo mes en el periodo, para quitar el ciclo anual y quedarse con la diferencia respecto a lo habitual.",
    ],
    [
      "Ajuste por ENSO",
      "De esa anomalía se descuenta la parte que explica el índice ONI, es decir, El Niño y La Niña. Lo que queda es el residuo que se analiza.",
    ],
    [
      "Serie anual",
      "El valor de cada año es el promedio de sus residuos mensuales. Solo entran años con los 12 meses completos; en la ventana actual eso deja 2001–2024.",
    ],
    [
      "Tendencia por celda",
      "Cada celda se prueba con Mann-Kendall para saber si hay cambio y con la pendiente de Theil-Sen para medir cuánto cambia por año.",
    ],
    [
      "Cambio claro",
      "Como se prueban miles de celdas a la vez, se aplica la corrección Benjamini-Hochberg (FDR 0.05). Una celda solo se marca como cambio claro si supera esa corrección.",
    ],
    [
      "Resolución y cobertura",
      "MERRA-2 usa 0.625° × 0.5° (unos 55 × 70 km), MODIS MOD13C2 0.05° (unos 5 × 5 km) e IMERG 0.1° (unos 11 × 11 km). Los análisis cubren Honduras y Centroamérica con un recorte rectangular.",
    ],
  ],
  limitacionesTitulo: "Limitaciones",
  limitaciones: [
    "Las precipitaciones disponibles son promedios de área, sin malla por celdas: no dicen dónde llueve más ni dónde cambia más.",
    "El NDVI se analiza como residuo mensual sin estacionalidad ni ENSO; el cambio porcentual no mide cobertura vegetal.",
    "El recorte rectangular incluye celdas de países vecinos y del mar, aunque el resultado se presente como una región.",
  ],
} as const;

export const EXPLICACIONES = {
  cambioClaro:
    "Cambio claro: es poco probable que sea casualidad, porque se mantiene aun después de descartar señales falsas.",
} as const;

export const LEYENDA = {
  titulo: "Cambios claros",
  frio: "Se enfría",
  neutro: "Sin cambio claro",
  calido: "Se calienta",
  noSignificativo: "Sin cambio significativo",
  descripcion:
    "El globo muestra cambios claros en azul y ámbar; las zonas grises no tienen un cambio claro.",
  aria: "Se enfría, sin cambio claro, se calienta; gris: sin cambio significativo",
} as const;

export const AYUDA_MAPA = {
  titulo: "Un mapa para mirar cambios",
  enlaces: [{ href: "#glosario", texto: NAVEGACION.glosario }],
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
      "Cambio cuya señal es suficientemente consistente para que sea poco probable que se deba al azar.",
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
    "Reúne información ambiental para ayudar a explorar tendencias de largo plazo.",
  ],
  fuentesTitulo: "Fuentes",
  fuentes: [
    {
      texto: "NASA GPM IMERG · GPM_3IMERGM · versión 07",
      url: "https://cmr.earthdata.nasa.gov/search/granules?short_name=GPM_3IMERGM",
    },
    {
      texto: "NASA MERRA-2 · M2TMNXFLX y M2TMNXSLV · versión 5.12.4",
      url: "https://cmr.earthdata.nasa.gov/search/granules?short_name=M2TMNXFLX",
    },
    {
      texto: "NASA MODIS · MOD13C2 · versión 061",
      url: "https://cmr.earthdata.nasa.gov/search/granules?short_name=MOD13C2",
    },
    {
      texto: "GeoNames (CC by 4.0). Nombres de ciudades y departamentos",
      url: "https://www.geonames.org",
    },
    {
      texto: "Natural Earth (dominio público). Fronteras de países",
      url: "https://www.naturalearthdata.com/",
    },
  ],
  fuenteOni: {
    texto: "NOAA/KNMI · índice ONI",
    url: "https://www.cpc.ncep.noaa.gov/data/indices/",
  },
  licencia: {
    texto: "Licencia MIT",
    url: "https://github.com/JacobEscoto/opus-terra/blob/main/LICENSE",
  },
  integrantes: [
    "Dana Ruiz",
    "Rose Hernández",
    "Nahomy Acosta",
    "Jacob Escoto",
    "José Ortiz",
    "Susan Flores",
  ],
  integrantesTitulo: "Integrantes",
} as const;
