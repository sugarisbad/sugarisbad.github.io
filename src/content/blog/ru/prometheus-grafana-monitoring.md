---
title: 'Мониторинг сервера своими руками: Prometheus + Grafana за вечер'
titleHtml: 'Мониторинг сервера своими руками: Prometheus + Grafana <em>за вечер</em>'
description: 'Метрики, дашборд и алерты в Telegram — без SaaS-подписок и лишних агентов. Один compose-файл, три сервиса, и вы узнаёте о проблеме раньше клиентов.'
pubDate: 2026-06-28
cat: monitoring
tags: [мониторинг, prometheus]
minutes: 8
ctaTitle: 'Хотите мониторинг <em>под ключ</em>?'
ctaText: 'Поставим Prometheus + Grafana с алертами в Telegram за 2–3 дня — с дашбордами и правилами, которые останутся у вас.'
---

## Три сервиса, ноль подписок

Для одного-двух серверов не нужны Datadog и New Relic — стек из node_exporter (метрики хоста), Prometheus (сбор и правила) и Grafana (дашборды) закрывает 90% задач и живёт в одном compose-файле. Памяти вся связка ест меньше 300 МБ.

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

Все порты — только на 127.0.0.1: наружу мониторинг не смотрит, в Grafana ходим через SSH-туннель или reverse-proxy с авторизацией.

## Что собирать и что рисовать

В prometheus.yml достаточно одного job на node_exporter c интервалом 15 секунд. Для дашборда не собирайте свой — импортируйте готовый Node Exporter Full (ID `1860` в каталоге Grafana): диск, память, CPU, сеть и load уже разложены по панелям.

```yaml
# prometheus.yml
scrape_configs:
  - job_name: node
    scrape_interval: 15s
    static_configs:
      - targets: ['node-exporter:9100']
```

<div class="practice"><span>ИЗ ПРАКТИКИ</span>Первое, что ловит свежеподнятый мониторинг у клиентов, — диск, заполненный логами Docker на 90%+. Проверьте <code>node_filesystem_avail_bytes</code> прежде, чем радоваться зелёному дашборду.</div>

## Алерты в Telegram

Красивый дашборд бесполезен, если на него нужно смотреть. Правило простое: всё важное само приходит в Telegram. Начиная с Grafana 9 контакт-поинт «Telegram» встроен — достаточно токена бота и chat_id, Alertmanager для старта не нужен.

Три правила, которые закрывают большинство инцидентов:

```text
диск: node_filesystem_avail_bytes{mountpoint="/"} 
      / node_filesystem_size_bytes < 0.15  (10 минут)
память: node_memory_MemAvailable_bytes 
      / node_memory_MemTotal_bytes < 0.10  (10 минут)
сервер молчит: up == 0                     (2 минуты)
```

Правило `up == 0` — главное: оно срабатывает, когда сервер перестал отдавать метрики вообще, то есть когда «всё лежит».

## Чек-лист

<div class="checklist">
  <div>node_exporter, Prometheus и Grafana подняты из compose-файла в git</div>
  <div>Порты мониторинга закрыты снаружи, доступ — туннель или proxy с auth</div>
  <div>Дашборд Node Exporter Full импортирован и показывает живые данные</div>
  <div>Алерты на диск, память и up == 0 приходят в Telegram</div>
  <div>Тестовый алерт отправлен и получен (кнопка Test в контакт-поинте)</div>
  <div>Retention в Prometheus задан осознанно (15 дней хватает почти всем)</div>
</div>
