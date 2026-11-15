<script lang="ts">
  import TrendMark from './TrendMark.svelte'
</script>

<!--
  Leyenda accesible: cada significado tiene forma + texto, no solo color.
  Los colores provienen de --trend-up / --trend-down definidas en app.css.
-->
<div class="leyenda" role="group" aria-label="Leyenda de tendencias">
  <span class="leyenda__titulo">Leyenda</span>
  <ul class="leyenda__lista">
    <li><TrendMark tendencia="alza" significativa conTexto /></li>
    <li><TrendMark tendencia="bajada" significativa conTexto /></li>
    <li><TrendMark tendencia="alza" significativa={false} conTexto texto="No significativa" /></li>
  </ul>
</div>

<style>
  .leyenda {
    display: flex;
    align-items: baseline;
    gap: 18px;
  }

  .leyenda__titulo {
    font: 10px var(--mono);
    letter-spacing: 0.08em;
    color: var(--faint);
  }

  .leyenda__lista {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 16px;
    margin: 0;
    padding: 0;
    list-style: none;
  }
</style>
