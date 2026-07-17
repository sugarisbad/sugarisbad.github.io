---
title: 'Setting up a VPS for Docker: from cloud-init to production'
titleHtml: 'Setting up a VPS for Docker: from cloud-init <em>to production</em>'
description: 'Step by step to a server you can be proud of: users and SSH keys via cloud-init, Docker with sane logging, firewall and unattended upgrades. All reproducible, as code.'
pubDate: 2026-07-12
cat: vps
tags: [vps, docker]
minutes: 9
ctaTitle: 'No time to do it <em>yourself</em>?'
ctaText: "We'll set up a Docker-ready VPS turnkey — from ~$95, with a cloud-init config that stays with you."
---

## Why cloud-init when you have hands

Manual SSH setup works right up until the second server. cloud-init runs your configuration on the first boot of a VPS — users, keys, packages — and the same file will bring up an identical server a year from now. Every major provider has a "user data" field right in the server creation form.

The minimal config: a dedicated `deploy` user with a key instead of a password, root login disabled, fresh packages.

```yaml
#cloud-config
users:
  - name: deploy
    groups: [sudo, docker]
    ssh_authorized_keys:
      - ssh-ed25519 AAAA… you@laptop
    sudo: ALL=(ALL) NOPASSWD:ALL
ssh_pwauth: false
disable_root: true
package_update: true
package_upgrade: true
```

## Docker: the official repo and log limits

Install Docker from the official repository, not from distro packages — those lag six months behind. And cap the logs immediately: a container writing to stdout with no limit will eat the whole disk in a couple of months. It is the single most common cause of "the server suddenly died" we get called about.

```json
// /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
```

<div class="practice"><span>FROM PRACTICE</span>After rewriting daemon.json you need <code>systemctl restart docker</code> — already-running containers keep the old log driver until they are recreated.</div>

## Firewall: three ports, no more

Only 22, 80 and 443 face the internet. Everything else — databases, metrics, admin panels — is reached over an SSH tunnel or VPN. The important nuance: Docker writes rules straight into iptables bypassing ufw, so a port published with `-p 5432:5432` is open to the whole internet no matter what ufw says. Publish ports on 127.0.0.1 only.

```bash
$ ufw default deny incoming
$ ufw allow 22/tcp comment 'ssh'
$ ufw allow 80,443/tcp comment 'web'
$ ufw enable
# expose service ports on loopback only:
ports: ["127.0.0.1:5432:5432"]
```

## Pre-production checklist

The server is ready when you can answer "yes" to every item — and point to where it lives in code:

<div class="checklist">
  <div>SSH key login only, root login disabled</div>
  <div>Docker from the official repo, logs capped (10m × 3)</div>
  <div>ufw: only 22, 80, 443 exposed; service ports on 127.0.0.1</div>
  <div>unattended-upgrades enabled for security updates</div>
  <div>compose files and cloud-init live in a git repository</div>
  <div>Backups configured and restored at least once</div>
</div>
