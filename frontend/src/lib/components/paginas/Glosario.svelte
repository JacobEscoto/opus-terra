<script lang="ts">
  import { APP, GLOSARIO, NAVEGACION } from '../../data/textos'
  interface PropiedadesComponente { onCerrar: () => void }
  let { onCerrar }: PropiedadesComponente = $props()
</script>

<svelte:head><title>Glosario — OpusTerra</title></svelte:head>

<article class="page">
  <div class="page__top"><button type="button" onclick={onCerrar}>{NAVEGACION.volver}</button></div>
  <header><p class="page__kicker">{APP.marca}</p><h1>{GLOSARIO.titulo}</h1><p class="page__intro">{GLOSARIO.introduccion}</p></header>
  <dl>{#each GLOSARIO.terminos as [termino, definicion]}<div><dt>{termino}</dt><dd>{definicion}</dd></div>{/each}</dl>
</article>

<style>
  .page { min-height: 100vh; width: min(820px, 100%); margin: 0 auto; padding: 28px 42px 64px; }
  .page__top { display: flex; justify-content: flex-end; margin-bottom: clamp(60px, 12vh, 130px); }
  .page__top button { border: 0; border-bottom: 1px solid var(--amber); padding: 0 0 5px; background: transparent; font: 10px var(--mono); color: var(--ink); }
  header { max-width: 680px; padding-bottom: 45px; border-bottom: 1px solid var(--hairline); }
  .page__kicker { margin-bottom: 17px; color: var(--amber); font: 10px var(--mono); }
  h1 { font-size: clamp(2.4rem, 7vw, 5rem); font-weight: 350; letter-spacing: -.07em; line-height: .95; }
  .page__intro { max-width: 52ch; margin-top: 24px; color: var(--muted); font-size: 15px; line-height: 1.65; }
  dl { margin: 0; }
  dl div { display: grid; grid-template-columns: minmax(160px, .7fr) 1.5fr; gap: 30px; padding: 27px 0; border-bottom: 1px solid var(--hairline); }
  dt { font-size: 16px; font-weight: 500; }
  dd { margin: 0; color: var(--muted); font-size: 13px; line-height: 1.7; }
  @media (max-width: 650px) { .page { padding: 18px 17px 48px; } .page__top { margin-bottom: 70px; } dl div { grid-template-columns: 1fr; gap: 10px; } }
</style>
