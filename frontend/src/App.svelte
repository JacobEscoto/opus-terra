<script lang="ts">
  import { onDestroy, onMount } from 'svelte'
  import EarthGlobe from './lib/components/EarthGlobe.svelte'
  import AnalysisPanel from './lib/components/AnalysisPanel.svelte'
  import TimelineControl from './lib/components/TimelineControl.svelte'
  import { cargarVariable, CATALOGO, type EstadoCarga } from './lib/data/loadAnalysis'
  import { prepararCapa, tieneValoresAnuales } from './lib/data/capa'
  import type { ParRegiones } from './lib/types/analysis'

  type FocusOn = (lat: number, lon: number, duracion: number) => Promise<void>
  type SetAutoRotate = (enabled: boolean) => void

  let carga = $state<EstadoCarga>({ estado: 'cargando' })
  let variableActiva = $state('merra2_t2m')
  let variablesCargadas = $state<string[]>([])
  let solicitud = 0

  /** Identificador del par elegido en la lista; null = vista de lista. */
  let idSeleccionado = $state<string | null>(null)

  /** Año mostrado en el panel cuando existan series anuales por celda. */
  let anio = $state<number>(2023)
  let capaTendenciaVisible = $state(true)
  let mostrarAyuda = $state(false)
  let recorridoActivo = $state(false)
  let focusOn = $state<FocusOn | null>(null)
  let cancelFocus = $state<(() => void) | null>(null)
  let setAutoRotate = $state<SetAutoRotate | null>(null)
  let timerRecorrido: ReturnType<typeof setTimeout> | null = null
  let recorridoToken = 0
  let enfoqueInicialHecho = false

  /**
   * En escritorio la columna del panel queda a la derecha: un offset negativo
   * desplaza el planeta hacia la izquierda dentro del canvas (prop existente
   * de EarthGlobe. En móvil
   * la columna es única y el planeta vuelve al centro.
   */
  let escritorio = $state(true)

  const desplazamiento = $derived(escritorio ? -0.17 : 0)

  const datos = $derived(carga.estado === 'listo' ? carga.datos : null)
  const preparacion = $derived(datos ? prepararCapa(datos) : null)
  const anualesDisponibles = $derived(datos ? tieneValoresAnuales(datos) : false)

  const parSeleccionado = $derived(
    datos
      ? datos.pares.find((par) => par.id === idSeleccionado) ?? null
      : null
  )

  function esperar(ms: number, token: number): Promise<boolean> {
    return new Promise((resolve) => {
      timerRecorrido = setTimeout(() => {
        timerRecorrido = null
        resolve(token === recorridoToken)
      }, ms)
    })
  }

  function detenerRecorrido() {
    recorridoToken += 1
    recorridoActivo = false
    if (timerRecorrido !== null) {
      clearTimeout(timerRecorrido)
      timerRecorrido = null
    }
    cancelFocus?.()
    setAutoRotate?.(true)
  }

  async function iniciarRecorrido(pares: ParRegiones[]) {
    if (recorridoActivo) {
      detenerRecorrido()
      return
    }
    if (!focusOn || pares.length === 0) return

    const token = ++recorridoToken
    recorridoActivo = true
    setAutoRotate?.(false)
    for (const par of pares) {
      if (token !== recorridoToken) return
      idSeleccionado = par.id
      const lat = (par.region_a.lat + par.region_b.lat) / 2
      const lon = (par.region_a.lon + par.region_b.lon) / 2
      await focusOn(lat, lon, 2000)
      if (token !== recorridoToken) return
      if (!(await esperar(4000, token))) return
    }
    if (token === recorridoToken) {
      recorridoActivo = false
      idSeleccionado = null
      setAutoRotate?.(true)
    }
  }

  function onGlobeReady(
    nextFocusOn: FocusOn,
    nextCancelFocus: () => void,
    nextSetAutoRotate: SetAutoRotate,
  ) {
    focusOn = nextFocusOn
    cancelFocus = nextCancelFocus
    setAutoRotate = nextSetAutoRotate
  }

  $effect(() => {
    if (carga.estado !== 'listo' || !focusOn || enfoqueInicialHecho) return
    enfoqueInicialHecho = true
    void focusOn(14.75, -86.25, 2000)
  })

  /** Lee el JSON seleccionado y reemplaza la capa sin crear otra escena. */
  async function cambiarVariable(id: string) {
    detenerRecorrido()
    const numeroSolicitud = ++solicitud
    variableActiva = id
    carga = { estado: 'cargando' }
    idSeleccionado = null
    try {
      const resultado = await cargarVariable(id)
      if (numeroSolicitud !== solicitud) return
      if (!variablesCargadas.includes(id)) variablesCargadas = [...variablesCargadas, id]
      carga = { estado: 'listo', datos: resultado }
      anio = resultado.periodo.fin
    } catch (error: unknown) {
      if (numeroSolicitud !== solicitud) return
      carga = {
        estado: 'error',
        mensaje:
          error instanceof Error
            ? error.message
            : 'No se pudieron leer los datos de análisis.',
      }
    }
  }

  function cargar() {
    void cambiarVariable(variableActiva)
  }

  onMount(() => {
    void cambiarVariable(variableActiva)

    // Sincroniza el desplazamiento del planeta con el punto de quiebre del layout.
    const consulta = window.matchMedia('(min-width: 1000px)')
    escritorio = consulta.matches
    const actualizar = (evento: MediaQueryListEvent) => (escritorio = evento.matches)
    consulta.addEventListener('change', actualizar)
    return () => consulta.removeEventListener('change', actualizar)
  })

  onDestroy(() => {
    detenerRecorrido()
    cancelFocus?.()
  })
</script>

<svelte:head>
  <title>OpusTerra — Mapa de cambios ambientales</title>
  <meta
    name="description"
    content="Explora tendencias ambientales globales con datos satelitales y modelos climáticos verificables."
  />
  <meta property="og:title" content="OpusTerra — Mapa de cambios ambientales" />
  <meta
    property="og:description"
    content="Explora tendencias ambientales globales con datos satelitales y modelos climáticos verificables."
  />
</svelte:head>

<!-- dataMode ilumina el planeta de forma pareja mientras un par está abierto;
     horizontalOffset lo corre a la izquierda para despejar la columna del panel. -->
  <EarthGlobe
    horizontalOffset={desplazamiento}
    dataMode={parSeleccionado !== null}
    celdas={preparacion?.celdas ?? []}
    capaVisible={capaTendenciaVisible}
    anio={anio}
    anios={datos?.periodo.anios_completos ?? []}
    escalaMaxima={preparacion?.escalaMaxima}
    onReady={onGlobeReady}
    onInteraction={detenerRecorrido}
  />

<main class="interface">
  <header class="masthead">
    <span>OpusTerra by Pegaso-X</span>
    <p class="welcome">Explora cómo cambian la temperatura, la lluvia y la vegetación del planeta.</p>
    <button
      class="about-button"
      type="button"
      aria-expanded={mostrarAyuda}
      aria-controls="about-panel"
      onclick={() => (mostrarAyuda = !mostrarAyuda)}
    >¿Cómo leer este mapa?</button>
  </header>

  {#if mostrarAyuda}
    <dialog id="about-panel" class="about-panel" aria-labelledby="about-title" open>
      <h2 id="about-title">Un mapa para mirar cambios</h2>
      <p>
        OpusTerra reúne observaciones satelitales y modelos climáticos para ayudarte a explorar
        dónde cambian la temperatura, la lluvia y la vegetación.
      </p>
      <p>
        Elige una variable, gira el planeta y abre un contraste para leer la señal y su contexto.
      </p>
    </dialog>
  {/if}

  <!-- Columna del planeta: el globo vive detrás, aquí solo va la línea de tiempo. -->
  <div class="stage">
    <div class="timeline-slot">
      {#if datos}
        <TimelineControl
           inicio={datos.periodo.inicio}
           fin={datos.periodo.fin}
           bind:anio
           disponible={anualesDisponibles}
           aviso="Esta variable no incluye una serie anual por celda."
        />
      {/if}
    </div>
  </div>

  <!-- Columna del panel: superficie propia, sin tapar el planeta. -->
  <aside class="rail">
    <div class="rail-slot">
      <AnalysisPanel
        carga={carga}
        parSeleccionado={parSeleccionado}
        onSeleccionar={(id) => (idSeleccionado = id)}
        onVolver={() => (idSeleccionado = null)}
        onReintentar={cargar}
        variables={CATALOGO}
        variableActiva={variableActiva}
        variablesCargadas={variablesCargadas}
        preparacion={preparacion}
        onCambiarVariable={(id) => void cambiarVariable(id)}
        capaVisible={capaTendenciaVisible}
        onAlternarCapa={() => (capaTendenciaVisible = !capaTendenciaVisible)}
        recorridoActivo={recorridoActivo}
        onRecorrido={() => datos && void iniciarRecorrido(datos.pares)}
        anio={anio}
        anualesDisponibles={anualesDisponibles}
        escalaMaxima={preparacion?.escalaMaxima ?? 1}
      />
    </div>
  </aside>

  <footer class="credits">
    <p>Fuentes: NASA MERRA-2, MODIS, GPM, NOAA/KNMI.</p>
    <p>Información ambiental; no es un diagnóstico de salud.</p>
  </footer>
</main>

<style>
  /* La .interface global es pointer-events: none; los slots reactivan los
     eventos solo donde hay controles, para no bloquear la órbita del globo. */
  .interface {
    display: grid;
    grid-template-columns: 1fr minmax(340px, 430px);
    grid-template-rows: auto 1fr;
    grid-template-areas:
      'masthead masthead'
      'stage    rail'
      'credits  credits';
    column-gap: 48px;
  }

  .masthead {
    grid-area: masthead;
    justify-content: space-between;
    pointer-events: auto;
  }

  .welcome {
    max-width: 48ch;
    margin: 0 auto 0 32px;
    color: var(--muted);
    font-size: 11px;
    line-height: 1.5;
  }

  .stage {
    grid-area: stage;
    min-height: 0;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: flex-start;
    padding-bottom: 4px;
  }

  .rail {
    grid-area: rail;
    min-width: 0;
  }

  .credits {
    grid-area: credits;
    display: flex;
    justify-content: space-between;
    gap: 24px;
    padding-top: 16px;
    border-top: 1px solid var(--hairline);
    color: var(--faint);
    font: 9px/1.5 var(--mono);
    pointer-events: auto;
  }

  .rail-slot,
  .timeline-slot {
    pointer-events: auto;
  }

  /* Columna única: panel debajo del masthead, línea de tiempo al final. */
  @media (max-width: 899px) {
    .interface {
      grid-template-columns: 1fr;
      grid-template-rows: auto minmax(180px, 1fr) auto auto;
      grid-template-areas:
        'masthead'
        'stage'
        'rail'
        'credits';
      column-gap: 0;
    }

    .stage {
      justify-content: flex-end;
      padding-top: 18px;
    }

    .rail {
      position: relative;
      z-index: 2;
      width: 100%;
    }

    .rail-slot {
      pointer-events: auto;
    }

    .credits {
      position: relative;
      z-index: 3;
      flex-direction: column;
      gap: 4px;
      padding-bottom: 4px;
    }
  }

  @media (max-width: 650px) {
    .welcome {
      display: none;
    }

    .stage {
      padding-top: 15px;
    }
  }
</style>
