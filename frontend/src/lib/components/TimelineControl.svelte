<script lang="ts">
  interface Props {
    /** Primer año del periodo analizado (viene del contrato). */
    inicio: number
    /** Último año del periodo analizado (viene del contrato). */
    fin: number
    /** Año activo; enlazado con App. Por ahora solo se muestra. */
    anio: number
  }

  let { inicio, fin, anio = $bindable() }: Props = $props()
</script>

<!-- Control de línea de tiempo: preparado para filtrar la vista del globo.
     Hoy solo muestra el año seleccionado; el resto de la UI puede usar
     `anio` cuando existan datos por año. -->
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
      aria-label="Año seleccionado"
      aria-valuetext={`Año ${anio}`}
    />
    <span class="timeline__valor">{fin}</span>
  </div>
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
</style>
