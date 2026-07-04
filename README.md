# DK — DevOps & AI-инфраструктура · лендинг

Одностраничный сайт-визитка на **[Astro](https://astro.build)**. Astro отдаёт статический
HTML с нулём JS в рантайме (только крошечный скрипт меню/анимаций), поэтому страница
грузится мгновенно и получает почти идеальные баллы Lighthouse. Идеально для GitHub Pages.

## Структура

```
astro.config.mjs          конфиг (⚠️ здесь настраивается base под GitHub Pages)
src/
  data/site.ts            весь контент и ЦЕНЫ (правьте здесь, а не в разметке)
  layouts/Base.astro      HTML-обёртка, SEO, фон, клиентский скрипт
  pages/index.astro       главная — секции рендерятся из data/site.ts
  pages/services.astro    страница прайса типовых услуг
  styles/global.css       дизайн-система 2026
bot/                      Telegram-бот приёма заявок (см. bot/README.md)
.github/workflows/deploy.yml   авто-сборка и деплой на GitHub Pages
```

Чтобы поменять текст, услуги или цену — редактируйте **`src/data/site.ts`**.

## Локальный запуск (нужен Node 18+)

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # прод-сборка в dist/
npm run preview  # предпросмотр прод-сборки
```

> Node можно скачать на nodejs.org. Локальная сборка **не обязательна** — GitHub Pages
> соберёт сайт сам (см. ниже).

## Деплой на GitHub Pages (без Node на вашей машине)

1. **Настройте `astro.config.mjs`** под своё имя репозитория:
   - репозиторий `landing` → страница будет по адресу `https://<user>.github.io/landing/`
     ```js
     site: 'https://<user>.github.io',
     base: '/landing/',              // ⚠️ ДОЛЖНО совпадать с именем репозитория
     ```
   - репозиторий `<user>.github.io` (личная страница) или свой домен → `base: '/'`.
2. Создайте репозиторий на GitHub и запушьте проект в ветку **main**:
   ```bash
   git init
   git add .
   git commit -m "site: лендинг DevOps/AI на Astro"
   git branch -M main
   git remote add origin https://github.com/<user>/<repo>.git
   git push -u origin main
   ```
3. В репозитории: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
4. Готово. Каждый `push` в `main` пересобирает и публикует сайт автоматически
   (workflow `.github/workflows/deploy.yml`).

## Обоснование цен (анализ рынка, середина 2026)

Цены заякорены под русскоязычный/CIS-рынок с премией за полный стек «сервер + ИИ +
автоматизация». Опорные данные:

| Пакет | Цена | На чём основано (mid-2026) |
|---|---|---|
| Настройка VPS | от 7 000 ₽ (~$80) | RU-фриланс за базовую настройку 2 100–3 000 ₽; здесь — автоматизация cloud-init, выше базовой |
| Self-hosted ИИ | от 20 000 ₽ (~$230) | заменяет $390–690/мес платных API; редкий, востребованный навык |
| ИИ-агент / бот | от 40 000 ₽ (~$460) | «mid-level» чат-бот/агент на глобальном рынке $300–800 + интеграции; для RU заякорено консервативно |
| Система под ключ | от 160 000 ₽ (~$1 850) | комплексные агентные системы стартуют от $5–15k глобально; локально — ниже |
| Ставка / абонентка | 4 000 ₽/час · от 10 000 ₽/мес | DevOps-фриланс Восточной Европы $50–95/час; RU-администрирование от 5 000 ₽/мес |

Источники: Index.dev (European developer rates 2026), Arc.dev (freelance rates 2026),
Aalpha (DevOps consultant rates), Fiverr / Metageeks (AI-agent & chatbot cost 2026),
Kwork / YouDo (RU-рынок администрирования), RamNode / Alpacked (self-hosted LLM).

> Все суммы «от …» — стартовые. Точная смета фиксируется письменно после созвона.
