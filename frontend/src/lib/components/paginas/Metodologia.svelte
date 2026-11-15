<script lang="ts">
  import { APP, METODOLOGIA, NAVEGACION } from '../../data/textos'
  interface Props { onCerrar: () => void }
  let { onCerrar }: Props = $props()
</script>
<article class="page">
  <div class="page__top"><button type="button" onclick={onCerrar}>{NAVEGACION.volver}</button></div>
  <header><p class="page__kicker">{APP.marca}</p><h1>{METODOLOGIA.titulo}</h1><p class="page__intro">{METODOLOGIA.introduccion}</p></header>
  <div class="page__sections">
    {#each METODOLOGIA.secciones as seccion}<section><h2>{seccion.titulo}</h2>{#each seccion.parrafos as parrafo}<p>{parrafo}</p>{/each}</section>{/each}
  </div>
</article>

<style>
  .page { width: min(820px, 100%); margin: 0 auto; padding: 28px 42px 64px; }
  .page__top { display: flex; justify-content: flex-end; margin-bottom: clamp(60px, 12vh, 130px); }
  .page__top button { border-bottom: 1px solid var(--amber); padding: 0 0 5px; background: transparent; font: 10px var(--mono); color: var(--ink); }
  header { max-width: 680px; padding-bottom: 48px; border-bottom: 1px solid var(--hairline); }
  .page__kicker { margin-bottom: 17px; color: var(--amber); font: 10px var(--mono); letter-spacing: .08em; }
  h1 { font-size: clamp(2.4rem, 7vw, 5rem); font-weight: 350; letter-spacing: -.07em; line-height: .95; }
  .page__intro { max-width: 50ch; margin-top: 25px; color: var(--muted); font-size: 15px; line-height: 1.65; }
  .page__sections { display: grid; gap: 0; }
  section { display: grid; grid-template-columns: minmax(150px, .7fr) 1.5fr; gap: 30px; padding: 27px 0; border-bottom: 1px solid var(--hairline); }
  h2 { font-size: 16px; font-weight: 500; line-height: 1.3; }
  section p { color: var(--muted); font-size: 13px; line-height: 1.7; }
  section p + p { margin-top: 13px; }
  @media (max-width: 650px) { .page { padding: 18px 17px 48px; } .page__top { margin-bottom: 70px; } section { grid-template-columns: 1fr; gap: 11px; } }
</style>
