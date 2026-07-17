# Handoff: Блог + FAQ для opsmith (Monolith, RU/EN)

## Overview
Расширение сайта opsmith (репозиторий `sugarisbad/sugarisbad.github.io`, Astro) для органического роста:
1. **Блог** — список статей (RU/EN) + шаблон статьи + RSS. Ловит запросы вроде «настройка VPS под Docker», «мониторинг сервера своими руками».
2. **FAQ-блок на /work/** — в llms.txt уже заявлен FAQ на этой странице, но его там нет. Блок закрывает это расхождение + даёт расширенный сниппет через разметку `FAQPage`.

Стиль — «Monolith», идентичен предыдущему редизайну (см. `design_handoff_opsmith/README.md` в репозитории — там полные токены, шапка, футер, фоновая анимация; здесь не дублируются).

## About the Design Files
Файлы — **дизайн-референсы в HTML** (прототипы), а не production-код. Задача — **воссоздать их в Astro-стеке проекта**: страницы в `src/pages/blog/` (RU) и `src/pages/en/blog/` (EN), контент статей — в Astro Content Collections (`src/content/blog/`), i18n-строки — в `src/i18n/{ru,en}.ts`. `.dc.html`-файлы открываются в браузере напрямую — используйте как живой референс. Игнорируйте служебный тег `<x-dc>`, `support.js`; атрибуты `style-hover` → CSS `:hover`; `sc-for`/`sc-if` → шаблонизация Astro.

## Fidelity
**High-fidelity.** Цвета, типографика, отступы, состояния — финальные, воспроизводить пиксель-в-пиксель. Токены, шрифты (Space Grotesk / Manrope / JetBrains Mono), шапка, футер, фон — те же, что во всём редизайне Monolith.

## Files
- `Blog RU.dc.html`, `Blog EN.dc.html` — список статей
- `Article RU.dc.html` — шаблон статьи (пример: «Настройка VPS под Docker»)
- `Work RU.dc.html`, `Work EN.dc.html` — страница «Процесс» с новым FAQ-блоком (остальное без изменений)
- `support.js` — рантайм для просмотра `.dc.html`, в реализацию не переносится

## Screens / Views

### 1. Блог — список (`Blog RU/EN`)
URL: `/blog/` и `/en/blog/`.

- **Hero** (padding 110px 0 60px): flex space-between, align flex-end. Слева кикер «БЛОГ»/«BLOG» (JetBrains Mono .76rem, letter-spacing .32em, accent), H1 «Инженерные заметки, *без воды*.» / «Engineering notes, *no fluff*.» (Space Grotesk 500, clamp(2.6rem,5vw,4.4rem), курсивный em — accent), подзаголовок muted 1.12rem max-width 620px. Справа кнопка **RSS →** (JetBrains Mono .78rem, letter-spacing .12em, accent, рамка `--line2`, padding 10px 20px; hover: фон `--accent-dim`, рамка accent) → `/rss.xml`.
- **Featured-карточка** (свежая статья): grid 1.2fr/.8fr, рамка `--line`, фон `--panel` + blur(12px), hover `--accent-dim`, вся карточка — ссылка на статью. Слева (padding 48px 44px): строка мета — бейдж «СВЕЖЕЕ»/«LATEST» в рамке `--line2` + дата и время чтения (muted); H2 clamp(1.6rem,2.6vw,2.3rem); excerpt muted; «Читать статью →» (mono .78rem accent). Справа (border-left `--line`, скрывается ≤920px): **мини-терминал** — JetBrains Mono .82rem, line-height 2.15, muted; заголовок «vps-01 · provisioning» с мигающей зелёной точкой 8px (keyframes blink, как на главной); строки `$ ssh deploy@vps-01`, `✓ cloud-init ·· done` (галочки — `--ok`), `● node-exporter · listening` (точка — accent).
- **Фильтр по темам**: ряд кнопок-чипов (flex, gap 10px). JetBrains Mono .74rem, letter-spacing .1em, padding 8px 18px, без border-radius. Неактивная: рамка `--line2`, цвет muted; hover: рамка/цвет accent. Активная: заливка accent, текст `--bg`. Категории: Все/All · VPS · Docker · Мониторинг/Monitoring · CI/CD · Self-hosted ИИ/AI. Клик — мгновенная фильтрация списка; featured-карточка видна только на «Все».
- **Список статей**: строки-таблица, border-top + border-bottom `--line`, hover `--accent-dim` (transition .3s). Grid `150px 1fr 320px 60px`, gap 36px, baseline, padding 36px 8px: дата (mono .78rem muted; RU — `12.07.2026`, EN — `2026-07-12`) · заголовок (Space Grotesk 500 clamp(1.2rem,1.9vw,1.5rem)) + теги под ним (mono .7rem accent, рамка `--line`, padding 3px 10px) · excerpt (muted .94rem; скрыт ≤920px) · стрелка «→» (mono accent, справа).
- **Под списком**: слева счётчик «6 статей»/«6 articles» (mono .78rem muted), справа «Подписаться через RSS →» (accent).
- **CTA-секция**: H2 «Не хотите разбираться *сами*?» / «Don't want to do it *yourself*?», текст, кнопки: бот (primary, `?start=src-blog` / `src-blog-en`) + «Услуги и цены →» (вторичная).
- **Футер**: как везде + добавлена ссылка «RSS» рядом с email.

Демо-контент (6 статей, заголовки под семантическое ядро): настройка VPS под Docker · мониторинг Prometheus+Grafana · self-hosted LLM (Ollama) · CI/CD GitHub Actions · бэкапы 3-2-1 (restic) · failover без Kubernetes. Тексты дат/заголовков/excerpt — в логике `.dc.html`-файлов, копировать оттуда. Реальные статьи пишутся отдельно.

### 2. Статья (`Article RU`)
URL: `/blog/<slug>/`. EN-версия зеркальна (не прототипировалась).

- **Шапка статьи** (padding 100px 0 56px, border-bottom `--line`): «← БЛОГ» (mono .76rem muted, hover accent); мета-ряд — теги-бейджи VPS, DOCKER (рамка `--line2`, mono accent) + «12 июля 2026 · 9 мин чтения» (muted); H1 clamp(2.2rem,4.4vw,3.8rem) с курсивным accent-акцентом; лид muted 1.12rem max-width 680px.
- **Тело**: grid `1fr 300px`, gap 80px (≤920px — одна колонка, сайдбар скрыт). Колонка статьи max-width 720px:
  - **H2 секций**: Space Grotesk 500 1.7rem, перед текстом номер `/ 01` (mono .8rem accent, margin-right 14px), у каждого — `id` для якорей.
  - **Абзацы**: цвет muted (основной текст статьи — muted, не `--text`), margin-bottom 18px.
  - **Инлайн-код**: JetBrains Mono .86em, цвет accent, рамка `--line`, padding 1px 7px.
  - **Код-блоки** `<pre>`: JetBrains Mono .84rem, line-height 1.8, фон `--panel`, рамка `--line`, padding 26px 30px, overflow-x auto, без border-radius; комментарии — muted, ключевые значения — accent.
  - **Врезка «ИЗ ПРАКТИКИ»**: border-left 2px accent, padding-left 26px; заголовок mono .72rem letter-spacing .14em accent, текст muted .98rem.
  - **Чек-лист**: рамка `--line`, строки grid `52px 1fr` (padding 16px 24px, разделители `--line`, hover `--accent-dim`): галочка «✓» цветом `--ok` (mono) + текст muted.
  - **CTA-карточка в конце**: рамка `--line`, фон `--panel`, padding 40px; H3 с курсивным accent, текст, кнопки бот (primary) + калькулятор (вторичная).
- **Сайдбар** (sticky top 104px): кикер «СОДЕРЖАНИЕ» (mono .72rem letter-spacing .32em accent, border-bottom `--line2`); ссылки-якоря `/ 01 Зачем cloud-init` … (muted .9rem, hover accent); ниже через разделитель — блок автора (mono .76rem: «автор / OPSMITH · devops») и «RSS →».
- **Prev/next**: grid 1fr/1fr, разделитель `--line` посередине, padding 40px 8px, hover `--accent-dim`; кикер «← ПРЕДЫДУЩАЯ»/«СЛЕДУЮЩАЯ →» (mono .72rem muted) + заголовок (Space Grotesk 1.15rem). Правая ячейка — text-align right.

### 3. FAQ на странице «Процесс» (`Work RU/EN`)
Новая секция между «Принципы» и CTA (border-top `--line`, padding 90px 0 100px).

- **Заголовок**: flex space-between, align flex-end. Слева кикер «FAQ» + H2 «Частые *вопросы*.» / «Common *questions*.» (clamp(2rem,3.6vw,3rem)). Справа mono-подпись «не нашли свой? → спросите в боте» (muted, ссылка accent → бот `?start=src-work` / `src-work-en`).
- **Аккордеон**: 6 строк, border-top списка + border-bottom каждой `--line`. Строка-кнопка: grid `80px 1fr 40px`, gap 36px, baseline, padding 28px 8px, hover `--accent-dim`; номер `/ 01` (mono .8rem accent) · вопрос (Space Grotesk 500 clamp(1.1rem,1.8vw,1.35rem)) · индикатор «+»/«−» (mono 1.1rem accent, справа). Ответ раскрывается под вопросом в той же сетке (колонка 2), muted .98rem, max-width 680px, padding-bottom 32px.
- **Поведение**: по умолчанию открыт первый вопрос; клик открывает вопрос и закрывает предыдущий (одновременно открыт максимум один); повторный клик закрывает.
- Тексты 6 вопросов/ответов (цены, работа с существующей инфраструктурой, гарантия, сроки, root-доступ, оплата) — в логике `Work RU/EN.dc.html`, копировать дословно.

## Навигация (все страницы)
В шапку всех 8 существующих страниц добавлена ссылка «Блог»/«Blog» — четвёртой, после «Процесс»/«Process», перед переключателем RU/EN. Стили как у остальных ссылок; на страницах блога и статьи она активная (цвет `--text`, underline accent). Скрывается ≤920px вместе с остальными (`data-rhide`).

## SEO / технические требования (суть задачи)
1. **RSS**: `/rss.xml` через `@astrojs/rss` из Content Collection блога (title, description, pubDate, link). Ссылки на него: кнопка в hero блога, строка под списком, футер + `<link rel="alternate" type="application/rss+xml">` в `Base.astro`.
2. **FAQPage JSON-LD** на `/work/` и `/en/work/`: `Question`/`acceptedAnswer` с теми же 6 текстами, что в видимом FAQ (llms.txt уже обещает FAQ на /work/ — расхождение закрывается). Проверить на validator.schema.org.
3. **Статьи**: `BlogPosting` JSON-LD (headline, datePublished, author), canonical + hreflang как на остальных страницах, статьи — в sitemap автоматически.
4. Заголовки статей держать под запросы семантического ядра (`docs/semantic-core.md`).

## Interactions & Behavior
- Hover строк/карточек: `background: var(--accent-dim)`, transition .3s; вторичные кнопки: border/цвет → accent.
- Фильтр блога: клиентский (крошечный inline-скрипт или CSS-фильтрация), мгновенный.
- FAQ-аккордеон: см. выше; можно нативно на `<details>` с сохранением визуала.
- Появление hero — каскад fadeup (0/.08/.16/.24/.3s), как на остальных страницах.
- Responsive ≤920px: многоколоночные grid → 1 колонка; excerpt в списке и терминал в featured скрыты; сайдбар статьи скрыт; ссылки разделов в шапке скрыты.

## State Management
- Блог: `activeCategory` (фильтр), производный список постов; featured виден только при «Все».
- FAQ: `openIndex: number | -1`.
- Остальное — статика.

## Design Tokens
Полностью совпадают с `design_handoff_opsmith/README.md` (тёмная/светлая через `prefers-color-scheme`): `--bg #0b0b0d/#f5f2ea`, `--panel`, `--line`, `--line2`, `--text`, `--muted`, `--accent #d8c9a3/#9b8a5c`, `--accent-dim`, `--ok #7fd4a8/#2c9e68`, `--btn-bg/fg`. Без border-radius. Шрифты Google Fonts: Space Grotesk 500 (заголовки), Manrope (текст), JetBrains Mono (кикеры, даты, код, чипы).

## Assets
Внешних картинок нет. Фон (SVG-линии + вертикальная сетка) — код, тот же, что на остальных страницах.
