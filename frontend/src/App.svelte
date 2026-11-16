<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import EarthGlobe from "./lib/components/EarthGlobe.svelte";
  import AnalysisPanel from "./lib/components/AnalysisPanel.svelte";
  import TimelineControl from "./lib/components/TimelineControl.svelte";
  import {
    cargarVariable,
    cargarRegiones,
    cargarPaises,
    CATALOGO,
    type EstadoCarga,
    type RegionDisponible,
  } from "./lib/data/loadAnalysis";
  import {
    cargarPaisesGeo,
    paisEnPunto,
    regionDePais,
    type PaisGeo,
    type RegionDisponibleLocal,
  } from "./lib/geo/paises";
  import {
    prepararCapa,
    tieneValoresAnuales,
    nombreCorto,
  } from "./lib/data/capa";
  import type { ParRegiones } from "./lib/types/analysis";
  import type { EtiquetaGlobo } from "./lib/three/etiquetasLayer";
  import { registrarEtiquetas } from "./lib/three/etiquetasLayer";
  import GlobeLegend from "./lib/components/GlobeLegend.svelte";
  import VariableMenu from "./lib/components/VariableMenu.svelte";
  import PaisChip from "./lib/components/PaisChip.svelte";
  import Metodologia from "./lib/components/paginas/Metodologia.svelte";
  import Fuentes from "./lib/components/paginas/Fuentes.svelte";
  import Glosario from "./lib/components/paginas/Glosario.svelte";
  import AcercaDe from "./lib/components/paginas/AcercaDe.svelte";
  import { APP, AYUDA_MAPA, NAVEGACION } from "./lib/data/textos";

  type Enfocar = (lat: number, lon: number, duracion: number) => Promise<void>;
  type FijarRotacionAutomatica = (habilitada: boolean) => void;

  let carga = $state<EstadoCarga>({ estado: "cargando" });
  let variableActiva = $state("merra2_t2m");
  let variablesCargadas = $state<string[]>([]);
  let regiones = $state<RegionDisponible[]>([]);
  let regionActiva = $state("honduras");
  let paises = $state<EtiquetaGlobo[]>([]);

  /** Territorios del GeoJSON, para dibujar fronteras y detectar pulsaciones. */
  let geo = $state<PaisGeo[]>([]);
  /** Selección geográfica, separada de la región que provee los datos. */
  let paisSeleccionado = $state<{
    pais: PaisGeo;
    region: RegionDisponibleLocal | null;
  } | null>(null);
  /** Los controles de leyenda y línea de tiempo pueden plegarse. */
  let controlesAbiertos = $state(true);

  const regionActual = $derived(
    regiones.find((region) => region.id == regionActiva) ?? null,
  );

  const variablesDisponibles = $derived(
    regionActual
      ? CATALOGO.filter((variable) =>
          regionActual.variables.includes(variable.id),
        )
      : CATALOGO,
  );

  let solicitud = 0;

  /** Identificador del par elegido en la lista; null = vista de lista. */
  let idSeleccionado = $state<string | null>(null);

  /** Año mostrado en el panel cuando existan series anuales por celda. */
  let anio = $state<number>(2023);
  let mostrarAyuda = $state(false);
  let recorridoActivo = $state(false);
  let enfocar = $state<Enfocar | null>(null);
  let cancelFocus = $state<(() => void) | null>(null);
  let fijarRotacionAutomatica = $state<FijarRotacionAutomatica | null>(null);
  let timerRecorrido: ReturnType<typeof setTimeout> | null = null;
  let recorridoToken = 0;
  type Pagina = "metodologia" | "fuentes" | "glosario" | "acerca";
  const PAGINAS: Pagina[] = ["metodologia", "fuentes", "glosario", "acerca"];
  let pagina = $state<Pagina | null>(null);
  let enlaceQueAbrioPagina = $state<HTMLElement | null>(null);
  let menuAbierto = $state(false);

  /** El panel de análisis solo se muestra cuando el usuario lo pide. */
  let panelAbierto = $state(false);

  /**
   * En escritorio, con el panel abierto, la columna del panel queda a la
   * derecha y un offset negativo desplaza el planeta a la izquierda. Con el
   * panel cerrado, o en móvil, el planeta queda centrado.
   */
  let escritorio = $state(true);

  const desplazamiento = $derived(escritorio && panelAbierto ? -0.17 : 0);

  const datos = $derived(carga.estado === "listo" ? carga.datos : null);
  const preparacion = $derived(datos ? prepararCapa(datos) : null);
  const anualesDisponibles = $derived(
    datos ? tieneValoresAnuales(datos) : false,
  );

  const parSeleccionado = $derived(
    datos
      ? (datos.pares.find((par) => par.id === idSeleccionado) ?? null)
      : null,
  );

  const etiquetasGlobo = $derived([
    ...paises,
    ...(parSeleccionado
      ? [parSeleccionado.region_a, parSeleccionado.region_b].map((region) => ({
          texto: nombreCorto(region),
          lat: region.lat,
          lon: region.lon,
          tipo: "lugar" as const,
        }))
      : []),
  ]);

  $effect(() => {
    registrarEtiquetas(etiquetasGlobo);
  });

  function paginaDesdeHash() {
    const hash = window.location.hash.slice(1) as Pagina;
    pagina = PAGINAS.includes(hash) ? hash : null;
  }

  /**
   * Pulsación sobre el globo: resuelve el territorio por sus geometrías y,
   * solo si la región de datos es distinta, cambia la región activa. La
   * selección geográfica y la disponibilidad de datos van por separado.
   */
  async function manejarSeleccionGlobo(lat: number, lon: number) {
    if (geo.length === 0) return;
    const pais = paisEnPunto(geo, lat, lon);
    if (!pais) {
      paisSeleccionado = null;
      return;
    }
    const region = regionDePais(pais, regiones);
    paisSeleccionado = { pais, region };
    if (region && region.id !== regionActiva) {
      await cambiarRegion(region.id, true);
    }
  }

  function abrirPagina(nombre: Pagina, evento?: MouseEvent) {
    if (evento?.currentTarget instanceof HTMLElement)
      enlaceQueAbrioPagina = evento.currentTarget;
    mostrarAyuda = false;
    menuAbierto = false;
    window.location.hash = nombre;
  }

  function cerrarPagina(restaurarFoco = false) {
    window.location.hash = "";
    if (restaurarFoco)
      requestAnimationFrame(() => enlaceQueAbrioPagina?.focus());
  }

  function abrirPanel() {
    panelAbierto = true;
  }

  function cerrarPanel() {
    detenerRecorrido();
    idSeleccionado = null;
    panelAbierto = false;
  }

  function manejarEscape(evento: KeyboardEvent) {
    if (evento.key !== "Escape") return;
    if (menuAbierto) {
      menuAbierto = false;
      return;
    }
    if (pagina) {
      evento.preventDefault();
      cerrarPagina(true);
      return;
    }
    if (panelAbierto) {
      cerrarPanel();
    }
  }

  function esperar(ms: number, token: number): Promise<boolean> {
    return new Promise((resolve) => {
      timerRecorrido = setTimeout(() => {
        timerRecorrido = null;
        resolve(token === recorridoToken);
      }, ms);
    });
  }

  function detenerRecorrido() {
    recorridoToken += 1;
    recorridoActivo = false;
    if (timerRecorrido !== null) {
      clearTimeout(timerRecorrido);
      timerRecorrido = null;
    }
    cancelFocus?.();
    fijarRotacionAutomatica?.(true);
  }

  async function iniciarRecorrido(pares: ParRegiones[]) {
    if (recorridoActivo) {
      detenerRecorrido();
      return;
    }
    if (!enfocar || pares.length === 0) return;

    const token = ++recorridoToken;
    recorridoActivo = true;
    fijarRotacionAutomatica?.(false);
    for (const par of pares) {
      if (token !== recorridoToken) return;
      idSeleccionado = par.id;
      const lat = (par.region_a.lat + par.region_b.lat) / 2;
      const lon = (par.region_a.lon + par.region_b.lon) / 2;
      await enfocar(lat, lon, 2000);
      if (token !== recorridoToken) return;
      if (!(await esperar(4000, token))) return;
    }
    if (token === recorridoToken) {
      recorridoActivo = false;
      idSeleccionado = null;
      fijarRotacionAutomatica?.(true);
    }
  }

  function alPrepararGlobo(
    siguienteEnfoque: Enfocar,
    nextCancelFocus: () => void,
    siguienteRotacion: FijarRotacionAutomatica,
  ) {
    enfocar = siguienteEnfoque;
    cancelFocus = nextCancelFocus;
    fijarRotacionAutomatica = siguienteRotacion;
  }

  function enfocarRegion(lat: number, lon: number) {
    void enfocar?.(lat, lon, 900);
  }

  /** Lee el JSON seleccionado y reemplaza la capa sin crear otra escena. */
  async function cambiarVariable(id: string) {
    detenerRecorrido();
    const numeroSolicitud = ++solicitud;
    variableActiva = id;
    carga = { estado: "cargando" };
    idSeleccionado = null;
    try {
      const resultado = await cargarVariable(id, regionActiva);
      if (numeroSolicitud !== solicitud) return;
      if (!variablesCargadas.includes(id))
        variablesCargadas = [...variablesCargadas, id];
      carga = { estado: "listo", datos: resultado };
      anio = resultado.periodo.fin;
    } catch (error: unknown) {
      if (numeroSolicitud !== solicitud) return;
      carga = {
        estado: "error",
        mensaje:
          error instanceof Error
            ? error.message
            : "No se pudieron leer los datos de análisis.",
      };
    }
  }

  async function cambiarRegion(id: string, conservarSeleccion = false) {
    if (id === regionActiva) return;
    detenerRecorrido();
    regionActiva = id;
    idSeleccionado = null;
    if (!conservarSeleccion) paisSeleccionado = null;
    variablesCargadas = [];
    const numeroRegion = ++solicitud;
    const paisesCargados = await cargarPaises(id);
    if (numeroRegion !== solicitud || id !== regionActiva) return;
    paises = paisesCargados;

    const permitidas =
      regiones.find((region) => region.id === id)?.variables ?? [];
    if (!permitidas.includes(variableActiva)) {
      variableActiva = permitidas[0] ?? variableActiva;
    }
    await cambiarVariable(variableActiva);
  }

  function cargar() {
    void cambiarVariable(variableActiva);
    const numeroRegion = solicitud;
    void cargarPaises(regionActiva).then((cargados) => {
      if (numeroRegion === solicitud) paises = cargados;
    });
  }

  onMount(() => {
    controlesAbiertos =
      typeof window !== "undefined"
        ? window.matchMedia("(min-width: 651px)").matches
        : true;
    void cargarRegiones()
      .then((list) => (regiones = list))
      .catch(console.error);
    void cargarPaises(regionActiva)
      .then((cargados) => (paises = cargados))
      .catch(console.error);
    void cargarPaisesGeo()
      .then((cargados) => (geo = cargados))
      .catch(console.error);
    void cambiarVariable(variableActiva);
    paginaDesdeHash();
    window.addEventListener("hashchange", paginaDesdeHash);
    window.addEventListener("keydown", manejarEscape);

    // Sincroniza el desplazamiento del planeta con el punto de quiebre del layout.
    const consulta = window.matchMedia("(min-width: 1000px)");
    escritorio = consulta.matches;
    const actualizar = (evento: MediaQueryListEvent) =>
      (escritorio = evento.matches);
    consulta.addEventListener("change", actualizar);
    return () => {
      consulta.removeEventListener("change", actualizar);
      window.removeEventListener("hashchange", paginaDesdeHash);
      window.removeEventListener("keydown", manejarEscape);
    };
  });

  onDestroy(() => {
    detenerRecorrido();
    cancelFocus?.();
  });
</script>

<svelte:head>
  <title>
    {pagina === "metodologia"
      ? "Metodología — OpusTerra"
      : pagina === "fuentes"
        ? "Fuentes de datos — OpusTerra"
        : pagina === "glosario"
          ? "Glosario — OpusTerra"
          : pagina === "acerca"
            ? "Acerca de — OpusTerra"
            : "OpusTerra — Cambios ambientales en el planeta"}
  </title>
  <meta
    name="description"
    content="Globo 3D con datos satelitales de la NASA para explorar tendencias de temperatura, lluvia y vegetación del planeta de forma clara y verificable."
  />
  <meta
    property="og:title"
    content="OpusTerra — Cambios ambientales en el planeta"
  />
  <meta
    property="og:description"
    content="Globo 3D con datos satelitales de la NASA para explorar tendencias de temperatura, lluvia y vegetación del planeta de forma clara y verificable."
  />
</svelte:head>

<!-- dataMode ilumina el planeta de forma pareja mientras un par está abierto;
     horizontalOffset lo corre a la izquierda para despejar la columna del panel. -->
<EarthGlobe
  horizontalOffset={desplazamiento}
  dataMode={parSeleccionado !== null}
  celdas={preparacion?.celdasCapa ?? []}
  {anio}
  anios={datos?.periodo.anios_completos ?? []}
  escalaMaxima={preparacion?.escalaMaxima}
  onReady={alPrepararGlobo}
  onInteraction={detenerRecorrido}
  onSelect={manejarSeleccionGlobo}
  {geo}
  seleccion={paisSeleccionado?.pais ?? null}
/>

<main class="interface" class:con-panel={panelAbierto}>
  <header class="masthead">
    <span>{APP.marca}</span>
    <button
      class="menu-button"
      type="button"
      aria-label={menuAbierto ? NAVEGACION.cerrarMenu : NAVEGACION.menu}
      aria-expanded={menuAbierto}
      aria-controls="site-menu"
      onclick={() => (menuAbierto = !menuAbierto)}
    >
      <span></span><span></span><span></span>
    </button>
  </header>

  {#if menuAbierto}
    <div
      id="site-menu"
      class="site-menu"
      role="dialog"
      aria-label={NAVEGACION.menu}
    >
      <nav aria-label="Secciones del sitio">
        <a
          href="#metodologia"
          onclick={(evento) => abrirPagina("metodologia", evento)}
          >{NAVEGACION.metodologia}</a
        >
        <a href="#fuentes" onclick={(evento) => abrirPagina("fuentes", evento)}
          >{NAVEGACION.fuentes}</a
        >
        <a
          href="#glosario"
          onclick={(evento) => abrirPagina("glosario", evento)}
          >{NAVEGACION.glosario}</a
        >
        <a href="#acerca" onclick={(evento) => abrirPagina("acerca", evento)}
          >{NAVEGACION.acerca}</a
        >
      </nav>
      <button
        class="about-button"
        type="button"
        aria-expanded={mostrarAyuda}
        aria-controls="about-panel"
        onclick={() => (mostrarAyuda = !mostrarAyuda)}
        >{NAVEGACION.comoLeer}</button
      >
      {#if mostrarAyuda}
        <div id="about-panel" class="about-panel" aria-labelledby="about-title">
          <h2 id="about-title">{APP.ayudaTitulo}</h2>
          <p>{APP.ayudaTexto}</p>
          <div class="help-links">
            {#each AYUDA_MAPA.enlaces as enlace}<a
                href={enlace.href}
                onclick={(evento) =>
                  abrirPagina(enlace.href.slice(1) as Pagina, evento)}
                >{enlace.texto}</a
              >{/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Controles contextuales: variable y región arriba a la izquierda; el
       país pulsado se anida debajo para no repartir elementos por la pantalla. -->
  <div class="hud hud--variables">
    <VariableMenu
      variables={variablesDisponibles}
      activa={variableActiva}
      cargadas={variablesCargadas}
      {regiones}
      {regionActiva}
      onCambiarVariable={(id) => void cambiarVariable(id)}
      onCambiarRegion={(id) => void cambiarRegion(id)}
    />
    {#if paisSeleccionado}
      <div class="hud__chip">
        <PaisChip
          nombre={paisSeleccionado.pais.nombre}
          regionNombre={paisSeleccionado.region?.nombre ?? null}
          onCerrar={() => (paisSeleccionado = null)}
        />
      </div>
    {/if}
  </div>

  <!-- Vista inicial: solo globo + leyenda y línea de tiempo abajo a la izquierda. -->
  <div class="stage">
    <div class="dock">
      <button
        type="button"
        class="dock__toggle"
        aria-expanded={controlesAbiertos}
        onclick={() => (controlesAbiertos = !controlesAbiertos)}
      >
        {controlesAbiertos ? APP.cerrarControles : APP.abrirControles}
      </button>
      {#if controlesAbiertos}
        <div class="legend-slot">
          <GlobeLegend />
        </div>
        {#if datos}
          <div class="timeline-slot">
            <TimelineControl
              inicio={datos.periodo.inicio}
              fin={datos.periodo.fin}
              bind:anio
              disponible={anualesDisponibles}
              aviso={APP.avisoSinSerie}
            />
          </div>
        {/if}
      {/if}
      {#if !panelAbierto}
        <button type="button" class="open-panel" onclick={abrirPanel}
          >Ver análisis</button
        >
      {/if}
    </div>
  </div>

  <!-- Columna del panel: solo existe cuando el usuario la abre. -->
  {#if panelAbierto}
    <aside class="rail">
      <div class="rail-slot">
        <button type="button" class="rail-close" onclick={cerrarPanel}
          >Cerrar ✕</button
        >
        <AnalysisPanel
          {carga}
          {parSeleccionado}
          onSeleccionar={(id) => (idSeleccionado = id)}
          onVolver={() => (idSeleccionado = null)}
          onReintentar={cargar}
          {preparacion}
          {recorridoActivo}
          onRecorrido={() => datos && void iniciarRecorrido(datos.pares)}
          onEnfocarRegion={enfocarRegion}
        />
      </div>
    </aside>
  {/if}
</main>

<footer class="site-footer">© {new Date().getFullYear()} Pegaso-X</footer>

{#if pagina}
  <div class="page-layer" role="dialog" aria-modal="true">
    {#if pagina === "metodologia"}
      <Metodologia onCerrar={() => cerrarPagina()} />
    {:else if pagina === "fuentes"}
      <Fuentes onCerrar={() => cerrarPagina()} />
    {:else if pagina === "glosario"}
      <Glosario onCerrar={() => cerrarPagina()} />
    {:else}
      <AcercaDe onCerrar={() => cerrarPagina()} />
    {/if}
  </div>
{/if}

<style>
  /* La .interface global es pointer-events: none; los slots reactivan los
     eventos solo donde hay controles, para no bloquear la órbita del globo. */
  .interface {
    display: grid;
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
    grid-template-areas:
      "masthead"
      "stage";
  }

  .interface.con-panel {
    grid-template-columns: 1fr minmax(340px, 430px);
    grid-template-areas:
      "masthead masthead"
      "stage    rail";
    column-gap: 48px;
  }

  .masthead {
    grid-area: masthead;
    justify-content: space-between;
    pointer-events: auto;
  }

  .menu-button {
    display: grid;
    gap: 4px;
    width: 36px;
    height: 32px;
    padding: 8px 7px;
    margin-left: auto;
    border: 1px solid var(--hairline);
    background: transparent;
  }
  .menu-button span {
    display: block;
    width: 100%;
    height: 1px;
    background: var(--ink);
  }
  .site-menu {
    position: absolute;
    top: 76px;
    right: 42px;
    z-index: 4;
    width: min(300px, calc(100vw - 48px));
    padding: 18px;
    border: 1px solid var(--hairline);
    background: rgba(16, 27, 44, 0.98);
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.3);
    pointer-events: auto;
  }
  .site-menu nav {
    display: grid;
    gap: 15px;
    font: 12px var(--mono);
  }
  .site-menu nav a {
    color: var(--ink);
  }
  .site-menu nav a:hover,
  .help-links a:hover {
    color: var(--amber);
  }
  .site-menu .about-button {
    margin-top: 20px;
  }
  .help-links {
    display: flex;
    gap: 16px;
    margin-top: 16px;
    font: 10px var(--mono);
    color: var(--amber);
  }
  .site-menu .about-panel {
    position: static;
    width: auto;
    margin: 18px 0 0;
    padding: 16px 0 0;
    border: 0;
    border-top: 1px solid var(--hairline);
    background: transparent;
    box-shadow: none;
  }

  .stage {
    grid-area: stage;
    min-height: 0;
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    align-items: flex-start;
    padding-bottom: 4px;
  }

  .rail {
    grid-area: rail;
    min-width: 0;
  }

  .dock {
    display: grid;
    gap: 10px;
    justify-items: start;
    width: 100%;
  }

  /* Controles flotantes: no interceptan el puntero salvo en sus propios
     controles, para dejar libres la órbita y la pulsación del globo. */
  .hud {
    position: absolute;
    z-index: 2;
    pointer-events: none;
  }

  .hud--variables {
    top: 74px;
    left: 42px;
    width: min(320px, calc(100vw - 84px));
  }

  .hud__chip {
    margin-top: 8px;
  }

  .dock__toggle,
  .open-panel,
  .rail-close {
    padding: 8px 12px;
    border: 1px solid var(--muted);
    background: var(--panel-bg);
    backdrop-filter: blur(10px);
    font: 10px var(--mono);
    color: var(--ink);
    pointer-events: auto;
  }

  .dock__toggle {
    justify-self: start;
  }

  .dock__toggle:hover,
  .dock__toggle:focus-visible {
    border-color: var(--amber);
    color: var(--amber);
  }

  .rail-slot,
  .legend-slot,
  .timeline-slot {
    pointer-events: auto;
  }

  .open-panel,
  .rail-close {
    padding: 8px 12px;
    border: 1px solid var(--muted);
    background: var(--panel-bg);
    backdrop-filter: blur(10px);
    font: 10px var(--mono);
    color: var(--ink);
    pointer-events: auto;
  }

  .open-panel:hover,
  .open-panel:focus-visible,
  .rail-close:hover,
  .rail-close:focus-visible {
    border-color: var(--amber);
    color: var(--amber);
  }

  .rail-close {
    display: block;
    margin: 0 0 8px auto;
  }

  .page-layer {
    position: fixed;
    inset: 0;
    z-index: 20;
    overflow-y: auto;
    background: var(--bg);
    pointer-events: auto;
  }
  .site-footer {
    position: fixed;
    right: 20px;
    bottom: 12px;
    z-index: 3;
    color: var(--faint);
    font: 10px var(--mono);
    pointer-events: none;
  }

  /* Columna única: panel debajo del masthead, línea de tiempo al final. */
  @media (max-width: 899px) {
    .interface,
    .interface.con-panel {
      grid-template-columns: 1fr;
      grid-template-rows: auto minmax(260px, 1fr) auto;
      grid-template-areas:
        "masthead"
        "stage"
        "rail";
      column-gap: 0;
    }

    .stage {
      position: relative;
      justify-content: flex-end;
      padding: 18px 0 10px;
    }

    .rail {
      position: relative;
      z-index: 2;
      width: 100%;
    }

    /* Con el panel abierto en móvil, el panel ocupa el espacio inferior. */
    .con-panel .dock {
      display: none;
    }

    .site-menu {
      right: 24px;
    }

    .hud--variables {
      top: 64px;
      left: 24px;
      width: min(320px, calc(100vw - 48px));
    }
  }

  @media (max-width: 650px) {
    .site-menu {
      top: 64px;
      right: 17px;
      width: min(300px, calc(100vw - 34px));
    }

    .hud--variables {
      top: 64px;
      right: 17px;
      left: 17px;
      width: auto;
    }

    .stage {
      min-height: 285px;
      padding: 15px 0 8px;
    }

    .dock {
      gap: 8px;
    }

    :global(.dock .timeline) {
      width: 100%;
      min-width: 0;
      background: rgba(11, 18, 32, 0.48);
      border-color: rgba(237, 243, 250, 0.2);
    }

    /* En móvil el pie de página chocaría con la línea de tiempo. */
    .site-footer {
      display: none;
    }
  }
</style>
