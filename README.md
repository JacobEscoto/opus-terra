# Trend Detective

**El globo terráqueo 3D que revela dónde el planeta cambia en direcciones opuestas, comprueba que el cambio es real y explica qué lo provoca.**

NASA Space Apps 2026 · Honduras

---

## El reto

La NASA nos pide construir un software que muestre **cómo está cambiando la Tierra con el paso del tiempo** usando datos de sus satélites. No basta con dibujar mapas bonitos. Hay que responder cuatro preguntas:

1. **¿Qué está cambiando?**
2. **¿Dónde?**
3. **¿Cuánto?**
4. **¿Es un cambio real o pudo ser casualidad?**

Y hay un detalle que lo cambia todo: **una misma causa puede tener efectos opuestos en distintas regiones**. Un mismo fenómeno puede traer más lluvia a un lugar y sequía a otro. El reto pide descubrir y explicar esos contrastes.

---

## El problema que resolvemos

Hoy existen mapas y visores que muestran colores sobre el planeta, e incluso mapas de tendencias. Pero les falta lo más importante:

- **No señalan dónde mirar.** El usuario tiene que saber de antemano qué región le interesa.
- **No explican el porqué.** Muestran *que* algo cambia, no *por qué* dos lugares se comportan de forma contraria.
- **No distinguen lo real de la casualidad.** Un vaivén natural del clima se ve igual que una tendencia nueva y significativa.
- **No hablan en lenguaje claro.** Suelen dejar al usuario frente a números sueltos sin contexto.

**Trend Detective** cierra esas cuatro brechas: encuentra los contrastes por sí solo, los explica, separa la señal real del ruido natural y lo cuenta con palabras normales.

---

## Qué hace la aplicación

- **Globo 3D interactivo.** Los colores muestran, región por región, si la variable está subiendo o bajando. Al abrir un par, la atmósfera se ilumina de forma pareja para señalar el contraste.
- **Línea de tiempo.** Mueve el periodo activo y observa cómo evoluciona el planeta año tras año.
- **Pares de contraste automáticos.** La app propone regiones con tendencias opuestas: una donde algo sube y otra donde baja. No tienes que adivinar dónde mirar.
- **Panel comparativo.** Al elegir un par, un panel compara ambas regiones lado a lado con una explicación corta y sencilla de por qué cambian distinto.
- **Marcas de confiabilidad.** Cuando la señal no alcanza significancia estadística, se marca como tal. Preferimos decir "no estamos seguros" antes que exagerar.
- **Contexto de salud.** Una tarjeta explica qué significa ese nivel para las personas, con las guías de la Organización Mundial de la Salud (OMS). Sin diagnósticos.
- **Sin instalación.** Se abre en el navegador, funciona en computadora y celular.

---

## Datos que usamos

Solo datos reales y verificables de la NASA y NOAA, recortados para la región de interés:

| Variable | Producto | Versión | Resolución | Cobertura |
|----------|----------|---------|------------|-----------|
| Precipitación observada | GPM IMERG | 07 | 0.1° × 0.1° | 1998-01 → 2025-09 |
| Precipitación modelada (PRECTOTCORR) | MERRA-2 flux (M2TMNXFLX) | 5.12.4 | 0.625° lon × 0.5° lat | 1996-01 → 2026-09 |
| Temperatura a nivel del suelo (T2M) | MERRA-2 superficie (M2TMNXSLV) | 5.12.4 | 0.625° lon × 0.5° lat | 1996-01 → 2026-09 |
| Vegetación (NDVI) | MODIS MOD13C2 | 061 | 0.05° × 0.05° | 2000-02 → 2026-10 |
| Índice Niño 3.4 (ONI) | NOAA / KNMI | — | — | 1996 → presente |

- **Centro de distribución:** NASA GES DISC. **Acceso:** Earthdata Search y OPeNDAP con recorte regional.
- **Ventana común de análisis:** 2000-02-01 a 2025-09-01, la intersección de las tres coberturas, para que todas las variables sean directamente comparables.
- **Formatos de entrega:** NetCDF como formato principal y GeoTIFF como respaldo.

> Las citas requeridas por producto y el detalle de cobertura están en [`docs/data-sources.md`](docs/data-sources.md). Las limitaciones del método están en [`docs/limitations.md`](docs/limitations.md).

---

## Cómo lo construimos

| Capa | Tecnología |
|------|-----------|
| Interfaz | Svelte 5 + TypeScript + Vite |
| Globo 3D | three.js |
| Datos | Python + `earthaccess` + `pydap` (OPeNDAP) + `xarray` / `rioxarray` |
| Formatos | NetCDF4 (principal) + GeoTIFF (respaldo) |

El backend descarga solo las variables y celdas de la región mediante OPeNDAP, en lugar de bajar archivos globales de cientos de megabytes. El detalle de cada decisión de diseño está en [`docs/decisions/`](docs/decisions/).

---

## En quién está pensado

- **Juries y evaluadores** del NASA Space Apps, que necesitan ver el valor en pocos minutos.
- **Docentes y estudiantes** que explican cambios climáticos y quieren una fuente visual y honesta.
- **Personas con curiosidad por el clima** que quieren explorar datos satelitales reales sin ser expertas en estadística.
- **Equipos de investigación** que necesitan un punto de partida visual para investigar contrastes regionales.

---

## Empezar

```bash
# Frontend (Svelte + Vite)
cd frontend
pnpm install
pnpm run dev

# Backend (descarga de datos NASA)
cd backend
uv sync
```

La guía completa está en [`frontend/README.md`](frontend/README.md) y [`backend/README.md`](backend/README.md).

---

## Licencia

MIT License

Copyright (c) 2026 JacobEscoto — ver [`LICENSE`](LICENSE).
