<script lang="ts">
  interface PropiedadesComponente {
    /** Nombre del territorio pulsado. */
    nombre: string;
    /** Nombre de la región de datos que lo cubre, o null si no hay. */
    regionNombre: string | null;
    onCerrar: () => void;
  }

  let { nombre, regionNombre, onCerrar }: PropiedadesComponente = $props();
</script>

<div class="pais-chip" role="status" aria-live="polite">
  <span class="pais-chip__punto" aria-hidden="true"></span>
  <div class="pais-chip__texto">
    <strong>{nombre}</strong>
    <span>
      {#if regionNombre}
        Datos disponibles en {regionNombre}
      {:else}
        Sin datos ambientales para este territorio
      {/if}
    </span>
  </div>
  <button
    type="button"
    class="pais-chip__cerrar"
    onclick={onCerrar}
    aria-label="Quitar la selección de {nombre}"
  >
    ✕
  </button>
</div>

<style>
  .pais-chip {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 9px 11px;
    border: 1px solid var(--amber);
    background: rgba(13, 20, 34, 0.9);
    backdrop-filter: blur(10px);
    pointer-events: auto;
  }

  .pais-chip__punto {
    flex: none;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--amber);
    box-shadow: 0 0 10px rgba(255, 181, 107, 0.65);
  }

  .pais-chip__texto {
    display: grid;
    gap: 2px;
    min-width: 0;
    flex: 1;
  }

  .pais-chip__texto strong {
    font-size: 13px;
    font-weight: 500;
    color: var(--ink);
  }

  .pais-chip__texto span {
    font: 9px/1.4 var(--mono);
    color: var(--muted);
  }

  .pais-chip__cerrar {
    flex: none;
    padding: 6px 8px;
    border: 1px solid var(--hairline);
    background: transparent;
    color: var(--muted);
    font: 11px var(--mono);
  }

  .pais-chip__cerrar:hover,
  .pais-chip__cerrar:focus-visible {
    border-color: var(--amber);
    color: var(--amber);
  }
</style>
