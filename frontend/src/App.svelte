<script lang="ts">
  import { onMount } from "svelte";
  import EarthGlobe from "./lib/components/EarthGlobe.svelte";
  import type { EarthTelemetry } from "./lib/three/earthScene";

  let telemetry = $state<EarthTelemetry | null>(null);
  let isWide = $state(false);

  const formatCoordinate = (
    value: number,
    positive: string,
    negative: string,
  ) => `${Math.abs(value).toFixed(2)}° ${value >= 0 ? positive : negative}`;

  onMount(() => {
    const query = window.matchMedia("(min-width: 900px)");
    const apply = () => (isWide = query.matches);
    apply();
    query.addEventListener("change", apply);
    return () => query.removeEventListener("change", apply);
  });
</script>

<svelte:head>
  <title>OpusTerra by Pegaso-X</title>
  <meta
    name="description"
    content="Globo terráqueo 3D con datos satelitales de la NASA para encontrar dónde la Tierra cambia en direcciones opuestas."
  />
</svelte:head>

<EarthGlobe
  onTelemetry={(value) => (telemetry = value)}
  horizontalOffset={isWide ? 0.2 : 0}
/>

<div class="stage">
  <header class="topbar">
    <div class="mark">
      <svg class="mark__glyph" viewBox="0 0 32 32" aria-hidden="true">
        <circle cx="16" cy="16" r="7" />
        <ellipse
          cx="16"
          cy="16"
          rx="14"
          ry="5.5"
          transform="rotate(-28 16 16)"
        />
      </svg>
      <span class="mark__name">Trend Detective</span>
    </div>
    <p class="topbar__meta">NASA Space Apps Challenge · 2026</p>
  </header>

  <main class="hero">
    <div class="copy">
      <h1>La Tierra no cambia<br />igual en todas partes.</h1>
      <p class="deck">
        Buscamos las regiones donde los satélites de la NASA están midiendo
        cambios opuestos: aquí algo sube mientras allá baja. Después comprobamos
        si ese cambio es real o solo un vaivén normal del clima.
      </p>
      <p class="stage-note">
        <span class="dot" aria-hidden="true"></span>
        Mockup inicial — la capa visual está lista; los datos satelitales llegan
        en la siguiente iteración.
      </p>
    </div>
  </main>

  <footer class="rail">
    <div class="rail__cell">
      <span class="rail__label">Posición del cursor</span>
      <span class="rail__value">
        {#if telemetry}
          {formatCoordinate(telemetry.lat, "N", "S")}
          <span class="rail__sep">·</span>
          {formatCoordinate(telemetry.lon, "E", "O")}
        {:else}
          Apunta al globo
        {/if}
      </span>
    </div>

    <p class="rail__hint">Arrastra para girar · rueda para acercar</p>

    <div class="rail__cell rail__cell--source">
      <span class="rail__label">Modo actual</span>
      <span class="rail__value"
        >Visualización de referencia · sin datos en vivo</span
      >
    </div>
  </footer>
</div>

<style>
  .stage {
    position: relative;
    z-index: 1;
    min-height: 100svh;
    display: grid;
    grid-template-rows: auto 1fr auto;
    gap: clamp(1.5rem, 4vh, 3rem);
    padding: clamp(1.25rem, 3vw, 2.5rem) clamp(1.25rem, 4vw, 3.5rem);
    /* Let the planet underneath receive the drag gestures. */
    pointer-events: none;
  }

  .copy,
  .rail,
  .topbar {
    pointer-events: auto;
  }

  /* ---------- top bar ---------- */
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--rule);
  }

  .mark {
    display: flex;
    align-items: center;
    gap: 0.65rem;
  }

  .mark__glyph {
    width: 26px;
    height: 26px;
    fill: none;
    stroke: var(--ink);
    stroke-width: 1.25;
    opacity: 0.85;
  }

  .mark__name {
    font-family: var(--display);
    font-weight: 500;
    font-size: 1.02rem;
    letter-spacing: 0.01em;
  }

  .topbar__meta {
    font-family: var(--mono);
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    color: var(--ink-3);
    white-space: nowrap;
  }

  /* ---------- hero ---------- */
  .hero {
    display: grid;
    grid-template-columns: minmax(0, 46fr) minmax(0, 54fr);
    align-items: center;
  }

  .copy {
    max-width: 34rem;
    padding-block: 1rem;
  }

  h1 {
    font-family: var(--display);
    font-weight: 300;
    font-size: clamp(2.4rem, 5.2vw, 4.2rem);
    line-height: 1.04;
    letter-spacing: -0.025em;
    color: var(--ink);
    text-wrap: balance;
  }

  .deck {
    margin-top: 1.5rem;
    max-width: 46ch;
    font-size: clamp(0.95rem, 1.05vw, 1.06rem);
    line-height: 1.65;
    color: var(--ink-2);
  }

  .stage-note {
    margin-top: 2rem;
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    max-width: 42ch;
    font-family: var(--mono);
    font-size: 0.73rem;
    line-height: 1.7;
    letter-spacing: 0.01em;
    color: var(--ink-3);
  }

  .dot {
    flex: none;
    width: 6px;
    height: 6px;
    margin-top: 0.55em;
    border-radius: 50%;
    background: var(--ink);
    box-shadow: 0 0 0 3px rgba(243, 247, 252, 0.12);
  }

  /* ---------- bottom rail ---------- */
  .rail {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--rule);
  }

  .rail__cell {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 0;
  }

  .rail__cell--source {
    align-items: flex-end;
    text-align: right;
  }

  .rail__label {
    font-family: var(--mono);
    font-size: 0.63rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--ink-3);
  }

  .rail__value {
    font-family: var(--mono);
    font-size: 0.8rem;
    color: var(--ink-2);
    font-variant-numeric: tabular-nums;
  }

  .rail__sep {
    color: var(--ink-faint);
    padding-inline: 0.35em;
  }

  .rail__hint {
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    color: var(--ink-faint);
    white-space: nowrap;
  }

  @media (max-width: 900px) {
    .stage {
      gap: 1.25rem;
      padding: 1.25rem;
    }

    .hero {
      grid-template-columns: 1fr;
      align-items: start;
    }

    .copy {
      max-width: 38rem;
      padding-block: 0.5rem;
    }

    .rail {
      grid-template-columns: 1fr 1fr;
      row-gap: 1rem;
    }

    .rail__hint {
      grid-column: 1 / -1;
      grid-row: 2;
      text-align: center;
      white-space: normal;
    }
  }

  @media (max-width: 560px) {
    .stage {
      min-height: 100dvh;
      gap: 0.9rem;
      padding: max(1rem, env(safe-area-inset-top))
        max(1rem, env(safe-area-inset-right))
        max(1rem, env(safe-area-inset-bottom))
        max(1rem, env(safe-area-inset-left));
    }

    .topbar {
      padding-bottom: 0.75rem;
    }

    .mark {
      gap: 0.5rem;
    }

    .mark__glyph {
      width: 22px;
      height: 22px;
    }

    .mark__name {
      font-size: 0.92rem;
    }

    h1 {
      max-width: 15ch;
      font-size: clamp(2.15rem, 11vw, 3rem);
    }

    .deck {
      margin-top: 1rem;
      max-width: 34ch;
      font-size: 0.9rem;
      line-height: 1.5;
    }

    .stage-note {
      margin-top: 1.1rem;
      max-width: 35ch;
      font-size: 0.66rem;
      line-height: 1.55;
    }

    .topbar__meta {
      display: none;
    }

    .rail {
      gap: 0.75rem;
      padding-top: 0.75rem;
      grid-template-columns: 1fr;
    }

    .rail__label {
      font-size: 0.58rem;
    }

    .rail__value {
      font-size: 0.68rem;
      line-height: 1.45;
    }

    .rail__hint {
      order: 3;
      font-size: 0.64rem;
    }

    .rail__cell--source {
      align-items: flex-start;
      text-align: left;
    }
  }
</style>
