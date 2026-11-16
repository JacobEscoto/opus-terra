<script lang="ts">
  import { METODOLOGIA } from "../../data/textos";
  import { NAVEGACION } from "../../data/textos";

  interface PropiedadesComponente {
    onCerrar: () => void;
  }

  let { onCerrar }: PropiedadesComponente = $props();
</script>

<svelte:head><title>Metodología — OpusTerra</title></svelte:head>

<article class="page">
  <div class="page__top">
    <button type="button" onclick={onCerrar}>{NAVEGACION.volver}</button>
  </div>

  <header>
    <p class="page__kicker">OpusTerra</p>
    <h1>{METODOLOGIA.titulo}</h1>
    <p class="intro">{METODOLOGIA.introduccion}</p>
  </header>

  <section>
    <h2>Pasos del análisis</h2>
    <ol class="pasos">
      {#each METODOLOGIA.secciones as [titulo, texto] (titulo)}
        <li>
          <strong>{titulo}</strong>
          <span>{texto}</span>
        </li>
      {/each}
    </ol>
  </section>

  <section>
    <h2>{METODOLOGIA.limitacionesTitulo}</h2>
    <ul class="limitaciones">
      {#each METODOLOGIA.limitaciones as limitacion (limitacion)}
        <li>{limitacion}</li>
      {/each}
    </ul>
  </section>
</article>

<style>
  .page {
    min-height: 100vh;
    width: min(820px, 100%);
    margin: 0 auto;
    padding: 28px 42px 64px;
  }
  .page__top {
    display: flex;
    justify-content: flex-end;
    margin-bottom: clamp(60px, 12vh, 130px);
  }
  .page__top button {
    border: 0;
    border-bottom: 1px solid var(--amber);
    padding: 0 0 5px;
    background: transparent;
    font: 10px var(--mono);
    color: var(--ink);
  }
  header {
    max-width: 680px;
    padding-bottom: 45px;
    border-bottom: 1px solid var(--hairline);
  }
  .page__kicker {
    margin-bottom: 17px;
    color: var(--amber);
    font: 10px var(--mono);
  }
  h1 {
    font-size: clamp(2.4rem, 7vw, 5rem);
    font-weight: 350;
    letter-spacing: -0.07em;
    line-height: 0.95;
  }
  .intro {
    max-width: 52ch;
    margin-top: 24px;
    color: var(--muted);
    font-size: 15px;
    line-height: 1.65;
  }
  section {
    display: grid;
    grid-template-columns: minmax(160px, 0.7fr) 1.5fr;
    gap: 30px;
    padding: 27px 0;
    border-bottom: 1px solid var(--hairline);
  }
  h2 {
    font-size: 16px;
    font-weight: 500;
  }
  .pasos {
    display: grid;
    gap: 15px;
    margin: 0;
    padding: 0;
    list-style: none;
    counter-reset: paso;
  }
  .pasos li {
    display: grid;
    gap: 4px;
    padding-left: 26px;
    position: relative;
    color: var(--muted);
    font-size: 13px;
    line-height: 1.7;
  }
  .pasos li::before {
    counter-increment: paso;
    content: counter(paso, decimal-leading-zero);
    position: absolute;
    left: 0;
    top: 2px;
    font: 10px var(--mono);
    color: var(--amber);
  }
  .pasos strong {
    color: var(--ink);
    font-size: 13px;
    font-weight: 500;
  }
  .limitaciones {
    display: grid;
    gap: 12px;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .limitaciones li {
    padding-left: 16px;
    border-left: 2px solid var(--amber);
    color: var(--muted);
    font-size: 13px;
    line-height: 1.7;
  }
  @media (max-width: 650px) {
    .page {
      padding: 18px 17px 48px;
    }
    .page__top {
      margin-bottom: 70px;
    }
    section {
      grid-template-columns: 1fr;
      gap: 12px;
    }
  }
</style>
