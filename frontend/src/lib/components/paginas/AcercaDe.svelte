<script lang="ts">
  import { ACERCA, APP, NAVEGACION } from '../../data/textos'
  interface PropiedadesComponente { onCerrar: () => void }
  let { onCerrar }: PropiedadesComponente = $props()
</script>

<svelte:head><title>Acerca de — OpusTerra</title></svelte:head>

<article class="page">
  <div class="page__top"><button type="button" onclick={onCerrar}>{NAVEGACION.volver}</button></div>
  <header><p class="page__kicker">{APP.marca}</p><h1>{ACERCA.titulo}</h1>{#each ACERCA.parrafos as parrafo}<p class="intro">{parrafo}</p>{/each}</header>
  <section><h2>{ACERCA.fuentesTitulo}</h2><div><ul>{#each ACERCA.fuentes as fuente}<li><a href={fuente.url} target="_blank" rel="noreferrer">{fuente.texto}</a></li>{/each}</ul><p class="oni"><a href={ACERCA.fuenteOni.url} target="_blank" rel="noreferrer">{ACERCA.fuenteOni.texto}</a></p></div></section>
  <section><h2>{ACERCA.integrantesTitulo}</h2><ul class="integrantes">{#each ACERCA.integrantes as integrante}<li>{integrante}</li>{/each}</ul></section>
  <p class="license"><a href={ACERCA.licencia.url} target="_blank" rel="noreferrer">{ACERCA.licencia.texto}</a></p>
</article>

<style>
  .page { min-height: 100vh; width: min(820px, 100%); margin: 0 auto; padding: 28px 42px 64px; }
  .page__top { display: flex; justify-content: flex-end; margin-bottom: clamp(60px, 12vh, 130px); }
  .page__top button { border: 0; border-bottom: 1px solid var(--amber); padding: 0 0 5px; background: transparent; font: 10px var(--mono); color: var(--ink); }
  header { max-width: 680px; padding-bottom: 45px; border-bottom: 1px solid var(--hairline); }
  .page__kicker { margin-bottom: 17px; color: var(--amber); font: 10px var(--mono); }
  h1 { font-size: clamp(2.4rem, 7vw, 5rem); font-weight: 350; letter-spacing: -.07em; line-height: .95; }
  .intro { max-width: 52ch; margin-top: 24px; color: var(--muted); font-size: 15px; line-height: 1.65; }
  section { display: grid; grid-template-columns: minmax(160px, .7fr) 1.5fr; gap: 30px; padding: 27px 0; border-bottom: 1px solid var(--hairline); }
  h2 { font-size: 16px; font-weight: 500; }
  ul { margin: 0; padding: 0; list-style: none; }
  li, section p { color: var(--muted); font-size: 13px; line-height: 1.7; }
  li + li { margin-top: 15px; }
  a { color: var(--ink); text-decoration-line: underline; text-decoration-style: dotted; text-decoration-color: var(--amber); text-underline-offset: 4px; }
  a:hover, a:focus-visible { color: var(--amber); }
  .integrantes { columns: 2; column-gap: 30px; }
  .integrantes li { break-inside: avoid; }
  .license { margin-top: 28px; color: var(--faint); font: 10px var(--mono); }
  @media (max-width: 650px) { .page { padding: 18px 17px 48px; } .page__top { margin-bottom: 70px; } section { grid-template-columns: 1fr; gap: 10px; } .integrantes { columns: 1; } }
</style>
