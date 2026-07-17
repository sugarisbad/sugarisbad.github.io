---
title: 'Backups that actually restore: 3-2-1 in practice'
titleHtml: 'Backups that actually <em>restore</em>: 3-2-1 in practice'
description: "restic + S3-compatible storage, restore checks on cron, and an alert if a backup goes silent. A backup nobody has tested is a lottery ticket."
pubDate: 2026-05-11
cat: vps
tags: [vps, backups]
minutes: 7
ctaTitle: 'Backups <em>under watch</em>?'
ctaText: "We'll set up restic with encryption, restore rehearsals and alerts — and show you how to recover in 10 minutes."
---

## The 3-2-1 rule without pedantry

Three copies of the data, on two different media, one off-site. In practice for a VPS this means: live data on the server, an encrypted backup in S3-compatible storage at a different provider — done. A backup on the same server (or at the same provider in the same DC) is not a copy, it's an illusion: lose the account and you lose everything.

## restic: encryption and deduplication out of the box

restic encrypts everything client-side, stores snapshots incrementally and speaks any S3. A single binary, no daemons.

```bash
$ export RESTIC_REPOSITORY=s3:s3.storage.example.com/backup-bucket
$ export RESTIC_PASSWORD_FILE=/root/.restic-pass
$ restic init                        # once
$ restic backup /srv/app/data /etc \
    --exclude='*.tmp'
$ restic forget --keep-daily 7 --keep-weekly 4 \
    --keep-monthly 6 --prune
```

Don't copy live database files — dump first, back up the dump:

```bash
$ docker exec db pg_dump -U app -Fc app > /srv/backup/app.dump
$ restic backup /srv/backup
```

## A backup doesn't exist until it's been restored

The step everyone skips: restores must be rehearsed. Not "someday, when it burns", but on a schedule. The minimum — a weekly `restic check --read-data-subset` plus restoring the dump into a temporary database and checking that it opens.

```bash
# in cron, weekly:
restic check --read-data-subset=10%
restic restore latest --target /tmp/restore-test \
    --include /srv/backup/app.dump
pg_restore --list /tmp/restore-test/srv/backup/app.dump
```

<div class="practice"><span>FROM PRACTICE</span>A silently dead backup is worse than none — it buys false calm. Monitor not "the backup failed" but "the backup hasn't succeeded in a while": a healthcheck ping after every successful run, an alert if there's no ping for 26 hours.</div>

## Checklist

<div class="checklist">
  <div>The backup lives at a different provider, not on the same server</div>
  <div>The repository is encrypted; the password exists outside this server</div>
  <div>Databases are backed up as dumps, not live file copies</div>
  <div>forget/prune configured: old snapshots don't eat the budget</div>
  <div>Restores rehearsed on cron, not by hand once a year</div>
  <div>An alert fires when the backup has been silent for a day</div>
</div>
