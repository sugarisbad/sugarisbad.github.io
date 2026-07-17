---
title: 'CI/CD for a small team: GitHub Actions without the pain'
titleHtml: 'CI/CD for a small team: GitHub Actions <em>without the pain</em>'
description: 'Deploy on push to main, secrets, rollbacks. One workflow file you can copy — no Jenkins, no dedicated CI server.'
pubDate: 2026-05-30
cat: cicd
tags: [ci/cd, github actions]
minutes: 6
ctaTitle: 'Want CI/CD <em>set up for you</em>?'
ctaText: "We'll build a pipeline for your stack: tests, builds, deploy on push, staging and rollbacks — with workflow files in your repository."
---

## One file instead of a CI server

For a team under ten people, Jenkins is a second product you have to administer. GitHub Actions lives in the repository: one YAML and you have tests on every push and production deploys on push to main. The free minutes cover almost every small project.

A working skeleton you can copy:

```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
concurrency: production   # deploys don't overlap

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

## Secrets: a dedicated key with minimal rights

In Settings → Secrets you put three things: the server address, a private SSH key and, if needed, a registry token. The key is a dedicated one generated only for deploys, for a user without sudo. Then a leaked secret costs you one key, not the whole server.

```bash
$ ssh-keygen -t ed25519 -f deploy_key -C "gh-actions"
# public key goes to the server, private into secrets.SSH_KEY
$ ssh-copy-id -i deploy_key.pub deploy@server
```

<div class="practice"><span>FROM PRACTICE</span>The <code>concurrency: production</code> line is mandatory. Without it two quick pushes start two deploys in parallel, and they interleave on the server in unpredictable order.</div>

## A rollback is a git revert

The most reliable rollback strategy for a small team is not a special button but `git revert` + push: the same pipeline ships the previous version the same way. This only works if every deploy is reproducible — images built from code, migrations reversible, config in the repository.

<div class="checklist">
  <div>Deploys run only from main; manual runs via workflow_dispatch</div>
  <div>Tests gate the deploy: if they fail, nothing ships</div>
  <div>The deploy SSH key is dedicated; its user has no sudo</div>
  <div>concurrency keeps deploys from overlapping</div>
  <div>Rollback rehearsed: git revert + push brings back the previous version</div>
</div>
