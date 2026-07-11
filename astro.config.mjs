import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// ────────────────────────────────────────────────────────────────────────────
// НАСТРОЙКА ПОД GITHUB PAGES:
//
//  • Проектная страница  username.github.io/<repo>:
//        site: 'https://username.github.io',  base: '/<repo>/'
//    ⚠️ base ДОЛЖЕН совпадать с именем репозитория, иначе не подгрузится CSS.
//
//  • Репозиторий  username.github.io  (личная страница) или свой домен:
//        site: 'https://username.github.io',  base: '/'
//
// ЯЗЫКИ: русский — на корне (/), английский — под /en/.
// Sitemap-интеграция сама проставляет hreflang-связи в sitemap.
// ────────────────────────────────────────────────────────────────────────────
export default defineConfig({
  site: 'https://opsmith.ru',
  base: '/',
  // CSS инлайнится в HTML: минус блокирующий запрос на критическом пути
  // (GitHub Pages отдаёт статику с кэшем всего 10 минут, так что отдельный
  // CSS-файл всё равно не кэшировался бы надолго).
  build: { inlineStylesheets: 'always' },
  i18n: {
    defaultLocale: 'ru',
    locales: ['ru', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  integrations: [
    sitemap({
      i18n: {
        defaultLocale: 'ru',
        locales: { ru: 'ru', en: 'en' },
      },
      filter: (page) => !page.includes('/404'),
      // lastmod = дата сборки: поисковики видят, что контент обновился
      serialize: (item) => ({ ...item, lastmod: new Date().toISOString() }),
    }),
  ],
});
