import { defineConfig } from 'astro/config';

// ────────────────────────────────────────────────────────────────────────────
// НАСТРОЙКА ПОД GITHUB PAGES:
//
//  • Проектная страница  username.github.io/<repo>:
//        site: 'https://username.github.io',  base: '/<repo>/'
//    ⚠️ base ДОЛЖЕН совпадать с именем репозитория, иначе не подгрузится CSS.
//
//  • Репозиторий  username.github.io  (личная страница) или свой домен:
//        site: 'https://username.github.io',  base: '/'
// ────────────────────────────────────────────────────────────────────────────
export default defineConfig({
  site: 'https://sugarisbad.github.io',
  base: '/',
});
