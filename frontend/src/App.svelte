<script lang="ts">
  import { onMount } from 'svelte'
  import EarthGlobe from './lib/components/EarthGlobe.svelte'
  import AnalysisPanel from './lib/components/AnalysisPanel.svelte'
  import TimelineControl from './lib/components/TimelineControl.svelte'
  import { cargarAnalisis, type EstadoCarga } from './lib/data/loadAnalysis'

  // El JSON (por ahora mock.json) es la única fuente de datos de la UI.
  let carga = $state<EstadoCarga>({ estado: 'cargando' })

  /** Identificador del par elegido en la lista; null = vista de lista. */
  let idSeleccionado = $state<string | null>(null)

  /** Año activo en la línea de tiempo (aún no filtra la vista). */
  let anio = $state<number>(2023)
  let capaTendenciaVisible = $state(true)

  /**
   * En escritorio la columna del panel queda a la derecha: un offset negativo
   * desplaza el planeta hacia la izquierda dentro del canvas (prop existente
   * de EarthGlobe. En móvil
   * la columna es única y el planeta vuelve al centro.
   */
  let escritorio = $state(true)

  const desplazamiento = $derived(escritorio ? -0.17 : 0)

  // Par completo correspondiente al identificador elegido.
  const parSeleccionado = $derived(
    carga.estado === 'listo'
      ? carga.datos.pares.find((par) => par.id === idSeleccionado) ?? null
      : null
  )

  /** Lee el JSON de análisis y actualiza el estado global de la interfaz. */
  async function cargar() {
    carga = { estado: 'cargando' }
    idSeleccionado = null
    try {
      const datos = await cargarAnalisis()
      carga = { estado: 'listo', datos }
      anio = datos.periodo.fin
    } catch (error: unknown) {
      carga = {
        estado: 'error',
        mensaje:
          error instanceof Error
            ? error.message
            : 'No se pudieron leer los datos de análisis.',
      }
    }
  }

  onMount(() => {
    void cargar()

    // Sincroniza el desplazamiento del planeta con el punto de quiebre del layout.
    const consulta = window.matchMedia('(min-width: 1000px)')
    escritorio = consulta.matches
    const actualizar = (evento: MediaQueryListEvent) => (escritorio = evento.matches)
    consulta.addEventListener('change', actualizar)
    return () => consulta.removeEventListener('change', actualizar)
  })
</script>

<svelte:head>
  <title>OpusTerra by Pegaso-X</title>
  <meta
    name="description"
    content="OpusTerra by Pegaso-X — un globo terráqueo 3D interactivo."
  />
</svelte:head>

<!-- dataMode ilumina el planeta de forma pareja mientras un par está abierto;
     horizontalOffset lo corre a la izquierda para despejar la columna del panel. -->
  <EarthGlobe
    horizontalOffset={desplazamiento}
    dataMode={parSeleccionado !== null}
    celdas={carga.estado === 'listo' ? carga.datos.resultados_pixeles : []}
    capaVisible={capaTendenciaVisible}
  />

<div class="interface">
  <header class="masthead">
    <span>OpusTerra by Pegaso-X</span>
  </header>

  <!-- Columna del planeta: el globo vive detrás, aquí solo va la línea de tiempo. -->
  <div class="stage">
    <div class="timeline-slot">
      {#if carga.estado === 'listo'}
        <TimelineControl
          inicio={carga.datos.periodo.inicio}
          fin={carga.datos.periodo.fin}
          bind:anio
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
          capaVisible={capaTendenciaVisible}
          onAlternarCapa={() => (capaTendenciaVisible = !capaTendenciaVisible)}
        />
    </div>
  </aside>
</div>

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

  .rail-slot,
  .timeline-slot {
    pointer-events: auto;
  }

  /* Columna única: panel debajo del masthead, línea de tiempo al final. */
  @media (max-width: 899px) {
    .interface {
      grid-template-columns: 1fr;
      grid-template-rows: auto 1fr;
      grid-template-areas:
        'masthead'
        'stage';
      column-gap: 0;
    }

    .stage {
      justify-content: flex-end;
      padding-top: 18px;
    }

    .rail {
      position: fixed;
      right: max(17px, env(safe-area-inset-right));
      bottom: 0;
      left: max(17px, env(safe-area-inset-left));
      z-index: 2;
      pointer-events: none;
    }

    .rail-slot {
      pointer-events: auto;
    }
  }

  @media (max-width: 650px) {
    .stage {
      padding-top: 15px;
    }
  }
</style>
