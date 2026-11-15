<script lang="ts">
  interface PropiedadesComponente {
    escalaMaxima: number
  }

  let { escalaMaxima }: PropiedadesComponente = $props()
</script>

<div class="leyenda" role="group" aria-label="Escala de cambios anuales">
  <div class="leyenda__cabeza">
    <span class="leyenda__titulo">Escala anual</span>
  </div>
  <div
    class="leyenda__barra"
    role="img"
    aria-label={`Más frío que lo normal a más cálido que lo normal. Escala fija de menos ${escalaMaxima.toFixed(4)} a más ${escalaMaxima.toFixed(4)}.`}
    title={`Escala fija: ±${escalaMaxima.toFixed(4)}`}
  ></div>
  <div class="leyenda__etiquetas">
    <span>más frío que lo normal</span>
    <span>más cálido que lo normal</span>
  </div>
</div>

<style>
  .leyenda {
    display: grid;
    gap: 5px;
    padding: 10px 0 2px;
  }

  .leyenda__cabeza,
  .leyenda__etiquetas {
    display: flex;
    justify-content: space-between;
    gap: 12px;
  }

  .leyenda__titulo,
  .leyenda__etiquetas {
    font: 10px var(--mono);
    color: var(--faint);
  }

  .leyenda__barra {
    height: 8px;
    border-radius: 999px;
    background: linear-gradient(90deg, #3988c2 0%, #d9d4c8 50%, #d99435 100%);
    box-shadow: inset 0 0 0 1px rgba(243, 247, 252, 0.12);
  }

  .leyenda__etiquetas {
    font-size: 9px;
    line-height: 1.3;
  }
</style>
