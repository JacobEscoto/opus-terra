<script lang="ts">
  import type { EstadoCarga } from '../data/loadAnalysis'
  import type { AnalisisTendencias, ParRegiones } from '../types/analysis'
  import Legend from './Legend.svelte'
  import PairList from './PairList.svelte'
  import RegionCard from './RegionCard.svelte'

  interface Props {
    /** Estado de la lectura del JSON (cargando / error / listo). */
    carga: EstadoCarga
    /** Par elegido actualmente, o null para la vista de lista. */
    parSeleccionado: ParRegiones | null
    onSeleccionar: (id: string) => void
    onVolver: () => void
    onReintentar: () => void
    capaVisible: boolean
    onAlternarCapa: () => void
  }

  let {
    carga,
    parSeleccionado,
    onSeleccionar,
    onVolver,
    onReintentar,
    capaVisible,
    onAlternarCapa,
  }: Props = $props()

  let panelExpandido = $state(false)

  const datos = $derived(carga.estado === 'listo' ? carga.datos : null)
  const conjuntos = $derived(datos?.analisis ?? (datos ? [datos] : []))

  function esPromedioDeArea(conjunto: AnalisisTendencias): boolean {
    return conjunto.pixeles_probados === 0 && conjunto.limitacion?.includes('area-promedio') === true
  }

  function celdasSignificativas(conjunto: AnalisisTendencias) {
    return conjunto.resultados_pixeles.filter((pixel) => pixel.significativa_fdr)
  }
</script>

<section class="panel" class:panel--expandido={panelExpandido} aria-label="Análisis de tendencias por pares de regiones">
  <header class="panel__head">
    <div class="panel__fila">
      <p class="kicker"><span>02</span>Análisis de tendencias</p>
    {#if datos}
        <span class="panel__mock" title="Datos procesados del backend">
          Datos procesados / Honduras
        </span>
      {/if}
    </div>
    <h2>{datos?.nombre_variable ?? '—'}</h2>
    {#if datos}
      <p class="panel__meta">
        {datos.variable}<span class="slash">/</span>{datos.unidad}<span class="slash">/</span>{datos.periodo.inicio}–{datos.periodo.fin}
      </p>    {/if}
    <button
      type="button"
      class="panel__toggle"
      aria-expanded={panelExpandido}
      onclick={() => (panelExpandido = !panelExpandido)}
    >
      <span>{panelExpandido ? 'Cerrar panel' : 'Abrir panel'}</span>
      <span aria-hidden="true">{panelExpandido ? '↓' : '↑'}</span>
    </button>
  </header>

  <div class="panel__contenido">
  {#if carga.estado === 'cargando'}
    <div class="estado" role="status" aria-live="polite">
      <p>Leyendo datos de análisis…</p>
      <div class="estado__barra"><span></span></div>
    </div>
  {:else if carga.estado === 'error'}
    <div class="estado estado--error" role="alert">
      <p>{carga.mensaje}</p>
      <button type="button" class="estado__reintentar" onclick={onReintentar}>Reintentar</button>
    </div>
  {:else if datos && parSeleccionado}
    <div class="detalle">
      <button type="button" class="panel__volver" onclick={onVolver}>← Volver a la lista</button>
      <p class="detalle__intro">
        Dos regiones del mismo par, con su tendencia y su marca de significancia.
      </p>
      <div class="detalle__regiones">
        <RegionCard
          region={parSeleccionado.region_a}
          etiqueta="Región A"
          unidad={datos.unidad}
          contextoOms={datos.contexto_oms}
        />
        <RegionCard
          region={parSeleccionado.region_b}
          etiqueta="Región B"
          unidad={datos.unidad}
          contextoOms={datos.contexto_oms}
        />
      </div>
    </div>
  {:else if datos}
    <div class="panel__cuerpo">
      <div class="capa-control">
        <div>
          <strong class="capa-control__titulo">Marcadores T2M</strong>
          <p class="capa-control__texto">
            Tendencia de temperatura 1996–2026 (MERRA-2), ajustada por ENSO. Celdas con tendencia significativa tras corrección FDR. Sin pares de contraste.
          </p>
        </div>
        <button type="button" class="capa-control__boton" onclick={onAlternarCapa} aria-pressed={capaVisible}>
          {capaVisible ? 'Ocultar' : 'Mostrar'}
        </button>
      </div>
      <Legend />
      {#each conjuntos as conjunto (conjunto.variable)}
        <article class="conjunto" aria-labelledby={`titulo-${conjunto.variable}`}>
          <div class="conjunto__cabecera">
            <div>
              <p class="conjunto__fuente">{conjunto.fuente}</p>
              <h3 id={`titulo-${conjunto.variable}`}>{conjunto.nombre_variable}</h3>
            </div>
            <span class="conjunto__periodo">{conjunto.periodo.inicio}–{conjunto.periodo.fin}</span>
          </div>

          {#if esPromedioDeArea(conjunto)}
            <div class="estado-datos estado-datos--area">
              <strong>Promedio de área: no hay análisis por píxel</strong>
              <p>{conjunto.pixeles_probados} píxeles probados · {conjunto.pixeles_significativos_fdr} significativos</p>
            </div>
          {:else if conjunto.pares.length === 0}
            <div class="estado-datos">
              <strong>Sin pares de tendencias opuestas significativas</strong>
              <p>{conjunto.pixeles_probados} píxeles probados · {conjunto.pixeles_significativos_fdr} significativos tras FDR</p>
            </div>
          {:else}
            <PairList
              pares={conjunto.pares}
              seleccionadoId={parSeleccionado?.id ?? null}
              onSeleccionar={onSeleccionar}
            />
          {/if}

          {#if conjunto.fuente.includes('MERRA-2')}
            <p class="resolucion">Resolución MERRA-2: cada celda representa aproximadamente 0.5° × 0.625°.</p>
          {/if}

          {#if conjunto.variable === 'merra2_t2m'}
            <div class="celdas" aria-label="Celdas T2M significativas">
              <h4>Celdas significativas</h4>
              {#each celdasSignificativas(conjunto) as pixel}
                <div class="celda">
                  <span>{pixel.lat.toFixed(2)}°, {pixel.lon.toFixed(2)}°</span>
                  <span class={pixel.sen_unidad_por_anio > 0 ? 'celda--positiva' : pixel.sen_unidad_por_anio < 0 ? 'celda--negativa' : ''}>
                    {pixel.sen_unidad_por_anio > 0 ? '+' : '−'}{Math.abs(pixel.sen_unidad_por_anio).toFixed(5)} °C/año
                  </span>
                </div>
              {/each}
            </div>
          {/if}
        </article>
      {/each}
    </div>
  {/if}
  </div>
</section>

<style>
  .panel {
    position: relative;
    padding: 18px 20px 20px;
    border: 1px solid var(--hairline);
    background: var(--panel-bg);
    backdrop-filter: blur(10px);
    max-height: calc(100svh - 145px);
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: var(--hairline) transparent;
  }

  .panel__contenido {
    min-height: 0;
  }

  .panel__toggle {
    display: none;
  }

  /* Esquinas de mira, como en un instrumento óptico: ámbar arriba a la
     izquierda, hairline abajo a la derecha. */
  .panel::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    width: 16px;
    height: 16px;
    border-top: 1px solid var(--amber);
    border-left: 1px solid var(--amber);
  }

  .panel::after {
    content: '';
    position: absolute;
    bottom: -1px;
    right: -1px;
    width: 16px;
    height: 16px;
    border-bottom: 1px solid var(--hairline);
    border-right: 1px solid var(--hairline);
  }

  .panel::-webkit-scrollbar {
    width: 8px;
  }

  .panel::-webkit-scrollbar-thumb {
    background: var(--hairline);
  }

  .panel__head {
    padding-bottom: 16px;
    border-bottom: 1px solid var(--hairline);
  }

  .panel__fila {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 12px;
  }

  .panel__head h2 {
    margin-top: 12px;
    font-size: 19px;
    font-weight: 500;
    letter-spacing: -0.03em;
  }

  .panel__mock {
    flex: none;
    padding: 3px 8px;
    border: 1px dashed var(--amber);
    font: 9px/1.4 var(--mono);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--amber);
  }

  .panel__meta {
    margin-top: 7px;
    font: 10px var(--mono);
    color: var(--faint);
  }

  .panel__cuerpo {
    display: grid;
    gap: 16px;
    padding-top: 15px;
  }

  .conjunto {
    display: grid;
    gap: 10px;
    padding-top: 15px;
    border-top: 1px solid var(--hairline);
  }

  .capa-control {
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 12px;
    align-items: start;
    padding: 11px 12px;
    border: 1px solid var(--hairline);
    background: rgb(255 255 255 / 3%);
  }

  .capa-control__titulo {
    display: block;
    font-size: 12px;
    font-weight: 500;
  }

  .capa-control__texto {
    margin: 5px 0 0;
    font: 10px/1.5 var(--mono);
    color: var(--faint);
  }

  .capa-control__boton {
    padding: 6px 9px;
    border: 1px solid var(--muted);
    background: transparent;
    font: 10px var(--mono);
    color: var(--ink);
    white-space: nowrap;
  }

  .capa-control__boton:hover,
  .capa-control__boton:focus-visible {
    border-color: var(--amber);
    color: var(--amber);
  }

  .conjunto__cabecera {
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }

  .conjunto__fuente,
  .conjunto__periodo,
  .resolucion,
  .celda,
  .estado-datos p {
    font: 10px/1.5 var(--mono);
    color: var(--faint);
  }

  .conjunto h3 {
    margin-top: 3px;
    font-size: 14px;
    font-weight: 500;
  }

  .conjunto__periodo {
    white-space: nowrap;
  }

  .estado-datos {
    display: grid;
    gap: 4px;
    padding: 11px 12px;
    border-left: 2px solid var(--amber);
    background: rgb(255 255 255 / 3%);
  }

  .estado-datos strong {
    font-size: 12px;
    font-weight: 500;
  }

  .estado-datos p {
    margin: 0;
  }

  .estado-datos--area {
    border-left-color: var(--muted);
  }

  .resolucion {
    margin: 0;
  }

  .celdas {
    display: grid;
    gap: 5px;
  }

  .celdas h4 {
    margin: 0 0 3px;
    font-size: 11px;
    font-weight: 500;
  }

  .celda {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 5px 0;
    border-bottom: 1px solid rgb(255 255 255 / 8%);
  }

  .celda--positiva {
    color: var(--amber);
  }

  .celda--negativa {
    color: var(--ink);
  }

  .detalle {
    display: grid;
    gap: 12px;
    padding-top: 15px;
  }

  .panel__volver {
    justify-self: start;
    padding: 6px 0 5px;
    border-bottom: 1px solid var(--muted);
    background: transparent;
    font: 10px var(--mono);
    color: var(--ink);
  }

  .detalle__intro {
    font: 10px/1.6 var(--mono);
    color: var(--faint);
  }

  /* Regiones lado a lado; en pantallas angostas se apilan. */
  .detalle__regiones {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .estado {
    display: grid;
    justify-items: center;
    gap: 12px;
    padding: 34px 10px;
    font: 11px var(--mono);
    color: var(--muted);
    text-align: center;
  }

  .estado--error {
    color: var(--ink);
  }

  .estado__barra {
    width: 150px;
    height: 1px;
    background: var(--hairline);
    overflow: hidden;
  }

  .estado__barra span {
    display: block;
    width: 40%;
    height: 100%;
    background: var(--amber);
    animation: barrido 1.4s cubic-bezier(0.65, 0, 0.35, 1) infinite;
  }

  .estado__reintentar {
    padding: 7px 14px;
    border: 1px solid var(--muted);
    background: transparent;
    font: 10px var(--mono);
    color: var(--ink);
  }

  .estado__reintentar:hover {
    border-color: var(--amber);
    color: var(--amber);
  }

  @keyframes barrido {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(250%);
    }
  }

  @media (max-width: 899px) {
    .panel {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-height: min(50dvh, 430px);
      padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
      overflow: hidden;
    }

    .panel:not(.panel--expandido) .panel__contenido {
      display: none;
    }

    .panel--expandido .panel__contenido {
      overflow-y: auto;
      overscroll-behavior: contain;
      scrollbar-width: thin;
      scrollbar-color: var(--hairline) transparent;
    }

    .panel__head {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 12px;
      padding-bottom: 0;
      border-bottom: 0;
    }

    .panel__fila,
    .panel__meta {
      display: none;
    }

    .panel__head h2 {
      min-width: 0;
      margin-top: 0;
      overflow: hidden;
      font-size: 15px;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .panel__toggle {
      display: inline-flex;
      align-items: center;
      justify-content: space-between;
      gap: 9px;
      min-width: 122px;
      min-height: 44px;
      padding: 8px 10px;
      border: 1px solid var(--muted);
      background: transparent;
      font: 10px var(--mono);
      color: var(--ink);
    }

    .panel__toggle:hover,
    .panel__toggle:focus-visible {
      border-color: var(--amber);
      color: var(--amber);
    }

    .panel :global(button) {
      min-height: 44px;
    }

    .capa-control__boton {
      min-width: 84px;
    }
  }

  @media (max-width: 650px) {
    .panel {
      padding: 15px 16px calc(17px + env(safe-area-inset-bottom));
    }

    .detalle__regiones {
      grid-template-columns: 1fr;
    }
  }
</style>
