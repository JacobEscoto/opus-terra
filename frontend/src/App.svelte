<script lang="ts">
  import { onDestroy, onMount } from 'svelte'
  import EarthGlobe from './lib/components/EarthGlobe.svelte'
  import AnalysisPanel from './lib/components/AnalysisPanel.svelte'
  import TimelineControl from './lib/components/TimelineControl.svelte'
  import { cargarVariable, CATALOGO, type EstadoCarga } from './lib/data/loadAnalysis'
  import { prepararCapa, tieneValoresAnuales } from './lib/data/capa'
  import type { ParRegiones } from './lib/types/analysis'
  import GlobeLegend from './lib/components/GlobeLegend.svelte'
  import Metodologia from './lib/components/paginas/Metodologia.svelte'
  import Glosario from './lib/components/paginas/Glosario.svelte'
  import AcercaDe from './lib/components/paginas/AcercaDe.svelte'
  import { APP, AYUDA_MAPA, NAVEGACION } from './lib/data/textos'

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
  type Pagina = 'metodologia' | 'glosario' | 'acerca'
  let pagina = $state<Pagina | null>(null)
  let enlaceQueAbrioPagina = $state<HTMLElement | null>(null)
  let menuAbierto = $state(false)

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

  function paginaDesdeHash() {
    const hash = window.location.hash.slice(1)
    pagina = hash === 'metodologia' || hash === 'glosario' || hash === 'acerca' ? hash : null
  }

  function abrirPagina(nombre: Pagina, evento?: MouseEvent) {
    if (evento?.currentTarget instanceof HTMLElement) enlaceQueAbrioPagina = evento.currentTarget
    mostrarAyuda = false
    menuAbierto = false
    window.location.hash = nombre
  }

  function cerrarPagina(restaurarFoco = false) {
    window.location.hash = ''
    if (restaurarFoco) requestAnimationFrame(() => enlaceQueAbrioPagina?.focus())
  }

  function manejarEscape(evento: KeyboardEvent) {
    if (evento.key !== 'Escape') return
    if (menuAbierto) {
      menuAbierto = false
      return
    }
    if (!pagina) return
    evento.preventDefault()
    cerrarPagina(true)
  }

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
    paginaDesdeHash()
    window.addEventListener('hashchange', paginaDesdeHash)
    window.addEventListener('keydown', manejarEscape)

    // Sincroniza el desplazamiento del planeta con el punto de quiebre del layout.
    const consulta = window.matchMedia('(min-width: 1000px)')
    escritorio = consulta.matches
    const actualizar = (evento: MediaQueryListEvent) => (escritorio = evento.matches)
    consulta.addEventListener('change', actualizar)
    return () => {
      consulta.removeEventListener('change', actualizar)
      window.removeEventListener('hashchange', paginaDesdeHash)
      window.removeEventListener('keydown', manejarEscape)
    }
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
    <span>{APP.marca}</span>
    <button class="menu-button" type="button" aria-label={menuAbierto ? NAVEGACION.cerrarMenu : NAVEGACION.menu} aria-expanded={menuAbierto} aria-controls="site-menu" onclick={() => (menuAbierto = !menuAbierto)}>
      <span></span><span></span><span></span>
    </button>
  </header>

  {#if menuAbierto}
    <div id="site-menu" class="site-menu" role="dialog" aria-label={NAVEGACION.menu}>
      <nav aria-label="Secciones del sitio">
        <a href="#metodologia" onclick={(evento) => abrirPagina('metodologia', evento)}>{NAVEGACION.metodologia}</a>
        <a href="#glosario" onclick={(evento) => abrirPagina('glosario', evento)}>{NAVEGACION.glosario}</a>
        <a href="#acerca" onclick={(evento) => abrirPagina('acerca', evento)}>{NAVEGACION.acerca}</a>
      </nav>
      <button class="about-button" type="button" aria-expanded={mostrarAyuda} aria-controls="about-panel" onclick={() => (mostrarAyuda = !mostrarAyuda)}>{NAVEGACION.comoLeer}</button>
      {#if mostrarAyuda}
        <div id="about-panel" class="about-panel" aria-labelledby="about-title">
          <h2 id="about-title">{APP.ayudaTitulo}</h2>
          <p>{APP.ayudaTexto}</p>
          <div class="help-links">{#each AYUDA_MAPA.enlaces as enlace}<a href={enlace.href} onclick={(evento) => abrirPagina(enlace.href.slice(1) as Pagina, evento)}>{enlace.texto}</a>{/each}</div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Columna del planeta: el globo vive detrás, aquí solo va la línea de tiempo. -->
  <div class="stage">
    <div class="legend-slot">
      <GlobeLegend anio={anio} mostrarAnio={anualesDisponibles} />
    </div>
    <div class="timeline-slot">
      {#if datos}
        <TimelineControl
           inicio={datos.periodo.inicio}
           fin={datos.periodo.fin}
           bind:anio
           disponible={anualesDisponibles}
            aviso={APP.avisoSinSerie}
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

</main>

{#if pagina}
  <div class="page-layer" role="dialog" aria-modal="true">
    {#if pagina === 'metodologia'}<Metodologia onCerrar={() => cerrarPagina()} />{:else if pagina === 'glosario'}<Glosario onCerrar={() => cerrarPagina()} />{:else}<AcercaDe onCerrar={() => cerrarPagina()} />{/if}
  </div>
{/if}

<style>
  /* La .interface global es pointer-events: none; los slots reactivan los
     eventos solo donde hay controles, para no bloquear la órbita del globo. */
  .interface {
    display: grid;
    grid-template-columns: 1fr minmax(340px, 430px);
    grid-template-rows: auto 1fr;
    grid-template-areas:
      'masthead masthead'
      'stage    rail';
    column-gap: 48px;
  }

  .masthead {
    grid-area: masthead;
    justify-content: space-between;
    pointer-events: auto;
  }

  .menu-button { display: grid; gap: 4px; width: 36px; height: 32px; padding: 8px 7px; margin-left: auto; border: 1px solid var(--hairline); background: transparent; }
  .menu-button span { display: block; width: 100%; height: 1px; background: var(--ink); }
  .site-menu { position: absolute; top: 76px; right: 42px; z-index: 4; width: min(300px, calc(100vw - 48px)); padding: 18px; border: 1px solid var(--hairline); background: rgba(16, 27, 44, .98); box-shadow: 0 18px 40px rgba(0,0,0,.3); pointer-events: auto; }
  .site-menu nav { display: grid; gap: 15px; font: 12px var(--mono); }
  .site-menu nav a { color: var(--ink); }
  .site-menu nav a:hover, .help-links a:hover { color: var(--amber); }
  .site-menu .about-button { margin-top: 20px; }
  .help-links { display: flex; gap: 16px; margin-top: 16px; font: 10px var(--mono); color: var(--amber); }
  .site-menu .about-panel { position: static; width: auto; margin: 18px 0 0; padding: 16px 0 0; border: 0; border-top: 1px solid var(--hairline); background: transparent; box-shadow: none; }

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

  .rail-slot,
  .timeline-slot {
    pointer-events: auto;
  }
  .timeline-slot { display: grid; gap: 10px; align-items: end; }
  .legend-slot { pointer-events: auto; }
  .page-layer { position: fixed; inset: 0; z-index: 20; overflow-y: auto; background: var(--bg); pointer-events: auto; }

  /* Columna única: panel debajo del masthead, línea de tiempo al final. */
  @media (max-width: 899px) {
    .interface {
      grid-template-columns: 1fr;
      grid-template-rows: auto minmax(260px, 1fr) auto;
      grid-template-areas:
        'masthead'
        'stage'
        'rail';
      column-gap: 0;
    }

    .stage {
      position: relative;
      justify-content: flex-end;
      padding: 18px 0 10px;
    }

    .rail {
      position: relative;
      z-index: 2;
      width: 100%;
    }

    .rail-slot {
      pointer-events: auto;
    }

    .site-menu { right: 24px; }
  }

  @media (max-width: 650px) {
    .site-menu { top: 64px; right: 17px; width: min(300px, calc(100vw - 34px)); }

    .stage {
      min-height: 285px;
      padding: 15px 0 8px;
    }

    /* Los controles quedan juntos en el borde inferior del espacio del globo,
       en vez de crecer entre el masthead y el panel de análisis. */
    .timeline-slot {
      position: absolute;
      right: 0;
      bottom: 2px;
      left: 0;
      width: min(100%, 360px);
      margin: 0 auto;
      gap: 6px;
    }

    .legend-slot {
      position: absolute;
      top: 8px;
      right: 0;
      left: 0;
      z-index: 1;
      display: flex;
      justify-content: center;
    }

    :global(.timeline-slot .timeline) {
      background: rgba(11, 18, 32, .48);
      border-color: rgba(237, 243, 250, .2);
      box-shadow: 0 -12px 30px rgba(5, 8, 15, .18);
    }
  }
</style>
