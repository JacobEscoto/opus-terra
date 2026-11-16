<script lang="ts">
  import { ACERCA, NAVEGACION } from "../../data/textos";
  import Fa from "svelte-fa";
  import { faGithub } from "@fortawesome/free-brands-svg-icons";
  import { faArrowLeft } from "@fortawesome/free-solid-svg-icons";
  interface PropiedadesComponente {
    onCerrar: () => void;
  }
  let { onCerrar }: PropiedadesComponente = $props();
</script>

<svelte:head><title>Acerca de — OpusTerra</title></svelte:head>

<article class="page">
  <div class="page__top">
    <button type="button" onclick={onCerrar}>
      <Fa icon={faArrowLeft} />
      <span>{NAVEGACION.volver}</span>
    </button>
  </div>
  
  <header class="page-header">
    <div class="header-content">
      <h1>{ACERCA.titulo}</h1>
      <div class="intro-block">
        {#each ACERCA.parrafos as parrafo}<p class="intro">{parrafo}</p>{/each}
      </div>
    </div>
  </header>

  <section>
    <h2>{ACERCA.fuentesTitulo}</h2>
    <div>
      <ul>
        {#each ACERCA.fuentes as fuente}<li>
            <a href={fuente.url} target="_blank" rel="noreferrer"
              >{fuente.texto}</a
            >
          </li>{/each}
      </ul>
      <p class="oni">
        <a href={ACERCA.fuenteOni.url} target="_blank" rel="noreferrer"
          >{ACERCA.fuenteOni.texto}</a
        >
      </p>
    </div>
  </section>

  <section>
    <h2>{ACERCA.integrantesTitulo}</h2>
    <ul class="integrantes">
      {#each ACERCA.integrantes as integrante}<li>{integrante}</li>{/each}
    </ul>
  </section>

  <div class="repository-wrapper">
    <a
      class="repository"
      href="https://github.com/JacobEscoto/opus-terra"
      rel="noreferrer"
      target="_blank"><Fa icon={faGithub} /></a
    >
  </div>
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
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: 0;
    border-bottom: 1px solid var(--amber);
    padding: 0 0 5px;
    background: transparent;
    font: 10px var(--mono);
    color: var(--ink);
    cursor: pointer;
  }
  
  /* Layout mejorado para el header y sus párrafos */
  .page-header {
    max-width: 720px;
    padding-bottom: 45px;
    border-bottom: 1px solid var(--hairline);
  }
  .header-content {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }
  h1 {
    font-size: clamp(2.4rem, 7vw, 5rem);
    font-weight: 350;
    letter-spacing: -0.07em;
    line-height: 0.95;
    margin: 0;
  }
  .intro-block {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .intro {
    max-width: 58ch;
    margin: 0;
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
    margin: 0;
    padding: 0;
    list-style: none;
  }
  li,
  section p {
    color: var(--muted);
    font-size: 13px;
    line-height: 1.7;
  }
  li + li {
    margin-top: 15px;
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
  .integrantes {
    columns: 2;
    column-gap: 30px;
  }
  .integrantes li {
    break-inside: avoid;
  }

  .repository-wrapper {
    margin-top: 30px;
  }

  .repository {
    display: inline-flex;
    align-items: center;
    font-size: 20px;
    text-decoration: none;
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
      gap: 10px;
    }
    .integrantes {
      columns: 1;
    }
  }
</style>
