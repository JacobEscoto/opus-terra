export const NAVEGACION = {
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
  avisoSinSerie: "Esta variable no incluye una serie anual por zona.",
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
