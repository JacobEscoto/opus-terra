<script lang="ts">
  import type { VariableCatalogo } from '../data/loadAnalysis'

  interface Props {
    /** Variables disponibles en el catálogo. */
    variables: VariableCatalogo[]
    /** Identificador de la variable activa. */
    activa: string
    /** Variables whose JSON is already loaded (cached). */
    cargadas?: string[]
    onCambiar: (id: string) => void
  }

  let { variables, activa, cargadas = [], onCambiar }: Props = $props()
</script>

<!-- Selector de variables: cada botón pide el JSON de su variable y la usa
     como fuente del panel y de la capa del globo. -->
<div class="selector" role="group" aria-label="Selector de variable">
  {#each variables as variable (variable.id)}
    <button
      type="button"
      class="selector__boton"
      class:selector__boton--activo={variable.id === activa}
      aria-pressed={variable.id === activa}
      onclick={() => onCambiar(variable.id)}
    >
      <span class="selector__etiqueta">{variable.etiqueta}</span>
      {#if !cargadas.includes(variable.id)}
        <span class="selector__estado" title="Su JSON se leerá al seleccionarla">↓</span>
      {/if}
    </button>
  {/each}
</div>

<style>
  .selector {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding-bottom: 13px;
    border-bottom: 1px solid var(--hairline);
  }

  .selector__boton {
    display: inline-flex;
    align-items: baseline;
    gap: 5px;
    padding: 7px 10px;
    border: 1px solid var(--muted);
    background: transparent;
    font: 10px var(--mono);
    color: var(--muted);
    white-space: nowrap;
  }

  .selector__boton:hover,
  .selector__boton:focus-visible {
    border-color: var(--amber);
    color: var(--ink);
  }

  .selector__boton--activo {
    border-color: var(--amber);
    color: var(--amber);
  }

  .selector__estado {
    color: var(--faint);
  }

  @media (max-width: 899px) {
    .selector {
      padding-bottom: 10px;
    }

    .selector :global(button) {
      min-height: 40px;
    }
  }
</style>
