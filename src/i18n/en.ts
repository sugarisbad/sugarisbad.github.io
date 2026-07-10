// English dictionary. Prices lead with USD for international clients.
import type { Dict } from './ru';

export const en: Dict = {
  code: 'en',
  htmlLang: 'en',
  ogLocale: 'en_US',

  seo: {
    siteName: 'Danila (sugarisbad) — DevOps engineer',
    personName: 'Danila',
    jobTitle: 'DevOps engineer',
    ogImageAlt: 'Danila — DevOps engineer: servers, CI/CD, automation, self-hosted AI',
  },

  nav: {
    home: 'Home',
    cases: 'Case studies',
    services: 'Services & pricing',
    work: 'How I work',
    contact: 'Contact',
    menu: 'Menu',
  },

  footerTagline: 'DevOps · automation · self-hosted AI',

  contact: {
    title: 'Let’s discuss your project',
    text: 'Describe your task in a couple of sentences — I’ll get back to you with a solution and an estimate within a day. The initial consultation is free and non-binding.',
    btnBot: '🤖 Leave a request via bot',
    btnMail: '✉ Email',
    mailSubject: 'DevOps project',
  },

  home: {
    title: 'Danila (sugarisbad) — DevOps engineer: servers, CI/CD, automation',
    desc: 'DevOps engineer: VPS setup and hardening, Docker, CI/CD, monitoring and high availability. Self-hosted AI (Ollama) and Telegram bots. Turnkey projects and managed server administration.',
    badge: 'Accepting projects · reply within a day',
    h1: '<span class="grad-text">DevOps</span> engineer<br />for your infrastructure',
    sub: 'Servers, Docker, CI/CD, monitoring and failover. You get a system that watches over itself and heals itself — not yet another contractor you have to chase about every little thing.',
    ctaDiscuss: 'Discuss your task →',
    ctaCases: 'View case studies',
    servicesEyebrow: '// what I do',
    servicesH2: 'DevOps as the foundation,<br />AI as the multiplier',
    servicesLead: 'I design and build infrastructure end to end: servers, containers, deployment, monitoring — as a single system.',
    btnPrices: 'Pricing & full price list →',
    btnWork: 'How I work →',
  },

  casesPage: {
    title: 'Case studies — Danila (sugarisbad), DevOps engineer',
    desc: 'Case studies: a GPU rental platform, a self-healing website, 24/7 hardware monitoring, load-balanced server fleets. Real systems built end to end by one engineer.',
    eyebrow: '// real projects',
    h1: 'Case studies',
    sub: 'Systems I designed and built end to end. Described in plain words — I’m happy to share the technical details on a call.',
    stackEyebrow: '// tools',
    stackH2: 'Technology stack',
    stackLead: 'What I work with every day — from system administration to integrating neural networks.',
    marqueeAria: 'Technologies',
    contactTitle: 'Want a system like this?',
    contactText: 'Tell me what your project needs — I’ll propose a solution and an estimate within a day.',
  },

  servicesPage: {
    title: 'Services & pricing — Danila (sugarisbad), DevOps engineer',
    desc: 'DevOps engineer services and pricing: VPS setup from $80, monitoring from $170, self-hosted AI from $230, turnkey systems. Written fixed quotes, prepayment-based workflow.',
    badge: 'Written fixed quote · prepayment-based workflow',
    h1: 'Services & <span class="grad-text">pricing</span>',
    sub: 'Standard packages and a full price list. All “from …” prices are starting points: I’ll give you an exact quote after a short call, and it won’t grow along the way. I work on prepayment — usually 50% upfront, the rest after you see the result.',
    plansEyebrow: '// packages',
    plansH2: 'Where people usually start',
    priceNote1: '<b>Managed administration</b> — from $115/mo: monitoring, updates, incident response, small fixes. &nbsp;·&nbsp; One-off consultation — $45/hour.',
    listEyebrow: '// full price list',
    listH2: 'Typical tasks',
    orderBtn: 'Order',
    priceNote2: 'Hourly rate — <b>$45/hour</b>. Combining several services is cheaper than ordering them separately: I merge the work and never charge twice for the same thing. Work starts after prepayment — 50/50 on small tasks.',
    contactTitle: 'Didn’t find your task?',
    contactText: 'The price list covers typical work, but most projects are a combination of items. Describe your task in your own words — I’ll turn it into a quote with a price and timeline within a day.',
  },

  workPage: {
    title: 'How I work — Danila (sugarisbad), DevOps engineer',
    desc: 'How I work: a written quote and prepayment, fixed pricing, 30 days of free support after delivery, all access and accounts belong to you. Answers to frequently asked questions.',
    eyebrow: '// process & terms',
    h1: 'How I work',
    sub: 'A transparent process with no surprises: a written quote before we start, prepayment-based workflow, and a month of free support after delivery.',
    processEyebrow: '// four steps',
    processH2: 'A process without surprises',
    guaranteesEyebrow: '// why it’s safe to work with me',
    guaranteesH2: 'Guarantees, not promises',
    guaranteesLead: 'The biggest fears when hiring a freelancer: “they’ll vanish”, “it’ll get more expensive”, “they’ll keep the access”. I close all of them before we start — in writing.',
    compareEyebrow: '// engagement formats',
    compareH2: 'Why working with an engineer directly pays off',
    compareLead: 'You could hand the same tasks to an agency or hire a full-time sysadmin. Here’s an honest comparison.',
    faqEyebrow: '// questions',
    faqH2: 'Frequently asked questions',
  },

  notFound: {
    title: 'Page not found',
    text: 'This page doesn’t exist. The link may be outdated.',
    btnHome: 'Back to home',
  },

  heroStats: [
    { value: '<60s', label: 'from one command to a ready server' },
    { value: '24/7', label: 'auto-monitoring and failover to standby' },
    { value: '10', label: 'services in a production GPU rental platform' },
    { value: '$0', label: 'in token bills — self-hosted AI on your hardware' },
  ],

  services: [
    {
      icon: '🛡️',
      title: 'VPS setup and hardening',
      text: 'I deploy servers turnkey: nginx, systemd services, firewall, SSH hardening, autostart and health checks. No manual SSH in production — everything via cloud-init.',
      tags: ['nginx', 'systemd', 'cloud-init', 'ufw', "Let's Encrypt"],
    },
    {
      icon: '🐳',
      title: 'Docker and containerization',
      text: 'I move applications into containers: docker-compose stacks with databases, caches and queues, multi-stage builds, private registries. One file — and the project runs anywhere.',
      tags: ['Docker', 'docker-compose', 'multi-stage', 'registry'],
    },
    {
      icon: '🚀',
      title: 'CI/CD and auto-deploy',
      text: 'GitLab CI / GitHub Actions pipelines: tests, build, deploy to the server on every push to main. Staging, rollbacks, secrets — releases stop being an event.',
      tags: ['GitLab CI', 'GitHub Actions', 'rollback', 'staging'],
    },
    {
      icon: '📈',
      title: 'Monitoring and alerts',
      text: 'Metrics, logs and health checks with Telegram alerts: you learn about problems before your customers do. Self-healing: monitoring catches a failure — the system switches to standby on its own.',
      tags: ['VictoriaMetrics', 'Grafana', 'health-check', 'failover'],
    },
    {
      icon: '🤖',
      title: 'Telegram bots and notifications',
      text: 'Bots that do real work: lead intake, server health alerts, statuses and task management right from the chat. Everything happening in your infrastructure — in your Telegram.',
      tags: ['Telegram Bot', 'Python', 'TypeScript', 'alerts'],
    },
    {
      icon: '🧠',
      title: 'Self-hosted AI',
      text: 'Your own neural network on your hardware via Ollama: no data leaks and no token bills. I pick a model for your task and hardware, and hand over a ready HTTP API for your services.',
      tags: ['Ollama', 'Gemma', 'llama.cpp', 'REST API'],
    },
  ],

  cases: [
    {
      icon: '🖥️',
      title: 'GPU rental marketplace',
      text: 'A service where owners of powerful machines rent them out. The platform connects machines on its own, runs client workloads, meters usage and issues invoices. Under the hood — ten independent services working as one.',
      tags: ['Go', 'Kafka', 'Docker', 'Postgres'],
      stat: { value: '10', label: 'services working as one' },
    },
    {
      icon: '⚙️',
      title: 'Server supervisor agent',
      text: 'A small program is installed on a GPU server and takes it under control: starts and stops client workloads, watches hardware health and keeps tasks from interfering with each other.',
      tags: ['Go', 'gRPC', 'Docker', 'Linux'],
      stat: { value: '1', label: 'program — the whole server under control' },
    },
    {
      icon: '🌐',
      title: 'Server fleet with smart load distribution',
      text: 'A system of dozens of servers that spreads incoming traffic between them. If one server is overloaded or goes down — traffic automatically shifts to healthy ones. A new server joins the fleet with a single script.',
      tags: ['HAProxy', 'load balancing', 'web panel'],
      stat: { value: '10+', label: 'servers configured with one script' },
    },
    {
      icon: '📡',
      title: 'Round-the-clock hardware watch',
      text: 'The system regularly checks the health of dozens of devices across servers and sends a Telegram message the moment something needs attention. The owner learns about problems before their customers do.',
      tags: ['monitoring', 'Telegram', 'web dashboard'],
      stat: { value: '24/7', label: 'you learn about problems first' },
    },
    {
      icon: '🐧',
      title: 'A ready server with one command',
      text: 'A script turns a clean server into a fully configured system in minutes: installs everything needed, enables protection and outputs ready-to-use connection details. No manual work — and therefore no mistakes.',
      tags: ['Docker', 'Linux', 'automation'],
      stat: { value: '1 command', label: 'from an empty server to a working one' },
    },
    {
      icon: '🔁',
      title: 'A website that repairs itself',
      text: 'The system watches the website around the clock. If it goes down — within a minute it rents a new server, fills it with AI-generated content and switches visitors over. All without human involvement.',
      tags: ['AI', 'auto-recovery', 'GitLab'],
      stat: { value: '~1 min', label: 'from failure to a working site' },
    },
  ],

  stack: [
    'Linux', 'nginx', 'systemd', 'cloud-init', 'Python / asyncio', 'FastAPI',
    'TypeScript', 'Bash', 'Ollama', 'Gemma / Llama', 'OpenClaw', 'Telegram Bot API',
    'GitLab CI/CD', 'Cloudflare API', 'TimeWeb Cloud', 'SQLite / SQLAlchemy',
    'JWT / bcrypt', 'Vue / Vite', "Let's Encrypt", 'pytest',
  ],

  plans: [
    {
      slug: 'plan-vps',
      title: 'VPS setup',
      desc: 'A turnkey server: deployed, hardened, with automated startup.',
      price: 'from $80',
      meta: '≈ 7,000 ₽ · 1–2 days',
      featured: true,
      cta: 'Order',
      features: [
        'nginx + SSL (Let’s Encrypt)',
        'SSH hardening and firewall',
        'systemd service autostart',
        'Monitoring and health checks',
        'Access documentation',
      ],
    },
    {
      slug: 'plan-monitoring',
      title: 'Monitoring and alerts',
      desc: 'Learn about problems before your customers do — via a Telegram message.',
      price: 'from $170',
      meta: '≈ 15,000 ₽ · 2–4 days',
      cta: 'Order',
      features: [
        'Server and application metrics',
        'Health checks for your services',
        'Instant Telegram alerts',
        'Incident history',
        'Option: automatic failover to standby',
      ],
    },
    {
      slug: 'plan-ai',
      title: 'Self-hosted AI',
      desc: 'Your own neural network on your hardware — no token bills, no data leaks.',
      price: 'from $230',
      meta: '≈ 20,000 ₽ · 2–4 days',
      cta: 'Order',
      features: [
        'Ollama setup + model selection',
        'Optimization for your hardware',
        'HTTP API for your services',
        'Quantization for speed/memory',
        'Replacing paid APIs (OpenAI etc.)',
      ],
    },
    {
      slug: 'plan-system',
      title: 'Turnkey system',
      desc: 'End-to-end automation: monitoring, failover, CI/CD, cloud APIs.',
      price: 'from $1,850',
      meta: '≈ 160,000 ₽ · from 3 weeks',
      cta: 'Discuss',
      features: [
        'Architecture design',
        'High availability and auto-recovery',
        'Cloud provider integrations',
        'CI/CD and automatic deployment',
        'Tests, documentation, support',
      ],
    },
  ],

  process: [
    { title: 'Call', text: 'We go through the task, I ask the right questions and propose a solution.' },
    { title: 'Quote and prepayment', text: 'I fix the scope, price and timeline in writing. Work starts after prepayment.' },
    { title: 'Work', text: 'I build the system, keep you posted and show intermediate results.' },
    { title: 'Handover', text: 'Documentation, access, instructions. Everything works and is easy to maintain.' },
  ],

  guarantees: [
    {
      icon: '📄',
      title: 'The price is fixed before we start',
      text: 'Scope, cost and timeline — in writing, before work begins. “Turned out to be more expensive along the way” is not my style.',
    },
    {
      icon: '🔑',
      title: 'Everything belongs to you',
      text: 'Code, servers, domains, access and documentation — on your accounts. Switch contractors at any moment without pain.',
    },
    {
      icon: '🛠️',
      title: '30 days of free support',
      text: 'For a month after delivery, fixes and consultations on the delivered work are included in the price. If it breaks — I fix it without counting hours.',
    },
    {
      icon: '⚡',
      title: 'Reply within a day',
      text: 'You write on Telegram — you get an answer from an engineer, not a manager. No “I’ll pass it to the team, we’ll get back next week”.',
    },
  ],

  compare: {
    columns: ['', 'Me', 'Agency', 'Full-time sysadmin'],
    rows: [
      ['Work starts', 'tomorrow', '1–2 weeks of approvals', '1–2 months of hiring'],
      ['Entry budget', 'from $80 per task', 'from $1,200 + management', 'from $1,700/mo + taxes'],
      ['Communication', 'directly with the engineer', 'through a manager', 'you still have to find one'],
      ['Automation and self-hosted AI', 'core specialty', 'depends on the team', 'rarely'],
      ['When there are no tasks', 'you pay nothing', '—', 'the salary keeps running'],
    ],
  },

  faq: [
    {
      q: 'How much will it really cost?',
      a: 'Exactly what the quote says. All prices on the site are “from” starting points, but the exact amount is fixed in writing before work starts and doesn’t grow along the way. If you decide to expand the scope during the project — we discuss and fix it separately.',
    },
    {
      q: 'I already have a server, but it’s configured “somehow”. Will you take it on?',
      a: 'Yes, that’s a common case. I’ll start with an audit: review what’s deployed, find security holes and single points of failure, and give you a cleanup plan with prices. The audit is billed hourly and usually takes 1–2 hours.',
    },
    {
      q: 'Can self-hosted AI really replace paid APIs?',
      a: 'For most practical tasks — yes: classification, text generation, command parsing, summarization. A local model on your hardware doesn’t send data anywhere and doesn’t bill you for tokens. For “maximum intelligence required” tasks I’ll tell you honestly where a local model won’t be enough.',
    },
    {
      q: 'What happens if something breaks after delivery?',
      a: 'For 30 days after delivery, fixes to the delivered work are free. After that — either one-off requests at the hourly rate, or managed administration from $115/mo where I watch the system myself.',
    },
    {
      q: 'How does payment work?',
      a: 'I work on prepayment, stage by stage: we fix a stage — prepayment — result — next stage. On small tasks it’s usually 50% upfront / 50% after a demo of the result. I work officially; we’ll discuss the details on a call.',
    },
  ],

  priceGroups: [
    {
      title: 'Servers and security',
      icon: '🛡️',
      items: [
        { slug: 'vps-setup', name: 'Turnkey VPS setup', desc: 'nginx + SSL, firewall, SSH hardening, systemd autostart, health checks, documentation', price: 'from $80', time: '1–2 days' },
        { slug: 'audit', name: 'Audit of an existing server', desc: 'Security and failure-point review, a written report with a fix plan and prices', price: '$45', time: '1–2 hours' },
        { slug: 'nginx-ssl', name: 'nginx: domains, SSL, reverse proxy', desc: 'Virtual hosts, Let’s Encrypt with auto-renewal, redirects, gzip/brotli, caching', price: 'from $60', time: '1 day' },
        { slug: 'migration', name: 'Migration to a new server', desc: 'Moving applications, databases and domains with zero downtime, verification and a rollback plan', price: 'from $140', time: '1–3 days' },
        { slug: 'backup', name: 'Backups', desc: 'Automatic database and file backups to external storage, restore verification', price: 'from $90', time: '1 day' },
      ],
    },
    {
      title: 'Docker and CI/CD',
      icon: '🐳',
      items: [
        { slug: 'dockerize', name: 'Dockerizing an application', desc: 'Dockerfile with multi-stage build, image size optimization, .dockerignore, documentation', price: 'from $115', time: '1–2 days' },
        { slug: 'compose', name: 'docker-compose stack', desc: 'App + database + cache + queue in one compose: networks, volumes, health checks, limits', price: 'from $170', time: '2–3 days' },
        { slug: 'cicd', name: 'CI/CD pipeline', desc: 'GitLab CI / GitHub Actions: tests → build → deploy on push, secrets, staging, rollbacks', price: 'from $170', time: '2–4 days' },
        { slug: 'mass-deploy', name: 'Mass deployment', desc: 'Scripts to roll out an identical configuration to a fleet of servers: cloud-init, idempotent steps', price: 'from $290', time: 'from 1 week' },
      ],
    },
    {
      title: 'Monitoring and high availability',
      icon: '📈',
      items: [
        { slug: 'monitoring', name: 'Monitoring + Telegram alerts', desc: 'Server and application metrics, health checks, instant incident notifications', price: 'from $170', time: '2–4 days' },
        { slug: 'balancer', name: 'Load balancing', desc: 'HAProxy / nginx upstream: traffic distribution, health checks, graceful switchover', price: 'from $210', time: '3–5 days' },
        { slug: 'failover', name: 'Automatic failover', desc: 'A standby environment + automatic switchover when the primary fails, failure scenario testing', price: 'from $345', time: 'from 1 week' },
      ],
    },
    {
      title: 'AI infrastructure',
      icon: '🧠',
      items: [
        { slug: 'ollama', name: 'Self-hosted AI (Ollama)', desc: 'Model selection for your hardware, quantization, HTTP API for your services, replacing paid APIs', price: 'from $230', time: '2–4 days' },
        { slug: 'tg-bot', name: 'AI agent / Telegram bot', desc: 'A bot with LLM parsing of free-form commands, notifications, integration with your API, deployment', price: 'from $460', time: '1–2 weeks' },
        { slug: 'turnkey', name: 'Turnkey system', desc: 'Architecture, high availability, CI/CD, cloud API integrations, tests and documentation', price: 'from $1,850', time: 'from 3 weeks' },
      ],
    },
    {
      title: 'Support',
      icon: '🤝',
      items: [
        { slug: 'subscription', name: 'Managed administration', desc: 'Monitoring, updates, incident response, small fixes — your server under supervision', price: 'from $115/mo', time: 'ongoing' },
        { slug: 'consult', name: 'One-off consultation', desc: 'A call: review of your infrastructure, answers to questions, an action plan', price: '$45/hour', time: 'by appointment' },
        { slug: 'incident', name: 'Emergency incident response', desc: 'Your server is down right now — I connect, diagnose, bring it back up and write a post-mortem', price: 'from $70', time: 'today' },
      ],
    },
  ],
};
