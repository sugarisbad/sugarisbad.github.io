import { defineConfig } from 'astro/config';

// ────────────────────────────────────────────────────────────────────────────
// НАСТРОЙКА ПОД GITHUB PAGES — прочитайте перед первым деплоем:
//
//  • Репозиторий вида  username.github.io/psycholofy  (проектная страница):
//        site: 'https://username.github.io',  base: '/psycholofy/'
//    ⚠️ base ДОЛЖЕН совпадать с именем репозитория, иначе не подгрузится CSS.
//
//  • Репозиторий  username.github.io  (личная страница) или свой домен:
//        site: 'https://username.github.io',  base: '/'
//
// Замените значения ниже на свои.
// ────────────────────────────────────────────────────────────────────────────
export default defineConfig({
  site: 'https://sugarisbad.github.io',
  base: '/landing/',
});
