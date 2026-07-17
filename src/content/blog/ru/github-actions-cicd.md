---
title: 'CI/CD для маленькой команды: GitHub Actions без боли'
titleHtml: 'CI/CD для маленькой команды: GitHub Actions <em>без боли</em>'
description: 'Деплой по пушу в main, секреты, откаты. Один workflow-файл, который можно скопировать — без Jenkins и выделенного CI-сервера.'
pubDate: 2026-05-30
cat: cicd
tags: [ci/cd, github actions]
minutes: 6
ctaTitle: 'Настроить CI/CD <em>за вас</em>?'
ctaText: 'Соберём пайплайн под ваш стек: тесты, сборка, деплой по пушу, стейджинг и откаты — с workflow-файлами в вашем репозитории.'
---

## Один файл вместо CI-сервера

Для команды до десяти человек Jenkins — это второй продукт, который нужно администрировать. GitHub Actions живёт в репозитории: один YAML — и у вас тесты на каждый пуш и деплой в прод по пушу в main. Бесплатных минут хватает почти всем небольшим проектам.

Рабочий каркас, который можно скопировать:

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
concurrency: production   # деплои не наслаиваются

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Tests
        run: docker compose -f compose.test.yml run --rm tests
      - name: Deploy over SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.HOST }}
          username: deploy
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /srv/app
            git pull --ff-only
            docker compose up -d --build
```

## Секреты: отдельный ключ, минимум прав

В Settings → Secrets кладём три вещи: адрес сервера, приватный SSH-ключ и, если нужно, токен реестра. Ключ — отдельный, сгенерированный только для деплоя, для пользователя без sudo. Тогда утечка секрета стоит вам одного ключа, а не всего сервера.

```bash
$ ssh-keygen -t ed25519 -f deploy_key -C "gh-actions"
# публичный — на сервер, приватный — в secrets.SSH_KEY
$ ssh-copy-id -i deploy_key.pub deploy@server
```

<div class="practice"><span>ИЗ ПРАКТИКИ</span>Строка <code>concurrency: production</code> — обязательна. Без неё два быстрых пуша подряд запускают два деплоя параллельно, и на сервере они переплетаются в непредсказуемом порядке.</div>

## Откат — это git revert

Самая надёжная стратегия отката для маленькой команды — не отдельная кнопка, а `git revert` + пуш: тот же пайплайн выкатит предыдущую версию тем же путём. Это работает, только если каждый деплой воспроизводим — образы собираются из кода, миграции обратимы, конфиг в репозитории.

<div class="checklist">
  <div>Деплой запускается только с main, вручную — через workflow_dispatch</div>
  <div>Тесты блокируют деплой: упали — выкатки нет</div>
  <div>SSH-ключ деплоя отдельный, у пользователя нет sudo</div>
  <div>concurrency не даёт деплоям наслаиваться</div>
  <div>Откат отрепетирован: git revert + push возвращает прошлую версию</div>
</div>
