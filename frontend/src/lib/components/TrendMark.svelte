<script lang="ts">
  import type { Tendencia } from '../types/analysis'

  interface PropiedadesComponente {
    /** Dirección del cambio detectado. */
    tendencia: Tendencia
    /** Si es falso, se dibuja un rombo neutro (señal sin significancia). */
    significativa: boolean
    /** Muestra el nombre de la tendencia junto a la figura. */
    conTexto?: boolean
    /** Etiqueta alternativa (opcional) para el texto visible. */
    texto?: string
  }

  let { tendencia, significativa, conTexto = false, texto }: PropiedadesComponente = $props()

  const etiqueta = $derived(
    texto ?? (significativa ? (tendencia === 'alza' ? 'Alza' : 'Bajada') : 'Sin señal clara')
  )

  /** Descripción para lectores de pantalla: color + forma + texto. */
  const descripcion = $derived(
    significativa
       ? `Tendencia al ${tendencia === 'alza' ? 'alza' : 'baja'}, cambio claro`
       : 'Cambio poco claro'
  )
</script>

<span class="marca" class:marca--texto={conTexto} role="img" aria-label={descripcion} title={descripcion}>
  <i
    class="figura"
    class:figura--alza={significativa && tendencia === 'alza'}
    class:figura--bajada={significativa && tendencia === 'bajada'}
    class:figura--neutra={!significativa}
    aria-hidden="true"
  ></i>
  {#if conTexto}
    <span class="marca__texto">{etiqueta}</span>
  {/if}
</span>

<style>
  .marca {
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }

  /* Figuras con forma propia (▲ / ▼ / rombo) para no depender solo del color. */
  .figura {
    display: inline-block;
    flex: none;
    width: 11px;
    height: 11px;
  }

  .figura--alza {
    background: var(--trend-up);
    clip-path: polygon(50% 0, 100% 100%, 0 100%);
  }

  .figura--bajada {
    background: var(--trend-down);
    clip-path: polygon(0 0, 100% 0, 50% 100%);
  }

  .figura--neutra {
    width: 9px;
    height: 9px;
    transform: rotate(45deg);
    border: 2px dashed var(--trend-neutral);
  }

  .marca__texto {
    font: 10px var(--mono);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--muted);
    white-space: nowrap;
  }
</style>
