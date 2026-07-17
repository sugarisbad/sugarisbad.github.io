---
title: 'Failover without Kubernetes: when k8s is overkill'
titleHtml: 'Failover without Kubernetes: when k8s is <em>overkill</em>'
description: 'docker compose + healthchecks + a standby server: 99.9% uptime with no cluster. Kubernetes solves problems of a scale most projects never reach.'
pubDate: 2026-04-19
cat: docker
tags: [docker, failover]
minutes: 6
ctaTitle: 'Want to survive <em>a dead server</em>?'
ctaText: "We'll design failover for your budget: from healthcheck-driven restarts to automatic switchover to a standby server."
---

## The honest question: what can you survive already

99.9% availability is 43 minutes of downtime per month. That level is reachable with a single server, correct restarts and fast recovery from code. Kubernetes earns its keep when you have dozens of services, dozens of deploys a day and a team ready to feed the cluster itself. For 2–5 services on one VPS, k8s adds more failure modes than it removes.

## Level 1: containers heal themselves

Most incidents are not "the server burned down" but "a process hung". A couple of compose lines cover this: a healthcheck catches the hang, `restart: always` revives crashes, autoheal restarts whatever went unhealthy.

```yaml
services:
  app:
    image: registry.example.com/app:latest
    restart: always
    healthcheck:
      test: ['CMD', 'curl', '-sf', 'http://localhost:8000/health']
      interval: 15s
      retries: 3
      start_period: 30s
  autoheal:
    image: willfarrell/autoheal:latest
    restart: always
    environment: { AUTOHEAL_CONTAINER_LABEL: all }
    volumes: ['/var/run/docker.sock:/var/run/docker.sock']
```

<div class="practice"><span>FROM PRACTICE</span>The <code>/health</code> endpoint must check dependencies (database, cache), not just return 200. Otherwise the healthcheck is green while the app serves 500s — a classic in "monitoring said nothing" post-mortems.</div>

## Level 2: a standby server and switchover

Only a second server saves you from losing the server itself. The cheap, cluster-free scheme: a small standby VPS receiving data every few minutes (restic or rsync), with the stack described by the same compose file. Switchover is an A-record change with a low TTL (60 s) or the provider's floating IP if there is one.

```text
monitor (external) ── catches down ──▶ standby
  1. restore data from the latest backup
  2. docker compose up -d
  3. switch floating IP / DNS (TTL 60)
total: minutes of downtime, pennies for standby
```

The whole chain can be automated with a script — one of our case studies is a site that migrates itself to a fresh VPS with no human involved in about a minute.

## Checklist

<div class="checklist">
  <div>Every service has a healthcheck that verifies dependencies</div>
  <div>restart: always + autoheal: hung things restart themselves</div>
  <div>The stack comes up with one command from git on a clean server</div>
  <div>Data leaves the server every N minutes; restore rehearsed</div>
  <div>DNS TTL is 60 s; switchover documented in a runbook</div>
  <div>Monitoring does not live on the server it watches</div>
</div>
