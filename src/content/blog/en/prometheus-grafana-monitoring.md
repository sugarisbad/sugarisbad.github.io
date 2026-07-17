---
title: 'DIY server monitoring: Prometheus + Grafana in one evening'
titleHtml: 'DIY server monitoring: Prometheus + Grafana <em>in one evening</em>'
description: 'Metrics, a dashboard and Telegram alerts — no SaaS subscriptions, no extra agents. One compose file, three services, and you learn about problems before your customers do.'
pubDate: 2026-06-28
cat: monitoring
tags: [monitoring, prometheus]
minutes: 8
ctaTitle: 'Want monitoring <em>done for you</em>?'
ctaText: "We'll deploy Prometheus + Grafana with Telegram alerts in 2–3 days — with dashboards and rules that stay with you."
---

## Three services, zero subscriptions

For one or two servers you don't need Datadog or New Relic — a stack of node_exporter (host metrics), Prometheus (collection and rules) and Grafana (dashboards) covers 90% of the job and lives in a single compose file. The whole bundle uses less than 300 MB of RAM.

```yaml
services:
  node-exporter:
    image: prom/node-exporter:v1.8.2
    pid: host
    volumes: ['/:/host:ro,rslave']
    command: ['--path.rootfs=/host']
    ports: ['127.0.0.1:9100:9100']
  prometheus:
    image: prom/prometheus:v2.53.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prom-data:/prometheus
    ports: ['127.0.0.1:9090:9090']
  grafana:
    image: grafana/grafana:11.1.0
    volumes: ['graf-data:/var/lib/grafana']
    ports: ['127.0.0.1:3000:3000']
volumes: { prom-data: {}, graf-data: {} }
```

All ports bind to 127.0.0.1 only: monitoring doesn't face the internet; you reach Grafana over an SSH tunnel or a reverse proxy with auth.

## What to collect and what to draw

One job for node_exporter with a 15-second interval is enough in prometheus.yml. Don't build your own dashboard — import the ready-made Node Exporter Full (ID `1860` in the Grafana catalog): disk, memory, CPU, network and load are already laid out.

```yaml
# prometheus.yml
scrape_configs:
  - job_name: node
    scrape_interval: 15s
    static_configs:
      - targets: ['node-exporter:9100']
```

<div class="practice"><span>FROM PRACTICE</span>The first thing a freshly deployed monitoring stack catches at client sites is a disk filled 90%+ with Docker logs. Check <code>node_filesystem_avail_bytes</code> before celebrating a green dashboard.</div>

## Alerts in Telegram

A beautiful dashboard is useless if someone has to stare at it. The rule is simple: everything important comes to you in Telegram. Since Grafana 9 the Telegram contact point is built in — a bot token and chat_id are enough; you don't need Alertmanager to get started.

Three rules that cover most incidents:

```text
disk:  node_filesystem_avail_bytes{mountpoint="/"} 
       / node_filesystem_size_bytes < 0.15  (10 min)
memory: node_memory_MemAvailable_bytes 
       / node_memory_MemTotal_bytes < 0.10  (10 min)
server silent: up == 0                      (2 min)
```

The `up == 0` rule is the big one: it fires when the server stops reporting metrics at all — i.e., when "everything is down".

## Checklist

<div class="checklist">
  <div>node_exporter, Prometheus and Grafana run from a compose file in git</div>
  <div>Monitoring ports closed from outside; access via tunnel or authed proxy</div>
  <div>Node Exporter Full dashboard imported and showing live data</div>
  <div>Disk, memory and up == 0 alerts arrive in Telegram</div>
  <div>A test alert has been sent and received (Test button on the contact point)</div>
  <div>Prometheus retention set deliberately (15 days is enough for almost everyone)</div>
</div>
