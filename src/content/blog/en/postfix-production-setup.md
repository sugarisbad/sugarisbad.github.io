---
title: 'Setting up Postfix: practices for reliable email'
titleHtml: 'Setting up Postfix: practices <em>for reliable email</em>'
description: 'DNS, relay restrictions, TLS, SPF/DKIM/DMARC and queue monitoring: what to configure before the first message. A practical approach and opsmith setup pricing — from RUB 18,000.'
pubDate: 2026-11-14
cat: vps
tags: [postfix, email]
minutes: 10
ctaTitle: 'Email on your domain — <em>turnkey</em>?'
ctaText: "We'll configure Postfix, TLS and SPF/DKIM/DMARC — from RUB 18,000. Incoming and outgoing mail tested, configuration and operating notes handed over. The base estimate is 2–3 days; scope is agreed before work starts."
---

## Start with the server's role and DNS

Postfix receives, routes and sends messages. For IMAP access and user mailboxes, you will usually also need Dovecot; for filtering and DKIM signing, something like Rspamd. Before installing packages, decide whether this is staff email, application notifications or an intermediate SMTP relay. That determines the exposed ports, authentication and delivery path.

A server receiving and sending mail directly needs a stable public IP, working TCP/25 and the ability to set a PTR record with the provider. Check hosting restrictions first: opening your firewall does not remove an upstream block on outbound SMTP.

The host should identify itself with a fully qualified name such as `mail.example.com`. Its A record points to the server IP, that IP's PTR points back to the same name, and the domain's MX points to the mail host. An example for a single IPv4 address:

```text
example.com.       IN MX 10 mail.example.com.
mail.example.com.  IN A     192.0.2.10
```

`192.0.2.10` is a documentation address: replace it with yours. The IP owner controls PTR records, usually through your VPS provider's panel. Enable IPv6 together with working routing, PTR and SPF: an AAAA record alone does not make the mail path ready.

<div class="practice"><span>FROM PRACTICE</span>A message accepted by <code>sendmail</code> has only entered the local queue. Confirm delivery through the remote server's response and a test mailbox. Even <code>status=sent</code> does not guarantee inbox placement: that is up to the recipient's filters.</div>

## Restrict relaying and separate the ports

An open relay lets anyone send messages through your server to unrelated domains. Keep relay authorization separate from spam filtering, using `smtpd_relay_restrictions`. For a modern Postfix 3.6+ installation, a base fragment looks like this:

```ini
# /etc/postfix/main.cf — fragment
myhostname = mail.example.com
mynetworks = 127.0.0.1/32 [::1]/128

smtpd_relay_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination

# Enable AUTH only on the client submission service
smtpd_sasl_auth_enable = no
```

Keep `mynetworks` limited to addresses you actually trust. Adding an entire hosting network or Docker subnet "to make the app work" grants relay privileges to every host inside it. Give applications separate SMTP accounts instead.

TCP/25 is for server-to-server mail. Clients submit messages over TCP/587 with STARTTLS or TCP/465 with TLS from the start. Accepted domains must also be configured explicitly: `mydestination` for local domains, or the appropriate virtual/relay maps for your design. Publishing an MX record does not itself tell Postfix to accept a domain's mail.

## TLS and authentication belong on the right service

A public MX typically offers STARTTLS with `may`, preserving compatibility with external senders. Submission requires both encryption and authentication. Applying `encrypt` to all inbound TCP/25 traffic prevents senders without TLS from delivering mail.

```ini
# /etc/postfix/main.cf — fragment for Postfix 3.6+
smtpd_tls_security_level = may
smtp_tls_security_level = may
smtpd_tls_chain_files = /etc/postfix/tls/mail.pem
smtpd_tls_mandatory_protocols = >=TLSv1.2
smtpd_tls_auth_only = yes

smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
smtpd_sasl_security_options = noanonymous
```

In `mail.pem`, the private key comes first, followed by the server certificate and intermediate certificates. The file is owned by root with `0600` permissions. Certificate renewal must replace this file atomically and run `postfix reload`. Configure the Dovecot socket at `/var/spool/postfix/private/auth` separately, allowing access for the Postfix user.

For TCP/587, add or update the existing service in `master.cf`:

```text
# /etc/postfix/master.cf
submission inet n - n - - smtpd
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_relay_restrictions=permit_sasl_authenticated,reject
```

These are configuration fragments, not a complete mail stack: the certificate, user database, authentication socket and recipient maps must exist. TCP/465 needs a separate service with `smtpd_tls_wrappermode=yes`. Settings beginning with `smtp_*` apply to Postfix's outbound client; `smtpd_*` settings apply to its receiving server.

If mail goes through a fixed external relayhost, require TLS with certificate and hostname verification for that destination. For direct MX delivery, `may` is a compatible baseline, but it does not prevent encryption downgrade attacks. A stricter server-to-server policy can use DANE with DNSSEC or an MTA-STS deployment.

## SPF, DKIM and DMARC: configure the complete chain

SPF lists authorized sending sources, DKIM signs the message, and DMARC checks alignment between the visible `From` domain and a domain authenticated by SPF or DKIM. Three TXT records without working signing and delivery-path checks do not finish the job.

For a single sending IP, an initial DNS configuration might look like this:

```text
example.com. IN TXT "v=spf1 ip4:192.0.2.10 -all"
_dmarc.example.com. IN TXT "v=DMARC1; p=none; rua=mailto:dmarc@example.com"
```

That SPF record fits only if this server is the domain's sole sender. Include your CRM, mailing service and other legitimate sources in one SPF record before enforcing `-all`. Publishing multiple separate `v=spf1` records at the same name causes a validation error.

Configure DKIM through Rspamd or OpenDKIM connected to Postfix via Milter. For RSA, use a 2048-bit key and a dedicated selector such as `mail2026._domainkey.example.com`. Check signing for messages submitted by SMTP clients and for mail injected locally by an application.

Start DMARC with `p=none` and a working mailbox for aggregate reports. Once every legitimate source is accounted for, move to `quarantine`, then `reject`. The `p=none` policy does not block anything. Inspect the recipient's `Authentication-Results` on test messages: expect `spf=pass`, `dkim=pass` and `dmarc=pass`.

## Spam filtering and limits: watch both directions

For inbound mail, configure filtering and an accurate recipient list. Reject an unknown mailbox during the SMTP session instead of accepting a message and later sending a bounce to a forged address. Catch-all delivery removes that check, so enable it only for a specific requirement.

For outbound mail, apply limits per account or application through a policy service or filtering component. Connection limits per IP and fail2ban help against password guessing, but do not replace volume controls for an already authenticated user.

On submission, bind permitted envelope-from addresses to logins through `smtpd_sender_login_maps` and a suitable mismatch restriction. This does not automatically validate the visible `From` header: add a separate filtering policy if that also needs to be restricted.

<div class="practice"><span>FROM PRACTICE</span>A sudden rise in the outgoing queue is a reason to inspect applications and accounts. Repeatedly running <code>postqueue -f</code> will not fix incorrect DNS, a recipient rejection or a stolen password. Find the cause through the queue ID and the remote server's response first.</div>

## Queues, backups and configuration as code

A minimal diagnostic sequence after changing configuration:

```bash
sudo postfix check
postconf -n
postqueue -p
```

`postfix check` checks some local settings and permissions, `postconf -n` shows overridden parameters, and `postqueue -p` shows the queue and deferral reasons. After checking, apply the changes with `sudo postfix reload`. None of these commands replaces an external test of reception, sending and relay rejection.

Monitor queue size and the age of the oldest deferred message, free space and inodes, authentication failures and TLS certificate expiry. Set thresholds against normal traffic. Add a full-path probe: application → SMTP → test mailbox. See our [Prometheus and Grafana article](/en/blog/prometheus-grafana-monitoring/) for the alerting approach.

Keep configuration and DNS templates in Git, with passwords and private keys stored separately. Encrypted backups should cover configuration, DKIM keys, user data and mailboxes if you host them. Test restoration on a separate machine; our [restic backup guide](/en/blog/backups-321-restic/) covers the approach.

## Checklist before switching MX

<div class="checklist">
  <div>The provider permits the required SMTP traffic; A/AAAA, PTR, MX and hostname agree</div>
  <div>An external untrusted host cannot relay to a third-party domain without AUTH</div>
  <div>587/465 require TLS and authentication; the certificate and renewal are tested</div>
  <div>An existing mailbox receives mail; an unknown recipient is correctly rejected</div>
  <div>An external recipient confirms SPF, DKIM and DMARC; every sending source is tested</div>
  <div>Sending limits and alerts for queues, disk space and certificate expiry work</div>
  <div>Configuration is reproducible and a backup has been restored on another host</div>
  <div>Migration includes an MX cutover plan and a route back to the previous server</div>
</div>

## What Postfix setup costs at opsmith

**Base self-hosted email setup starts at RUB 18,000.** This is the "Self-hosted email: DKIM/SPF/DMARC" item in our [price list](/en/services/), with an estimated **2–3 days** once the required access and hosting environment are ready.

For a typical project, we agree on Postfix on one server, receiving and sending for a domain, SMTP submission with TLS and authentication, SPF/DKIM/DMARC, relay restriction checks and test delivery. Configuration and operating notes are handed over. Domain and mailbox counts, Dovecot, webmail and migration of existing messages are scoped before work begins.

Additional work uses the same published price-list items:

- **Existing server and security audit — RUB 4,800**, estimated at 1–2 hours.
- **Automated backups — from RUB 9,600**, estimated at 1 day.
- **Monitoring with Telegram alerts — from RUB 18,000**, estimated at 2–4 days.
- **Retainer administration — from RUB 12,000/month.**

For example, base email setup plus automated backups starts at **RUB 27,600**: 18,000 + 9,600. There is no dedicated bundle discount for this pair in the price list. VPS hosting, domains, external storage and paid SMTP relay services are billed separately; migration and custom integrations are scoped individually.

These are the base RUB prices as of November 14, 2026. The [service calculator](/en/services/) shows USD equivalents at its displayed exchange rate. We agree on the final scope and quote in writing. Correct authentication helps delivery, while inbox placement also depends on IP reputation, message content and the recipient's policies.

[Discuss email setup on Telegram →](https://t.me/sugarisbad_bot?start=mail-en)

## References

- [Postfix: SMTP relay and access control](https://www.postfix.org/SMTPD_ACCESS_README.html).
- [Postfix: TLS support and encryption policies](https://www.postfix.org/TLS_README.html).
- [Postfix: SASL and Dovecot integration](https://www.postfix.org/SASL_README.html).
- [Gmail sender requirements](https://support.google.com/a/answer/81126?hl=en).
