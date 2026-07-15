# Handoff: Opsmith — редизайн сайта (Monolith, RU/EN, светлая/тёмная тема)

## Overview
Полный редизайн сайта DevOps-студии opsmith (текущий репозиторий: `sugarisbad/sugarisbad.github.io`, Astro). 8 страниц: Главная, Кейсы, Услуги+калькулятор, Процесс — каждая в RU и EN. Стиль «Monolith»: люкс-минимализм для корпоративных клиентов.

## About the Design Files
Файлы в этом пакете — **дизайн-референсы в HTML** (прототипы, показывающие внешний вид и поведение), а не production-код. Задача — **воссоздать эти макеты в существующем стеке проекта (Astro)**, используя его паттерны: страницы в `src/pages/` (RU) и `src/pages/en/` (EN), данные в `src/data/`, i18n в `src/i18n/`. `.dc.html`-файлы открываются в браузере напрямую — используйте их как живой референс. Игнорируйте служебный тег `<x-dc>`, атрибуты `style-hover` (это hover-стили → переведите в CSS :hover), `sc-for`/`sc-if` (циклы/условия → шаблонизация Astro) и `support.js`.

## Fidelity
**High-fidelity.** Цвета, типографика, отступы, состояния — финальные. Воспроизводить пиксель-в-пиксель.

## Design Tokens
Тема выбирается автоматически через `@media (prefers-color-scheme)` + `color-scheme: dark light`. Всё построено на CSS-переменных:

Тёмная (по умолчанию):
- `--bg: #0b0b0d` — фон
- `--panel: rgba(17,17,20,.72)` — панели/шапка (с `backdrop-filter: blur(12-14px)`)
- `--line: rgba(216,201,163,.14)` — тонкие разделители (1px)
- `--line2: rgba(216,201,163,.34)` — границы кнопок/рамок
- `--text: #f2ede1` — основной текст
- `--muted: #8a8578` — вторичный текст
- `--accent: #d8c9a3` — шампань-акцент (курсивные em, кикеры, цифры)
- `--accent-dim: rgba(216,201,163,.08)` — hover-фон строк/карточек
- `--ok: #7fd4a8` — статус healthy
- `--btn-bg: #d8c9a3`, `--btn-fg: #0b0b0d` — основная кнопка

Светлая (`prefers-color-scheme: light`):
- `--bg: #f5f2ea`, `--panel: rgba(251,249,244,.78)`, `--line: rgba(110,102,80,.18)`, `--line2: rgba(110,102,80,.4)`, `--text: #17150f`, `--muted: #6e6650`, `--accent: #9b8a5c`, `--accent-dim: rgba(155,138,92,.08)`, `--ok: #2c9e68`, `--btn-bg: #17150f`, `--btn-fg: #f5f2ea`

Типографика (Google Fonts):
- Заголовки: Space Grotesk, weight 500 (не bold!), letter-spacing -0.03em, line-height 1.04; акцентные слова — `<em>` курсивом цветом `--accent`
- Текст: Manrope 400/500/600, line-height 1.65
- Моно (кикеры, цены, панель статуса): JetBrains Mono; кикеры — 0.76rem, letter-spacing 0.32em, uppercase, цвет `--accent`
- H1: clamp(2.4rem, 5vw, 4.4–4.6rem); H2: clamp(2rem, 3.6–4vw, 3–3.2rem)

Прочее:
- Кнопки и рамки — **без border-radius** (острые углы, часть стиля)
- Основная кнопка: `background: var(--btn-bg); color: var(--btn-fg); padding: 16px 38px; font-weight: 600; letter-spacing: .04em`; hover: opacity .88
- Вторичная: `border: 1px solid var(--line2)`; hover: border/цвет → `--accent`
- Селекшн: `::selection{background:var(--accent);color:var(--bg)}`

## Фоновая анимация (все страницы)
Fixed full-viewport слой (z-index 0, pointer-events none):
1. SVG с 1–3 кривыми Безье через экран, `stroke: var(--accent)/var(--muted)`, opacity .12–.3, `stroke-dasharray: 800` + keyframes `lineflow` (stroke-dashoffset 800→0, 12–20s linear infinite) + 2–3 точки-circle на линиях
2. Вертикальные волосяные линии: `background-image: linear-gradient(90deg, var(--line) 1px, transparent 1px); background-size: 140px 100%; opacity: .5`
3. На главной — мягкое radial-пятно `--accent-dim` 640px, дрейф (`slowdrift`, 18s)

Появление контента: keyframes `fadeup` (opacity 0 + translateY(20px) → нет), каскад задержек 0/.08/.16/.3s.

## Screens / Views
Референсы содержат точные тексты RU и EN — копировать из файлов.

### Шапка (все страницы)
Sticky, `background: var(--panel)` + blur, нижняя граница `--line`, высота 72px, контейнер max-width 1240px, padding 0 24px. Слева логотип «OPSMITH» (Space Grotesk 700, letter-spacing .14em). Справа: 3 ссылки разделов (0.9rem; активная — `--text` + underline 1px `--accent`), переключатель RU/EN (рамка `--line2`, активный язык — фон `--accent`), кнопка «Созвон»/«Book a call» → https://calendly.com/opsmith/30min (hover: заливка `--accent`).

### Главная (Home RU/EN)
1. Hero: grid 1.25fr/.75fr, gap 70px. Слева кикер «DEVOPS · INFRASTRUCTURE · AI», H1 «Инженерия инфраструктуры для компаний, которым *нельзя падать*.» / «Infrastructure engineering for companies that *cannot go down*.», подзаголовок, 2 кнопки (Обсудить проект → #contact; Кейсы →). Справа — **панель статуса продакшена**: рамка `--line`, фон `--panel`, JetBrains Mono 0.82rem, line-height 2.15; строки «api-cluster / db-primary / ai-inference / ci/cd pipeline — ● healthy/passing» (`--ok`), «failover — standby» (`--accent`), разделитель, «uptime / 2025 — 99.98%», «без инцидентов — 214 дней»; зелёная точка в заголовке мигает (keyframes blink, 50% opacity .25).
2. Статистика: 4 колонки с левыми границами `--line`: `<60 сек` (accent), 24/7, 10, `0 ₽`/`$0` + подписи.
3. Услуги: заголовок-грид (.85fr/1.15fr) + 6 строк-грид (80px номер / заголовок / описание / стрелка), разделители `--line`, hover `--accent-dim`. Кнопки: Цены и калькулятор; Как мы работаем →.
4. Кейсы-превью: 3 карточки в grid с gap 1px на фоне `--line` (эффект таблицы), цифра accent 2.3rem + заголовок + текст.
5. Контакт (#contact): H2 с курсивным акцентом, кнопки: бот (primary), Calendly, mailto:contact@opsmith.ru.
6. Футер: OPSMITH · contact@opsmith.ru · «devops · automation · self-hosted ai».

### Кейсы (Cases RU/EN)
Hero-заголовок «Системы, которые работают *без нас*.» / «Systems that run *without us*.». 3 кейса — строки таблицы (gap 1px на `--line`): слева (1.35fr) номер `case_01` + бейдж в рамке + H2 + абзацы «Задача./Problem.» и «Решение./Solution.» + теги стека (JetBrains Mono 0.72rem в рамках `--line`); справа (1fr, левая граница) — 3 метрики (значение accent 2.3rem + подпись). CTA-секция + футер.

### Услуги и цены (Services RU/EN) — калькулятор
Данные прайса — в `pricing.js` (8 категорий, 34 позиции; RU/EN названия, базовые цены в рублях, флаги from/monthly/hourly, слаги и короткие коды).
- Layout: grid 1.5fr/.85fr. Слева категории: заголовок-кикер с нижней границей `--line2`, строки-чекбоксы (grid 20px/1fr/auto): квадратный чекбокс 18px (выбран — заливка `--accent`, галочка цветом `--bg`), название + срок, цена справа (JetBrains Mono, `--accent`).
- Справа sticky-панель итога: счётчик позиций, «ИТОГО, ОТ» + сумма (Space Grotesk ~2.4rem), опционально строки «плюс ежемесячно» и «комбо-скидка» (цвет `--ok`), кнопка «Отправить заказ в Telegram» → `https://t.me/sugarisbad_bot?start=calc-<коды>`, кнопка Calendly, примечание.
- Под списком — блок «Не нашли свою задачу?» с кнопкой «Написать в бот» (`?start=custom`).
- **Валюты**: RU — рубли как в pricing.js. EN — доллары: на клиенте fetch `https://www.cbr-xml-daily.ru/daily_json.js` → `Valute.USD.Value`; fallback 92 ₽/$; цена = `ceil(rub / rate / 5) * 5` (округление вверх до $5, минимум $5). Под hero — примечание «USD prices are pegged to the official CBR exchange rate · today $1 = XX.XX ₽».
- Комбо-скидки (в рублях): vps-setup+monitoring −2500; dockerize+compose+cicd −6000; ollama+ai-bot −7200; k8s-cluster+gitops −9000.

### Процесс (Work RU/EN)
H1 «Прозрачно, *по шагам*.» / «Transparent, *step by step*.». 5 шагов — строки (grid 120px/1fr/1fr/auto): крупный номер accent, заголовок, текст, бейдж результата «→ смета + roadmap» в рамке. Секция «Принципы» — 3 карточки (таблица gap 1px): / 01 Всё письменно, / 02 Инфраструктура как код, / 03 Ваши данные — ваши. CTA: Calendly (primary) + бот + калькулятор.

## Interactions & Behavior
- Hover строк/карточек: `background: var(--accent-dim)`, transition .25–.3s
- Hover вторичных кнопок: border-color/color → `--accent`
- Калькулятор: клик по строке — toggle; пересчёт мгновенный; кнопка отправки при 0 позиций — opacity .45 + pointer-events none, текст «Отметьте хотя бы одну позицию»
- Плавный скролл к #contact
- Появление hero-контента каскадом fadeup

## Responsive (≤920px)
- Многоколоночные grid'ы → 1 колонка (hero, услуги-строки, кейсы, калькулятор, шаги)
- Статистика 4 → 2 колонки
- В шапке скрываются ссылки разделов (остаются логотип, RU/EN, кнопка созвона); H1 ~2.4rem
- Sticky-панель калькулятора → static, под списком

## State Management
- Калькулятор: `selected: Record<slug, boolean>`; производные: count, total, monthly, comboDiscount, deep-link коды
- EN-услуги: `usdRate` (fetch ЦБ, fallback 92) + флаг live/fallback
- Остальное — статика

## Контакты и ссылки
- Email: **contact@opsmith.ru** (везде; старый dk0x@proton.me и ссылка на GitHub удалены)
- Telegram-бот: https://t.me/sugarisbad_bot (start-параметры: src-home, src-cases, src-work, custom, calc-<codes>; EN-варианты с суффиксом -en)
- Calendly: https://calendly.com/opsmith/30min
- Прямой Telegram-контакт (@sugarisbaddy) — удалён намеренно, не возвращать

## Assets
Внешних картинок нет. Шрифты — Google Fonts (Space Grotesk, Manrope, JetBrains Mono). Фон — код (SVG + CSS), не изображения.

## Files
- `Home RU.dc.html`, `Home EN.dc.html` — главные
- `Cases RU.dc.html`, `Cases EN.dc.html` — кейсы
- `Services RU.dc.html`, `Services EN.dc.html` — услуги + калькулятор
- `Work RU.dc.html`, `Work EN.dc.html` — процесс
- `pricing.js` — единый источник прайса (использовать как основу для `src/data/`)
