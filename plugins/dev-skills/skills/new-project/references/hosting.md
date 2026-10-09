# Hosting — from artifact to live URL

Turns the built project into the **live, publicly reachable application** on the user's VPS, using the hosting pattern the host already practices. Re-detect the pattern each run; never assume example values are still true. Contents: host pattern, recipe, guardrails, teardown, forms per type.

**Naming rule: the deployment carries the project's own name — `<project>.<base-domain>`, vhost `<project>.conf`, compose project `<project>`. Never a "demo" label, prefix or subdomain: what is deployed is the application itself.** Ownership of created resources is proven by the **deployment registry**, not by any naming convention.

## The host pattern (detect, don't assume)

Detected shape (verify each element in Phase 0):
- **Host nginx** as reverse proxy: one vhost file per app in `/etc/nginx/sites-available/` + symlink in `sites-enabled/`, each doing `proxy_pass http://127.0.0.1:<port>`.
- **Apps in docker compose**, publishing **loopback-only** ports (e.g. `127.0.0.1:6201->80`).
- **TLS via certbot** (`--nginx` installer), one cert per FQDN.
- **Base domain** from the plugin option `${user_config.new_project_host_domain_pattern}` (default `<dashed-ip>.nip.io`, a DNS-free pattern where any `<label>.<dashed-ip>.nip.io` resolves to the VPS). A real wildcard domain, when configured, takes precedence.

Phase 0 detection: `which nginx docker`, `sudo -n true`, list `sites-available/` and their `proxy_pass` ports, `ss -tlnp` for listeners, `docker ps` port bindings, public IP (for the nip.io base), read the deployment registry.

## Deployment recipe (Phase 5)

1. **Name & port.** Name: `<project>` (validated at Checkpoint 1, collision-checked there against existing confs, compose projects and the registry). Port: first free port in the range `${user_config.new_project_port_range_start}`-`${user_config.new_project_port_range_end}`, checked against `ss -tlnp`, every `proxy_pass` in `sites-available/`, `docker ps`, and the registry. Collision ⇒ next port, **never** kill a listener.
2. **Run the app — the whole app**: `docker compose up -d` with **every** service the application needs (backend, database, cache, workers — never a front pointing at a mocked or absent backend), `restart: unless-stopped`, **named volumes for every stateful service** so data survives restarts, ports bound `127.0.0.1:<port>:…` — never `0.0.0.0` — and **explicit resource limits** (`mem_limit`, `cpus`) sized to the app: a deployment must never be able to starve the host's other services (an OOM here takes preprod projects down with it). Verify persistence: `docker compose restart`, then confirm previously entered data is still there. (A non-dockerized fallback — systemd user unit — is acceptable for trivial static sites; docker is the default.)
3. **Vhost**: FQDN = `<project>.<base_domain>` (nip.io base if no domain configured). Write `/etc/nginx/sites-available/<project>.conf` (proxy_pass to the port, standard proxy headers, `client_max_body_size` if uploads), symlink into `sites-enabled/`, then **`nginx -t` — if it fails, remove your file and symlink and reload nothing** — then `systemctl reload nginx`.
4. **Privacy gate — mandatory decision, default `${user_config.new_project_privacy_default}` (basic-auth = closed).** If the brief marks the data private or sensitive (interview Round 4) **and** the app has no authentication of its own, protect the vhost with **HTTP basic auth**: generate a random password (`openssl rand -base64 15`), write `/etc/nginx/htpasswd-<project>` (`openssl passwd -apr1` output, via `sudo tee`, mode 640), add `auth_basic` + `auth_basic_user_file` to the vhost's `location /`. Credentials are delivered at Checkpoint 2 and in the final report — never committed anywhere. Skipping the gate on private data requires the user's **explicit** wish for an open app (their Round-4 "shareable with anyone" answer counts). Public-by-intent apps and apps with real in-app auth skip the gate naturally.
5. **TLS**: `certbot --nginx -d <fqdn>`. Mind Let's Encrypt rate limits (per-domain weekly caps — nip.io FQDNs share the nip.io registered domain, so a busy week can hit them): on rate-limit failure, serve HTTP and state it plainly in the report rather than failing the run.
6. **Verify from the outside**: `curl -I https://<fqdn>` must answer through the public route (a `401` is the *expected* answer when the privacy gate is on — then verify again with the credentials); capture the screenshot **through the public URL**, not localhost.
7. **Register** the deployment in `~/.claude/new-project-deployments.yml`: `name, fqdn, port, project_dir, compose_project, vhost_file, auth (basic|app|open), created` (ISO date). **The registry is the sole proof of ownership** — it is what makes teardown and collision checks reliable, and what authorizes ever touching a resource again.

## Guardrails (shared host — these override any convenience)

- **Only create, never edit**: existing vhost files, containers, compose projects, certs and listeners belong to real projects (preprod included) — untouchable, unrestartable.
- **Ownership = registry entry.** A resource may be modified or removed **only** if it appears in `~/.claude/new-project-deployments.yml`. Anything not in the registry is someone else's, whatever its name looks like.
- `nginx -t` **before every reload**, without exception.
- Loopback binding only; the only public doors are nginx's 80/443.
- **Not production-grade**: the slot carries no backups, monitoring, SLA or hardening for third-party users; opening it to real third-party users is a production decision outside this skill. Anything secret stays in the project's `.env` (not in git, not in the vhost).
- **Machine-wide, not just nginx**: no `apt install`/system-wide package changes (user-space toolchains only), no shared-config edits, no `docker system prune`, no docker-daemon or service restarts, no firewall changes. `sudo` is for the vhost file, `nginx -t`/reload and certbot — nothing else.
- **Disk before build**: check `df -h` in Phase 0 and again before heavy builds (docker images eat GBs) — a full disk breaks every project on the host, not just this one.
- The Phase 0 **host-safety snapshot** is the reference, and the check is **mechanical**: `${CLAUDE_SKILL_DIR}/scripts/check-host-safety.sh snapshot <dir>` in Phase 0, `${CLAUDE_SKILL_DIR}/scripts/check-host-safety.sh diff <dir> --allow-name <project> --allow-port <port>` in Phase 5 (covers listeners, containers, vhosts, certs, cron, firewall status when readable, and the disk floor `NP_MIN_DISK_GB`, default 3 GB, set from `${user_config.new_project_min_disk_gb}`). **Exit 0 is a prerequisite for Checkpoint 2** — a violation means something pre-existing changed or something unexpected appeared: fix it, never wave it through.
- If sudo or nginx is unavailable, hosting is **declared impossible in Phase 0** and the run downgrades to `--no-host` behavior with an explicit blind spot — never a half-configured attempt discovered at Phase 5.

## Teardown (`--teardown=<name>`)

1. Look the name up in the registry (`~/.claude/new-project-deployments.yml`); not found ⇒ list what *is* registered and stop — never guess at unregistered resources.
2. Show what will be removed (containers, vhost, htpasswd file if any, cert) and **confirm with the user**.
3. `docker compose down` in the registered project dir → remove vhost symlink + file (+ `/etc/nginx/htpasswd-<name>` if present) → `nginx -t` → reload → `certbot delete --cert-name <fqdn>` (optional, offer it) → remove the registry entry → report.

## Deployment forms per type

- **web-app, static-site, api** (and **bot-worker** with a web surface): hosted URL as above. For an api, the URL serves `/docs`.
- **cli, library, tui**: no URL — the deliverable remains artifact + transcript per `delivery.md`. (Exposing a TUI via ttyd is possible but opt-in only — it's a shell on the VPS.)
- **browser-ext**: the built zip is *served* from a URL for easy download, but the extension itself still loads locally.
