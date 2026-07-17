// Единый источник прайса (из design_handoff_opsmith/pricing.js).
// Базовые цены в рублях; EN-страница конвертирует в доллары по курсу ЦБ.
// Однобуквенные коды идут в payload deep-link'а бота:
// t.me/<bot>?start=calc-<коды> (макс. 64 символа [A-Za-z0-9_-]).
// Должны совпадать с CALC_ITEMS в bot/bot.py.

export const CBR_RATE_URL = 'https://www.cbr-xml-daily.ru/daily_json.js';
export const FALLBACK_USD_RATE = 92; // если API ЦБ недоступен

export type PriceItem = {
  slug: string;
  code: string;
  name_ru: string;
  name_en: string;
  time_ru: string;
  time_en: string;
  rub: number;
  from?: boolean;
  monthly?: boolean;
  hourly?: boolean;
};

export type PriceGroup = {
  title_ru: string;
  title_en: string;
  items: PriceItem[];
};

export const PRICING: PriceGroup[] = [
  { title_ru: 'Серверы и безопасность', title_en: 'Servers & security', items: [
    { slug: 'vps-setup', code: 'a', name_ru: 'Настройка VPS/VDS «под ключ»', name_en: 'Turnkey VPS/VDS setup', time_ru: '1–2 дня', time_en: '1–2 days', rub: 8400, from: true },
    { slug: 'audit', code: 'b', name_ru: 'Аудит сервера и безопасности', name_en: 'Server & security audit', time_ru: '1–2 часа', time_en: '1–2 hours', rub: 4800 },
    { slug: 'hardening', code: 'c', name_ru: 'Хардненинг: fail2ban, ufw, SSH, обновления', name_en: 'Hardening: fail2ban, ufw, SSH, patching', time_ru: '1 день', time_en: '1 day', rub: 7200, from: true },
    { slug: 'nginx-ssl', code: 'd', name_ru: 'nginx: домены, SSL, реверс-прокси', name_en: 'nginx: domains, SSL, reverse proxy', time_ru: '1 день', time_en: '1 day', rub: 6000, from: true },
    { slug: 'migration', code: 'e', name_ru: 'Миграция на новый сервер', name_en: 'Migration to a new server', time_ru: '1–3 дня', time_en: '1–3 days', rub: 14400, from: true },
    { slug: 'backup', code: 'f', name_ru: 'Автоматическое резервное копирование', name_en: 'Automated backups', time_ru: '1 день', time_en: '1 day', rub: 9600, from: true },
    { slug: 'mail', code: 'g', name_ru: 'Self-hosted почта: DKIM/SPF/DMARC', name_en: 'Self-hosted email: DKIM/SPF/DMARC', time_ru: '2–3 дня', time_en: '2–3 days', rub: 18000, from: true },
  ]},
  { title_ru: 'Docker и CI/CD', title_en: 'Docker & CI/CD', items: [
    { slug: 'dockerize', code: 'h', name_ru: 'Docker-изация приложения', name_en: 'Dockerize an application', time_ru: '1–2 дня', time_en: '1–2 days', rub: 12000, from: true },
    { slug: 'compose', code: 'i', name_ru: 'docker-compose стек (БД, кэш, очереди)', name_en: 'docker-compose stack (DB, cache, queues)', time_ru: '2–3 дня', time_en: '2–3 days', rub: 18000, from: true },
    { slug: 'cicd', code: 'j', name_ru: 'CI/CD пайплайн (GitLab CI / GitHub Actions)', name_en: 'CI/CD pipeline (GitLab CI / GitHub Actions)', time_ru: '2–4 дня', time_en: '2–4 days', rub: 18000, from: true },
    { slug: 'registry', code: 'k', name_ru: 'Приватный Docker Registry', name_en: 'Private Docker registry', time_ru: '1 день', time_en: '1 day', rub: 9600, from: true },
    { slug: 'iac', code: 'l', name_ru: 'Инфраструктура как код (Ansible / Terraform)', name_en: 'Infrastructure as code (Ansible / Terraform)', time_ru: 'от 1 недели', time_en: '1+ week', rub: 30000, from: true },
  ]},
  { title_ru: 'Kubernetes и оркестрация', title_en: 'Kubernetes & orchestration', items: [
    { slug: 'k8s-cluster', code: 'm', name_ru: 'Кластер Kubernetes под ключ (k3s / k8s)', name_en: 'Turnkey Kubernetes cluster (k3s / k8s)', time_ru: '1–2 недели', time_en: '1–2 weeks', rub: 48000, from: true },
    { slug: 'k8s-migrate', code: 'n', name_ru: 'Миграция приложений в Kubernetes', name_en: 'App migration to Kubernetes', time_ru: '1–2 недели', time_en: '1–2 weeks', rub: 36000, from: true },
    { slug: 'gitops', code: 'o', name_ru: 'Helm-чарты и GitOps (ArgoCD)', name_en: 'Helm charts & GitOps (ArgoCD)', time_ru: '3–5 дней', time_en: '3–5 days', rub: 24000, from: true },
    { slug: 'k8s-audit', code: 'p', name_ru: 'Аудит и оптимизация кластера', name_en: 'Cluster audit & optimization', time_ru: '2–3 дня', time_en: '2–3 days', rub: 14400, from: true },
  ]},
  { title_ru: 'Облака и миграции', title_en: 'Cloud & migrations', items: [
    { slug: 'cloud-migrate', code: 'q', name_ru: 'Миграция в облако / между облаками', name_en: 'Migration to / between clouds', time_ru: 'от 1 недели', time_en: '1+ week', rub: 24000, from: true },
    { slug: 'cost-opt', code: 'r', name_ru: 'Оптимизация облачных расходов', name_en: 'Cloud cost optimization', time_ru: '3–5 дней', time_en: '3–5 days', rub: 18000, from: true },
    { slug: 'multi-env', code: 's', name_ru: 'Стейджинг и дев-окружения', name_en: 'Staging & dev environments', time_ru: '2–4 дня', time_en: '2–4 days', rub: 14400, from: true },
  ]},
  { title_ru: 'Мониторинг и SRE', title_en: 'Monitoring & SRE', items: [
    { slug: 'monitoring', code: 't', name_ru: 'Мониторинг + алерты в Telegram', name_en: 'Monitoring + Telegram alerts', time_ru: '2–4 дня', time_en: '2–4 days', rub: 18000, from: true },
    { slug: 'logging', code: 'u', name_ru: 'Централизованные логи (Loki / ELK)', name_en: 'Centralized logging (Loki / ELK)', time_ru: '2–4 дня', time_en: '2–4 days', rub: 16800, from: true },
    { slug: 'balancer', code: 'v', name_ru: 'Балансировка нагрузки', name_en: 'Load balancing', time_ru: '3–5 дней', time_en: '3–5 days', rub: 21600, from: true },
    { slug: 'failover', code: 'w', name_ru: 'Автоматический failover', name_en: 'Automatic failover', time_ru: 'от 1 недели', time_en: '1+ week', rub: 36000, from: true },
    { slug: 'loadtest', code: 'x', name_ru: 'Нагрузочное тестирование', name_en: 'Load testing', time_ru: '2–3 дня', time_en: '2–3 days', rub: 14400, from: true },
  ]},
  { title_ru: 'Базы данных', title_en: 'Databases', items: [
    { slug: 'db-setup', code: 'y', name_ru: 'Установка и тюнинг PostgreSQL / MySQL', name_en: 'PostgreSQL / MySQL setup & tuning', time_ru: '1–2 дня', time_en: '1–2 days', rub: 12000, from: true },
    { slug: 'db-replica', code: 'z', name_ru: 'Репликация и бэкапы БД', name_en: 'DB replication & backups', time_ru: '2–4 дня', time_en: '2–4 days', rub: 18000, from: true },
    { slug: 'db-migrate', code: 'A', name_ru: 'Миграция БД без простоя', name_en: 'Zero-downtime DB migration', time_ru: '3–5 дней', time_en: '3–5 days', rub: 24000, from: true },
  ]},
  { title_ru: 'ИИ-инфраструктура', title_en: 'AI infrastructure', items: [
    { slug: 'ollama', code: 'B', name_ru: 'Self-hosted ИИ (Ollama)', name_en: 'Self-hosted AI (Ollama)', time_ru: '2–4 дня', time_en: '2–4 days', rub: 24000, from: true },
    { slug: 'ai-bot', code: 'C', name_ru: 'ИИ-агент / Telegram-бот', name_en: 'AI agent / Telegram bot', time_ru: '1–2 недели', time_en: '1–2 weeks', rub: 48000, from: true },
    { slug: 'turnkey', code: 'D', name_ru: 'Система под ключ', name_en: 'Turnkey system', time_ru: 'от 3 недель', time_en: '3+ weeks', rub: 192000, from: true },
  ]},
  { title_ru: 'Поддержка', title_en: 'Support', items: [
    { slug: 'subscription', code: 'E', name_ru: 'Абонентское администрирование', name_en: 'Retainer administration', time_ru: 'постоянно', time_en: 'ongoing', rub: 12000, from: true, monthly: true },
    { slug: 'consult', code: 'F', name_ru: 'Разовая консультация', name_en: 'One-off consultation', time_ru: 'по записи', time_en: 'by appointment', rub: 4800 },
    { slug: 'incident', code: 'G', name_ru: 'Срочное реагирование на инцидент', name_en: 'Urgent incident response', time_ru: 'сегодня', time_en: 'today', rub: 7200, from: true },
    { slug: 'hourly', code: 'H', name_ru: 'Часовая ставка инженера', name_en: 'Engineer hourly rate', time_ru: 'гибко', time_en: 'flexible', rub: 3600, from: true, hourly: true },
  ]},
];

// Комбо-скидки (в рублях): применяются автоматически, когда все позиции
// связки отмечены; несколько связок в одном заказе суммируются.
// Составы и суммы должны совпадать с CALC_BUNDLES в bot/bot.py.
export const BUNDLES: { req: string[]; save: number }[] = [
  { req: ['vps-setup', 'monitoring'], save: 2500 },
  { req: ['dockerize', 'compose', 'cicd'], save: 6000 },
  { req: ['ollama', 'ai-bot'], save: 7200 },
  { req: ['k8s-cluster', 'gitops'], save: 9000 },
  { req: ['vps-setup', 'nginx-ssl', 'hardening', 'backup'], save: 4500 },
  { req: ['migration', 'backup'], save: 2400 },
  { req: ['db-setup', 'db-replica'], save: 3000 },
  { req: ['monitoring', 'logging'], save: 3500 },
  { req: ['balancer', 'failover'], save: 5000 },
  { req: ['monitoring', 'failover'], save: 4000 },
  { req: ['cicd', 'registry'], save: 2500 },
];

// Готовые пакеты: одним кликом отмечают набор позиций в калькуляторе.
// Цена пакета = сумма позиций минус комбо-скидки, которые собираются внутри
// набора, — считается на месте из PRICING и BUNDLES (отдельных цен нет).
export type Package = {
  slug: string;
  name_ru: string;
  name_en: string;
  desc_ru: string;
  desc_en: string;
  items: string[];
};

export const PACKAGES: Package[] = [
  {
    slug: 'start',
    name_ru: 'Старт',
    name_en: 'Start',
    desc_ru: 'Сервер под ключ: настройка, домены и SSL, защита, бэкапы.',
    desc_en: 'Turnkey server: setup, domains & SSL, hardening, backups.',
    items: ['vps-setup', 'nginx-ssl', 'hardening', 'backup'],
  },
  {
    slug: 'production',
    name_ru: 'Продакшен',
    name_en: 'Production',
    desc_ru: 'Приложение в проде: сервер, контейнеры, автодеплой и мониторинг.',
    desc_en: 'App in production: server, containers, auto-deploy and monitoring.',
    items: ['vps-setup', 'dockerize', 'compose', 'cicd', 'monitoring'],
  },
  {
    slug: 'scale',
    name_ru: 'Масштаб',
    name_en: 'Scale',
    desc_ru: 'Кластер Kubernetes с GitOps, мониторингом и автоматическим failover.',
    desc_en: 'Kubernetes cluster with GitOps, monitoring and automatic failover.',
    items: ['k8s-cluster', 'gitops', 'monitoring', 'failover'],
  },
];
