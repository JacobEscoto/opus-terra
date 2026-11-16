<script lang="ts">
  import { ACERCA, NAVEGACION } from "../../data/textos";

  interface PropiedadesComponente {
    onCerrar: () => void;
  }

  let { onCerrar }: PropiedadesComponente = $props();
</script>

<svelte:head><title>Fuentes de datos — OpusTerra</title></svelte:head>

<article class="page">
  <div class="page__top">
    <button type="button" onclick={onCerrar}>{NAVEGACION.volver}</button>
  </div>

  <header>
    <p class="page__kicker">OpusTerra</p>
    <h1>{NAVEGACION.fuentes}</h1>
    <p class="intro">
      Los productos públicos usados en los análisis, con su versión y su
      identificador.
    </p>
  </header>

  <section>
    <h2>Productos</h2>
    <ul>
      {#each ACERCA.fuentes as fuente (fuente.url)}
        <li>
          <a href={fuente.url} target="_blank" rel="noreferrer"
            >{fuente.texto}</a
          >
        </li>
      {/each}
      <li>
        <a href={ACERCA.fuenteOni.url} target="_blank" rel="noreferrer"
          >{ACERCA.fuenteOni.texto}</a
        >
      </li>
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
  ul {
    display: grid;
    gap: 15px;
    margin: 0;
    padding: 0;
    list-style: none;
  }
  li {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.7;
  }
  a {
    color: var(--ink);
    text-decoration-line: underline;
    text-decoration-style: dotted;
    text-decoration-color: var(--amber);
    text-underline-offset: 4px;
  }
  a:hover,
  a:focus-visible {
    color: var(--amber);
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
