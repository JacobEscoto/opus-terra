# Nuestra idea para el reto de la NASA

> Documento para el equipo. Está escrito en lenguaje simple a propósito: la idea es que todos entendamos qué vamos a hacer y por qué.

---

## 1. El reto en pocas palabras

La NASA nos pide hacer un software que muestre **cómo está cambiando la Tierra con el paso del tiempo**, usando datos de sus satélites. No basta con dibujar mapas bonitos. Tenemos que responder cuatro preguntas:

1. **¿Qué está cambiando?**
2. **¿Dónde?**
3. **¿Cuánto?**
4. **¿Es un cambio real o pudo ser casualidad?**

Hay un detalle importante: una misma causa puede tener efectos **opuestos** en distintas regiones. Por ejemplo, un mismo fenómeno puede traer más lluvia a un lugar y sequía a otro. El reto quiere que descubramos y expliquemos esos contrastes.

---

## 2. Nuestra idea, en una frase

**Un globo terráqueo 3D que encuentra los lugares del planeta donde las cosas cambian en direcciones contrarias, comprueba que el cambio es real y explica qué causa común lo provoca.**

---

## 3. Cómo lo vería una persona que usa el programa

1. Abre la página web y ve un globo 3D con colores. Cada color indica si algo está subiendo o bajando en esa zona.
2. Las zonas donde el cambio **no es confiable** aparecen marcadas como tales. Preferimos decir "no estamos seguros" antes que exagerar.
3. Mueve una línea de tiempo y ve cómo fue evolucionando el planeta año tras año.
4. El programa le propone **pares de regiones con cambios opuestos**: una donde algo sube y otra donde baja.
5. Al elegir un par, aparece un panel que compara las dos regiones lado a lado, con una explicación corta y sencilla de por qué cambian distinto.
6. Una tarjeta le explica qué significa ese nivel para las personas, usando las guías de la Organización Mundial de la Salud (OMS).

---

## 4. ¿Qué lo hace diferente de lo que ya existe?

Ya existen herramientas que muestran mapas con colores y hasta tendencias. Si solo hacemos eso, nos van a decir que es "más de lo mismo". Lo que nos separa es esto:

- **Busca los contrastes por sí solo.** El usuario no tiene que adivinar dónde mirar; el programa le muestra dónde hay cambios opuestos.
- **Explica el porqué.** Revisa si una causa común, como el fenómeno de El Niño, explica por qué dos regiones cambian de forma contraria.
- **Separa lo natural de lo nuevo.** Quita el efecto de esa causa natural para ver si el cambio sigue existiendo. Así respondemos "¿esto es real o solo es un vaivén normal del clima?".
- **Habla claro.** Cada resultado viene con una explicación en palabras normales, no con números sueltos.

Si alguien nos pregunta en qué se diferencia de Google Earth: **Google Earth muestra cómo se ve la Tierra; nosotros mostramos qué está cambiando y si ese cambio es real.**

---

## 5. ¿Qué dato vamos a usar?

Para no hacer un proyecto demasiado grande, elegimos **una sola variable principal**:

- **Contaminación del aire** (principalmente el dióxido de nitrógeno, que viene del tráfico y la industria).

Hay un detalle por confirmar: antes de comprometernos, vamos a comprobar con datos de prueba que esta variable realmente muestre regiones con cambios opuestos. Si no aparecen contrastes claros, cambiamos a **la lluvia**, que suele mostrar mejor ese efecto. La idea del proyecto no cambia, solo el dato.

---

## 6. ¿Y la salud, las inundaciones y las costas?

Estos temas salieron en las conversaciones y son importantes. Así los vamos a tratar:

| Tema | Qué hacemos con él |
|---|---|
| **Contaminación del aire** | Es el centro del proyecto. |
| **Salud** | La NASA no mide enfermedades ni síntomas. La usamos como **contexto**: explicamos por qué importa cada nivel de contaminación con las guías de la OMS. No damos diagnósticos ni decimos cómo afecta a una persona en particular. |
| **Inundaciones y costas** | Son una gran segunda etapa. Las mencionamos en la presentación como **lo que sigue**, pero no las construimos ahora. |

La razón es simple: es mejor entregar algo pequeño que funcione bien que algo enorme que quede a medias. A los jurados les importa que el problema esté bien planteado, que la solución funcione y que tenga sentido.

---

## 7. Puntos clave para no desviarnos

1. **Una sola pregunta:** ¿dónde cambian las cosas en direcciones opuestas y por qué?
2. **Una sola variable principal** para el prototipo.
3. **Todo dato del análisis viene de la NASA** (o de sus socios en el reto).
4. **Cada pantalla responde:** qué cambia, dónde, cuánto y si es real.
5. **Cualquier idea nueva pasa un filtro:** si no ayuda a responder la pregunta principal, se anota para "trabajo futuro".
6. **Decir siempre cuando algo es una suposición**, no un resultado comprobado.

---

## 8. Qué vamos a entregar

- Una **página web** que se abre con un enlace. No hay que instalar nada, funciona en computadora y también en celular.
- Un **video corto de respaldo**, por si falla el internet durante la presentación.
- Una **presentación de 3 a 5 minutos** con cuatro partes: el problema, la solución, el impacto y cómo podría crecer para ayudar en todo el mundo.

---

## 9. Cómo puede aportar cada quien

No hace falta programar para ser clave en este proyecto.

- **Investigación:** buscar qué políticas o hechos explican los cambios en las regiones que elijamos, y reunir fuentes confiables con enlace y fecha.
- **Análisis:** revisar que los resultados tengan sentido y anotar qué es firme y qué es solo una hipótesis.
- **Diseño:** dibujar las pantallas, elegir colores que todos puedan distinguir (sin depender solo de rojo y verde) y cuidar que todo se entienda rápido.
- **Presentación:** escribir el discurso, preparar las diapositivas y ensayar con el equipo.
- **Código:** a cargo de quien programa, con apoyo de todos para probar y dar opiniones.

---

## 10. Recursos que nos pueden servir

Estos recursos vienen en la página oficial del reto. Los ordenamos según qué tan útiles creemos que serán para esta idea.

### Los que más vamos a usar

- **Giovanni** (https://giovanni.gsfc.nasa.gov): una herramienta de la NASA donde eliges una variable (contaminación, lluvia, temperatura...) y te muestra cómo cambió con el tiempo. Es ideal para **explorar antes de programar** y comprobar si una idea tiene datos que la respalden.
- **KNMI Climate Explorer** (https://climexp.knmi.nl): una web de los Países Bajos para explorar datos del clima. Sirve para consultar el índice de El Niño y comparar con otras variables sin escribir código. Muy útil para el equipo que investiga.
- **Artículo sobre pruebas para detectar tendencias:** explica cómo saber si un cambio en el tiempo es real. Es la base de nuestra parte científica; conviene que alguien del equipo lo lea y haga un resumen de una hoja.
- **Guía sobre significancia estadística:** explica qué significa que un resultado sea "significativo" y no casualidad. Va de la mano con el artículo anterior.
- **Artículo sobre clorofila en zonas costeras:** es un ejemplo completo de cómo se hace una serie de tiempo y se comprueba que es significativa. Podemos copiar su forma de explicar el método.
- **AppEEARS** (https://appeears.earthdatacloud.nasa.gov): permite pedir datos de un punto o de una zona y recibir la serie de tiempo ya armada. Es útil para preparar datos con anticipación, aunque no responde al instante.
- **Climate Data Online (CDO)** (https://www.ncei.noaa.gov/cdo-web/): datos de estaciones de medición en tierra. Sirve para **comprobar** que lo que dicen los satélites coincide con lo que miden los instrumentos reales.

### Los que dejaríamos para después

- **Hydrology Time Series:** solo nos serviría si decidimos usar la humedad del suelo o el agua de los ríos como variable.
- **SWOT:** mide la altura del agua en lagos, ríos y mares, pero es una misión reciente y no tiene suficientes años de historia para ver tendencias largas.
- **Radarsat (RCM), Geo.ca y el tutorial de radar:** están más enfocados en Canadá o en mapear inundaciones con radar. Son interesantes para la segunda etapa, pero tienen mucha curva de aprendizaje para el tiempo que tenemos.
- **Monitoring and protecting our ecosystem from space:** buena lectura de contexto para la presentación, aunque no la necesitamos para construir nada.

### Otros recursos que también ayudan

- **Earthdata Search** (https://search.earthdata.nasa.gov): el buscador oficial de datos de la NASA. Ahí se encuentra el nombre exacto de cada conjunto de datos.
- **Worldview** (https://worldview.earthdata.nasa.gov): un visor de la NASA para ver imágenes del planeta. Nos sirve de referencia para saber qué ya existe y cómo diferenciarnos.
- **Guías de calidad del aire de la OMS:** para explicar en palabras simples cuándo un nivel de contaminación es preocupante.

---

## 11. Antes del evento y durante el evento

**Antes (hoy):**
- Crear la cuenta gratuita de **NASA Earthdata**.
- Confirmar que todos estamos registrados en el evento y en el mismo equipo.
- Explorar en Giovanni para decidir la variable y las regiones.
- Preparar bocetos, textos y el guion de la presentación.
- Dejar listas las herramientas en la computadora de quien programa.

**Durante el evento:**
- El código y el análisis se hacen durante el hackathon, ya que las reglas de estos eventos suelen pedir que el trabajo se cree en esos días. Conviene confirmar los términos del evento con la organización.
- Crear un repositorio público para el código, porque normalmente se pide enlazarlo al enviar el proyecto.
- Enviar el proyecto en la plataforma oficial antes del cierre.

---

## 12. Una frase para recordar

> "No queremos decir cuánto cambia un lugar. Queremos mostrar por qué dos lugares cambian de forma distinta, y comprobar que ese cambio es real."
