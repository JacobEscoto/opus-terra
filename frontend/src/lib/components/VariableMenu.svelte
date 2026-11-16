<script lang="ts">
  import type {
    RegionDisponible,
    VariableCatalogo,
  } from "../data/loadAnalysis";

  interface PropiedadesComponente {
    /** Variables disponibles en la región activa. */
    variables: VariableCatalogo[];
    /** Identificador de la variable activa. */
    activa: string;
    /** Variables cuyo JSON ya está en memoria. */
    cargadas: string[];
    /** Regiones con datos disponibles. */
    regiones: RegionDisponible[];
    /** Región de datos activa. */
    regionActiva: string;
    onCambiarVariable: (id: string) => void;
    onCambiarRegion: (id: string) => void;
  }

  let {
    variables,
    activa,
    cargadas,
    regiones,
    regionActiva,
    onCambiarVariable,
    onCambiarRegion,
  }: PropiedadesComponente = $props();

  let abierto = $state(false);
  let raiz = $state<HTMLDivElement | null>(null);
  let panel = $state<HTMLDivElement | null>(null);
  let disparador = $state<HTMLButtonElement | null>(null);

  const activaDatos = $derived(
    variables.find((variable) => variable.id === activa) ?? null,
  );

  function alternar() {
    abierto = !abierto;
  }

  function elegir(id: string) {
    onCambiarVariable(id);
    abierto = false;
    disparador?.focus();
  }

  function cerrar() {
    abierto = false;
  }

  function pulsarFuera(evento: MouseEvent) {
    if (!abierto) return;
    if (raiz?.contains(evento.target as Node)) return;
    cerrar();
  }

  function teclaGlobal(evento: KeyboardEvent) {
    if (evento.key !== "Escape" || !abierto) return;
    cerrar();
    disparador?.focus();
  }

  $effect(() => {
    if (abierto) panel?.focus();
  });
</script>

<svelte:window onclick={pulsarFuera} onkeydown={teclaGlobal} />

<div class="vm" bind:this={raiz}>
  <button
    type="button"
    class="vm__disparador"
    bind:this={disparador}
    aria-expanded={abierto}
    aria-controls="vm-panel"
    onclick={alternar}
  >
    <span class="vm__rotulo">Variable</span>
    <span class="vm__activa">{activaDatos?.etiqueta ?? "—"}</span>
    <span class="vm__chev" aria-hidden="true">{abierto ? "↑" : "↓"}</span>
  </button>

  {#if abierto}
    <div
      id="vm-panel"
      class="vm__panel"
      bind:this={panel}
      tabindex="-1"
      role="dialog"
      aria-label="Selector de variable y región de datos"
    >
      <div class="vm__grupo" role="group" aria-label="Variables disponibles">
        {#each variables as variable (variable.id)}
          <button
            type="button"
            class="vm__opcion"
            class:vm__opcion--activa={variable.id === activa}
            aria-pressed={variable.id === activa}
            onclick={() => elegir(variable.id)}
          >
            <span class="vm__nombre">{variable.etiqueta}</span>
            <span class="vm__meta">
              {#if !cargadas.includes(variable.id)}
                <span class="vm__descarga" title="Su datos se leerán al elegirla"
                  >↓</span
                >
              {/if}
              {#if variable.id === activa}
                <span class="vm__check" aria-hidden="true">✓</span>
              {/if}
            </span>
          </button>
        {/each}
      </div>

      <label class="vm__region">
        <span>Región de datos</span>
        <select
          value={regionActiva}
          onchange={(evento) => onCambiarRegion(evento.currentTarget.value)}
        >
          {#each regiones as region (region.id)}
            <option value={region.id}>{region.nombre}</option>
          {/each}
        </select>
      </label>

      <p class="vm__pista">
        Consejo: pulsa el territorio de un país en el globo para ver si tiene
        datos y cambiar de región.
      </p>
    </div>
  {/if}
</div>

<style>
  .vm {
    position: relative;
    width: 100%;
    pointer-events: auto;
  }

  .vm__disparador {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--muted);
    background: var(--panel-bg);
    backdrop-filter: blur(10px);
    color: var(--ink);
    text-align: left;
  }

  .vm__disparador:hover,
  .vm__disparador:focus-visible {
    border-color: var(--amber);
  }

  .vm__rotulo {
    font: 9px var(--mono);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--faint);
  }

  .vm__activa {
    overflow: hidden;
    font: 500 12px var(--mono);
    color: var(--ink);
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .vm__chev {
    color: var(--amber);
    font-size: 11px;
  }

  .vm__panel {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    z-index: 5;
    width: min(320px, calc(100vw - 34px));
    padding: 8px;
    border: 1px solid var(--hairline);
    background: rgba(13, 20, 34, 0.97);
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35);
  }

  .vm__panel:focus {
    outline: none;
  }

  .vm__grupo {
    display: grid;
  }

  .vm__opcion {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 11px;
    border-bottom: 1px solid var(--hairline);
    background: transparent;
    color: var(--muted);
    text-align: left;
  }

  .vm__opcion:last-child {
    border-bottom: 0;
  }

  .vm__opcion:hover,
  .vm__opcion:focus-visible {
    background: rgba(120, 185, 255, 0.06);
    color: var(--ink);
  }

  .vm__opcion--activa {
    color: var(--amber);
  }

  .vm__opcion--activa .vm__nombre {
    font-weight: 500;
  }

  .vm__meta {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font: 10px var(--mono);
  }

  .vm__descarga {
    color: var(--faint);
  }

  .vm__check {
    color: var(--amber);
  }

  .vm__region {
    display: grid;
    gap: 6px;
    padding: 12px 11px 6px;
    border-top: 1px solid var(--hairline);
  }

  .vm__region span {
    font: 9px var(--mono);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--faint);
  }

  .vm__region select {
    padding: 8px 10px;
    border: 1px solid var(--muted);
    background: var(--bg);
    font: 11px var(--mono);
    color: var(--ink);
  }

  .vm__region select:focus-visible {
    outline: 2px solid var(--amber);
    outline-offset: 3px;
  }

  .vm__pista {
    margin: 10px 11px 4px;
    font: 9px/1.55 var(--mono);
    color: var(--faint);
  }
</style>
