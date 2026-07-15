// Английский словарь. Структура — как у ru (тип Dict).
// Тексты страниц — из дизайн-референсов design_handoff_opsmith (EN-версии).

import type { Dict, Locale, ServiceRow, CasePreview, CaseItem, Step, Principle } from './ru';

export const en: Dict = {
  code: 'en' as Locale,
  htmlLang: 'en',
  ogLocale: 'en_US',

  seo: {
    siteName: 'OPSMITH — DevOps studio: servers, CI/CD, automation, self-hosted AI',
    personName: 'Danila',
    jobTitle: 'DevOps Engineer',
    ogImageAlt: 'OPSMITH — DevOps studio: servers, CI/CD, automation, self-hosted AI',
  },

  nav: {
    home: 'Home',
    cases: 'Case studies',
    services: 'Services & pricing',
    work: 'Process',
    contact: 'Contact',
    call: 'Book a call',
    langLabel: 'Language',
  },

  footer: {
    tagline: 'devops · automation · self-hosted ai',
  },

  home: {
    title: 'OPSMITH — DevOps studio: VPS setup, Docker, CI/CD, turnkey automation',
    desc: 'OPSMITH — infrastructure engineering: turnkey Linux server (VPS/VDS) setup, Kubernetes, CI/CD, monitoring and resilience, self-hosted AI (Ollama). Remote, quotes fixed in writing.',
    kicker: 'DEVOPS · INFRASTRUCTURE · AI',
    h1: 'Infrastructure engineering for companies that <em>cannot go down</em>.',
    sub: 'Servers, Kubernetes, CI/CD, monitoring and self-hosted AI — designed, documented and delivered turnkey. Your customers never notice a failure.',
    ctaDiscuss: 'Discuss a project',
    ctaCases: 'Case studies →',
    status: {
      head: '// production',
      rows: [
        { name: 'api-cluster', value: '● healthy', tone: 'ok' },
        { name: 'db-primary', value: '● healthy', tone: 'ok' },
        { name: 'ai-inference', value: '● healthy', tone: 'ok' },
        { name: 'ci/cd pipeline', value: '● passing', tone: 'ok' },
        { name: 'failover', value: 'standby', tone: 'accent' },
      ],
      foot: [
        { name: 'uptime / 2025', value: '99.98%' },
        { name: 'incident-free', value: '214 days' },
      ],
    },
    stats: [
      { value: '<60 sec', label: 'from one command to a ready server', accent: true },
      { value: '24/7', label: 'monitoring and automatic failover' },
      { value: '10', label: 'services in a production GPU rental platform' },
      { value: '$0', label: 'in token bills — self-hosted AI on your hardware' },
    ],
    servicesKicker: 'SERVICES',
    servicesH2: 'DevOps as the foundation.<br /><em>AI as the multiplier.</em>',
    servicesLead: 'We design and build infrastructure end to end — servers, containers, deployment, monitoring — as one coherent system, not a pile of scripts.',
    services: [
      { num: '01', title: 'VPS / Linux setup & hardening', text: 'Turnkey servers: nginx, systemd, firewall, SSH hardening, health checks. Everything via cloud-init — no manual tweaks in production.' },
      { num: '02', title: 'Docker & containerization', text: 'Compose stacks with databases, caches and queues, multi-stage builds, private registries. One file — the project runs anywhere.' },
      { num: '03', title: 'CI/CD & auto-deploy', text: 'Push to main — tests, build, deploy. Staging, rollbacks, secrets. Releases stop being an event.' },
      { num: '04', title: 'Monitoring & resilience', text: 'Metrics, logs, Telegram alerts. Monitoring catches a failure — the system switches to standby on its own.' },
      { num: '05', title: 'Telegram bots & notifications', text: 'Lead intake, server health alerts, task management from the chat. Your whole infrastructure — in your Telegram.' },
      { num: '06', title: 'Self-hosted AI', text: 'Your own neural network on your hardware via Ollama: no data leaks, no token bills. A ready HTTP API.' },
    ] as ServiceRow[],
    btnPrices: 'Pricing & calculator',
    btnWork: 'How we work →',
    casesKicker: 'SELECTED WORK',
    casesH2: 'Running in production<br />right now',
    casesAll: 'All case studies →',
    casesPreview: [
      { value: '10', title: 'GPU rental platform', text: 'Node onboarding, job orchestration, metering and billing — ten services acting as one.' },
      { value: '~1 min', title: 'A website that repairs itself', text: 'Complete server loss → new VPS, full stack and AI-generated content — no humans involved.' },
      { value: '24/7', title: 'Hardware under watch', text: 'Dozens of devices under constant checks — we learn of failures before customers do.' },
    ] as CasePreview[],
  },

  contact: {
    kicker: 'CONTACT',
    h2: 'Describe the task — we reply with a solution <em>within a day</em>.',
    text: 'Two sentences are enough. The initial consultation is free and non-binding.',
    btnBot: 'Leave a request via bot',
    btnCall: 'Book a 30-min call',
  },

  casesPage: {
    title: 'DevOps case studies: infrastructure automation, 24/7 monitoring, self-hosted AI — OPSMITH',
    desc: 'Infrastructure automation examples: a GPU rental platform, a self-healing website, 24/7 hardware monitoring. Real production systems — from architecture to monitoring.',
    kicker: 'CASE STUDIES',
    h1: 'Systems that run <em>without us</em>.',
    sub: 'Not demos or pet projects — real platforms in production. What it was, what we built, what it delivered.',
    problemLabel: 'Problem.',
    solutionLabel: 'Solution.',
    items: [
      {
        num: 'case_01',
        badge: 'GPU · PLATFORM',
        title: 'GPU rental marketplace',
        problem: 'The client needed a platform that connects third-party GPU machines, hands them to customers for workloads, and takes over all accounting and billing.',
        solution: 'A system of 10 services: node registration, job orchestration, usage metering, automatic billing and a control panel. All containerized, with monitoring and self-recovery.',
        stack: ['Docker', 'docker-compose', 'Python', 'FastAPI', 'PostgreSQL', 'Grafana', 'nginx'],
        metrics: [
          { value: '10', label: 'services acting as one' },
          { value: '24/7', label: 'monitoring of nodes and jobs' },
          { value: 'auto', label: 'billing and GPU-hour metering' },
        ],
      },
      {
        num: 'case_02',
        badge: 'SELF-HEALING',
        title: 'A website that repairs itself',
        problem: 'A stretch goal: the site had to survive complete loss of its server with zero human involvement.',
        solution: 'Monitoring detects the outage → a script rents a new VPS → cloud-init provisions the stack → a neural network fills the site with content → traffic switches over. The whole cycle takes about a minute.',
        stack: ['Bash', 'cloud-init', 'Ollama', 'nginx', 'Python', 'systemd'],
        metrics: [
          { value: '~1 min', label: 'from outage to a new server' },
          { value: '0', label: 'manual steps during failure' },
          { value: 'AI', label: 'content generated on the fly' },
        ],
      },
      {
        num: 'case_03',
        badge: 'MONITORING',
        title: 'Round-the-clock hardware watch',
        problem: 'Dozens of physical devices across locations — issues had to surface before customers noticed.',
        solution: 'A single health-check system with metrics and logs, Telegram alerts with severity levels. The on-call sees the problem in chat and reacts by runbook — often before any complaint.',
        stack: ['VictoriaMetrics', 'Grafana', 'Telegram Bot', 'Python', 'systemd'],
        metrics: [
          { value: '24/7', label: 'continuous device monitoring' },
          { value: 'dozens', label: 'of devices under watch' },
          { value: 'first', label: 'we learn of failures before clients' },
        ],
      },
    ] as CaseItem[],
    ctaH2: 'Need this kind of <em>reliability</em>?',
    ctaText: "Tell us what hurts in your infrastructure — we'll propose a solution and estimate within a day.",
    ctaBot: 'Discuss a project',
    ctaCall: 'Book a call',
    ctaServices: 'Services & pricing →',
  },

  servicesPage: {
    title: 'DevOps services & pricing: server setup, CI/CD, monitoring, self-hosted AI — OPSMITH',
    desc: 'Full DevOps price list: turnkey VPS/VDS setup, Docker & CI/CD, Kubernetes, monitoring, databases, self-hosted AI (Ollama). Order calculator, quotes fixed in writing.',
    kicker: 'SERVICES & PRICING',
    h1: 'Full price list. Build your order <em>in a minute</em>.',
    sub: "Tick the work you need — the calculator estimates a starting price and sends the order to our Telegram bot. We fix an exact quote in writing after a short call, and it won't grow. Don't see your task — message the bot and we'll quote it individually.",
    rateNote: 'USD prices are pegged to the official CBR exchange rate',
    rateNoteFallback: 'Live exchange rate unavailable — using a recent reference rate.',
    calc: {
      countLabel: 'Items in order:',
      totalLabel: 'TOTAL, FROM',
      monthlyLabel: 'plus monthly, from',
      comboLabel: 'bundle discount',
      btnSend: 'Send order to Telegram',
      btnEmpty: 'Select at least one item',
      btnCall: 'Book a 30-min call',
      note: 'Hourly items are priced for 1 hour. The bundle discount appears automatically once a related set of work is in the order.',
      fromPrefix: 'from ',
      monthlySuffix: '/mo',
      hourlySuffix: '/hr',
    },
    custom: {
      title: "Don't see your task?",
      text: "Describe it in the bot — we'll return with a quote within a day.",
      btn: 'Message the bot →',
    },
  },

  workPage: {
    title: 'How we work: a transparent step-by-step process, quote & roadmap — OPSMITH',
    desc: 'A transparent DevOps studio process: call & brief, audit & plan, implementation, verification & handover, support. Everything in writing, infrastructure as code, access stays with you.',
    kicker: 'PROCESS',
    h1: 'Transparent, <em>step by step</em>.',
    sub: 'No "we\'ll just tweak something over there." Every stage has a clear deliverable you can verify. We work remotely and put everything in writing.',
    steps: [
      { num: '01', title: 'Call & brief', text: 'We listen to the task and the current state: what the project is, where it lives, what hurts. Precise questions, no guessing later.', output: 'shared understanding' },
      { num: '02', title: 'Audit & plan', text: 'We examine the infrastructure, find bottlenecks and risks. We return with a work plan, timelines and a fixed quote.', output: 'quote + roadmap' },
      { num: '03', title: 'Implementation', text: 'We provision and configure: servers, containers, CI/CD, monitoring. Everything reproducible from code.', output: 'working system' },
      { num: '04', title: 'Verification & handover', text: 'Load tests, failover and alert checks, documentation and access handover.', output: 'docs + access' },
      { num: '05', title: 'Support', text: 'Optional retainer administration: we monitor, update and respond to incidents.', output: 'under watch' },
    ] as Step[],
    principlesKicker: 'PRINCIPLES',
    principles: [
      { num: '/ 01', title: 'Everything in writing', text: "Quote, timelines, scope — all fixed. The price doesn't grow along the way." },
      { num: '/ 02', title: 'Infrastructure as code', text: 'No manual SSH tweaks in production. Everything reproduces from the repository.' },
      { num: '/ 03', title: 'Your data is yours', text: 'Self-hosted solutions, access stays with you. No lock-in.' },
    ] as Principle[],
    ctaH2: 'Start with a <em>free call</em>?',
    ctaText: "We'll discuss the task, scope the work and rough out timelines. No commitment.",
    ctaBot: 'Message the bot',
    ctaCall: 'Book a 30-min call',
    ctaCalc: 'Build an order →',
  },

  notFound: {
    title: 'Page not found',
    text: "This page doesn't exist. The link may be outdated.",
    btnHome: 'Back home',
  },
};
