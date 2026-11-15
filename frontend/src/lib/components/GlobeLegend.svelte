<script lang="ts">
  import { LEYENDA } from '../data/textos'

  interface Props { anio?: number; mostrarAnio?: boolean }
  let { anio, mostrarAnio = false }: Props = $props()
  let abierta = $state(true)

  function sincronizarDetalle(evento: Event) {
    abierta = (evento.currentTarget as HTMLDetailsElement).open
  }

  $effect(() => {
    const consulta = window.matchMedia('(max-width: 650px)')
    abierta = !consulta.matches
  })
</script>

<details class="globe-legend" open={abierta} ontoggle={sincronizarDetalle}>
  <summary>{LEYENDA.titulo}{#if mostrarAnio && anio}<span>Año {anio}</span>{/if}</summary>
  <div class="globe-legend__body">
    <div class="globe-legend__bar" role="img" aria-label={LEYENDA.aria}></div>
    <div class="globe-legend__labels"><span>{LEYENDA.leve}</span><span>{LEYENDA.fuerte}</span></div>
    <p>{LEYENDA.descripcion}</p>
  </div>
</details>

<style>
  .globe-legend { width: min(250px, calc(100vw - 34px)); padding: 11px 13px 12px; border: 1px solid var(--hairline); background: var(--panel-bg); backdrop-filter: blur(10px); pointer-events: auto; }
  summary { display: flex; justify-content: space-between; gap: 12px; cursor: pointer; list-style: none; font: 10px var(--mono); color: var(--muted); }
  summary::-webkit-details-marker { display: none; }
  summary::before { content: '＋'; color: var(--amber); }
  details[open] summary::before { content: '−'; }
  summary span { color: var(--amber); }
  .globe-legend__body { display: grid; gap: 6px; padding-top: 10px; }
   .globe-legend__bar { height: 8px; border-radius: 999px; background: linear-gradient(90deg, #3988c2, #d9d4c8 50%, #d99435); box-shadow: inset 0 0 0 1px rgba(243, 247, 252, .12); }
  .globe-legend__labels { display: flex; justify-content: space-between; gap: 12px; font: 9px/1.3 var(--mono); color: var(--faint); }
  p { color: var(--muted); font-size: 11px; line-height: 1.45; }
  @media (max-width: 650px) {
    .globe-legend { width: 100%; padding: 8px 11px; }
    .globe-legend__body { padding-top: 8px; }
  }
</style>
