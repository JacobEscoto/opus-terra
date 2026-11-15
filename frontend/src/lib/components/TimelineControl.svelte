<script lang="ts">
  interface PropiedadesComponente {
    /** Primer año del periodo analizado (viene del contrato). */
    inicio: number
    /** Último año del periodo analizado (viene del contrato). */
    fin: number
  /** Año activo; enlazado con App y con la capa del globo. */
    anio: number
    /** El JSON de la variable trae valores por año y por celda. */
    disponible: boolean
    /** Aviso cuando no hay datos anuales que mostrar. */
    aviso?: string
  }

  let { inicio, fin, anio = $bindable(), disponible, aviso }: PropiedadesComponente = $props()
</script>

<!-- El control solo se activa cuando el JSON trae valores por año y por celda. -->
<div class="timeline">
  <div class="timeline__cabeza">
    <label class="timeline__etiqueta" for="timeline-anio">Línea de tiempo</label>
    <output class="timeline__anio" for="timeline-anio">Año {anio}</output>
  </div>
  <div class="timeline__fila">
    <span class="timeline__valor">{inicio}</span>
    <input
      id="timeline-anio"
      type="range"
      min={inicio}
      max={fin}
      step="1"
      bind:value={anio}
      disabled={!disponible}
      aria-label="Año seleccionado"
      aria-valuetext={`Año ${anio}`}
    />
    <span class="timeline__valor">{fin}</span>
  </div>
  {#if !disponible && aviso}
    <p class="timeline__aviso">{aviso}</p>
  {/if}
</div>

<style>
  .timeline {
    display: grid;
    gap: 8px;
    padding: 13px 16px 14px;
    border: 1px solid var(--hairline);
    background: var(--panel-bg);
    backdrop-filter: blur(10px);
    min-width: 260px;
  }

  .timeline__cabeza {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 14px;
  }

  .timeline__etiqueta {
    font: 10px var(--mono);
    letter-spacing: 0.08em;
    color: var(--faint);
  }

  .timeline__anio {
    font: 500 12px var(--mono);
    color: var(--amber);
  }

  .timeline__fila {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .timeline__valor {
    font: 10px var(--mono);
    color: var(--muted);
  }

  input[type='range'] {
    flex: 1;
    accent-color: var(--blue);
  }

  input[type='range']:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .timeline__aviso {
    margin: 0;
    font: 10px/1.5 var(--mono);
    color: var(--faint);
  }
</style>
