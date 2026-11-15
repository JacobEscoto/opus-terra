import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const entorno = loadEnv(mode, process.cwd(), '')
  const urlSitio = entorno.VITE_URL_SITIO?.trim()

  return {
    plugins: [svelte(), {
      name: 'seo-url-sitio',
      transformIndexHtml(html: string) {
        if (!urlSitio) return html.replace(/\s*<[^>]+data-url-sitio[^>]*>\s*/g, '\n')
        return html
          .replace(/data-url-sitio="meta"/g, `content="${urlSitio}"`)
          .replace(/data-url-sitio="enlace"/g, `href="${urlSitio}"`)
      },
    }],
  }
})
