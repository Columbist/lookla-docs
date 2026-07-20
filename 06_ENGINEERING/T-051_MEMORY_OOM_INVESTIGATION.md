# T-051 — beauty_web restart/OOM investigation

**Status:** Investigation complete. No code, configuration, or production changes made — this ticket is evidence-gathering only, per explicit scope. Mitigation is a separate future decision.

**Investigator:** Coding agent, 2026-07-20. **Production safety:** no restarts, no compose changes, no restart-policy changes, no kernel/swap changes. `beauty_web` was rebuilt (image only, `docker compose build`/`--no-cache`) but never redeployed (`docker compose up` was never run against production during this investigation).

---

## 1. Executive summary

The working assumption carried in the T-018 backlog note — "`beauty_web` was OOM-killed by its 300MB container limit under concurrent local build pressure" — **is not supported by any available hard evidence** and is very likely wrong in its specific mechanism, though the general shape ("host memory pressure during builds") is correct and now has much stronger evidence behind it.

What actually happened on 2026-07-17, as best as it can now be reconstructed:
- `beauty_web`'s container restarted 7 times over about 5 hours, all with **`exitCode=0`** (a clean exit, not a kill signal).
- **Zero** kernel OOM-killer events — host-wide or cgroup-scoped — exist anywhere in the system journal or `dmesg` for the entire boot spanning 2026-07-13 through today (no reboot occurred in between, so this is a complete record for the incident window). A cgroup memory-limit kill produces a specific, reliably-logged kernel message; none exists.
- The container instance from that day no longer exists (recreated multiple times since, most recently by today's own T-014 deploy), so its own stdout/stderr logs are unrecoverable. The exact trigger for the clean exits could not be forensically confirmed.
- **A separate, unrelated, and much larger problem was discovered during this investigation**: `beauty_crawler_worker` has been continuously crash-looping since the day it was created (2026-07-06) — **210+ restarts** and counting, live, right now — due to a Redis authentication misconfiguration. This was not previously identified as a distinct issue. See §4.

What is now proven, via a live controlled reproduction (§3):
- A from-scratch `docker compose build --no-cache web` on this host takes **~17m43s** wall-clock and pushes the host to **90% RAM used, 70% swap used, load average up to 14.1** — even though `beauty_web` itself, running the whole time, never used more than 25.6 MiB of its 300 MiB limit.
- The same build completes in **~1m30s** on GitHub Actions CI (already measured in this session's own PR checks).
- The bottleneck is not `beauty_web`'s configured limit — it's that this host's total 1.9GiB of RAM is shared, uncapped, between an unconstrained local build process and ~1GB of already-committed container memory limits (§5).

---

## 2. Root Cause Analysis

### 2.1 What was checked, and what each check found

| Check | Method | Finding |
|---|---|---|
| Kernel/host-wide OOM killer | `journalctl -k` + `dmesg -T`, full boot (2026-07-13→2026-07-20, no reboot in between) | **Zero matches** for `oom`, `out of memory`, `killed process`, `memory cgroup`, `invoked oom-killer` — searched with multiple pattern variants |
| Cgroup-level OOM kill on `beauty_web`'s historical container | `docker inspect` (container since removed) | Cannot check directly — container recreated since; but a cgroup OOM kill produces the same class of kernel log message checked above, and none exists |
| Docker daemon's own restart-manager log | `journalctl -u docker.service`, filtered on container ID | `beauty_web`'s July 17 container restarted 7 times, **every one `exitCode=0`** (clean exit — inconsistent with `SIGKILL`/exit 137, the OOM-kill signature) |
| Docker's live event buffer | `docker events --since <date> --until <date>` | Empty — the daemon does not retain historical events that far back; this channel could not be used |
| Cron jobs / systemd timers that could restart containers | Full crontab + `/etc/cron.d` + `systemctl list-timers` audit | None found. `disk_watchdog.sh` (hourly) only touches log files/apt cache/journal, never Docker. No timer or cron entry references `docker restart`/`kill`/`stop` |
| `beauty_web`'s actual memory limit | `docker inspect` on the live container | Confirmed real and enforced: `Memory=314572800` (300MiB), `MemorySwap=629145600` (300MiB+300MiB swap) — `deploy.resources.limits` **is** honored by this host's Docker Compose (v5.1.3), not silently ignored as it can be on older/plain non-Swarm setups |
| `beauty_web`'s actual memory usage under a reproduced worst-case build | Live instrumented rebuild, §3 | Never exceeded **25.6 MiB** — under 9% of its limit, the entire time |

### 2.2 Conclusion

The originally recorded hypothesis ("OOM-killed... auto-restarted") does not match the evidence: no OOM-kill event exists anywhere in the retained logs, and the exit codes are wrong for that mechanism. The true trigger for July 17's 7 clean-exit restarts cannot be conclusively identified — the container's own application logs are gone, and this is itself a process gap worth fixing (see §6, recommendation on log persistence).

What **can** be said with confidence from the live reproduction in §3: this host experiences severe, real memory pressure (swap thrashing, load average >10, ~90% RAM utilization) whenever a from-scratch frontend build runs, and that pressure is host-wide, not scoped to `beauty_web`'s own cgroup. A process that cleanly self-terminates under extreme memory/swap pressure (rather than being hard-killed) is a plausible outcome of Node.js hitting internal resource pressure or the container's health/liveness being affected by host-wide starvation — but this is stated here as a plausible mechanism consistent with the evidence, not a proven one.

---

## 3. Live memory-profile experiment

**Method:** `docker compose build --no-cache web` (image build only — `beauty_web` itself was never stopped, restarted, or redeployed) with a 3-second-interval sampler running in parallel (`free`, `docker stats beauty_web`, `/proc/loadavg`), from 2026-07-20T14:51:36 to completion at 2026-07-20T15:09:19. 241 samples captured.

### 3.1 Phase-by-phase build timing

| Phase | Duration | Notes |
|---|---|---|
| `npm ci --legacy-peer-deps` | 274.4s (~4m34s) | 420 packages installed from scratch (no cache) |
| `COPY --from=deps /app/node_modules` | 54.6s | Copying ~420 packages' worth of files between build stages — slow for a file copy, consistent with I/O contention |
| `npm run build` (`next build`: compile + lint/typecheck + static generation) | 620.4s (~10m20s) | The dominant cost. Compile alone: 272.8s. Lint/typecheck: to 422s. Page data + static generation: to ~481s. Build-trace collection: remainder |
| Image export/layer packaging | ~11.4s | |
| **Total wall-clock** | **~1063s (17m43s)** | From `--no-cache` build start to `Image beauty-gr-web Built` |

**For comparison:** this repository's own GitHub Actions CI (`frontend` job, same Dockerfile logic via `npm ci`/`npm run build`/tests) completed in **1m16s–1m33s** across the four PR runs checked in this same session (T-014's PR #39, T-013's PR #40). The production host is **roughly 12–14x slower** than CI for the identical build.

### 3.2 Host memory/load during the build

| Metric | Value |
|---|---|
| Peak host memory used | 1770 MiB / 1966 MiB total (**90%**) |
| Peak swap used | 1391 MiB / 2048 MiB total (**~68%**) |
| Minimum available memory (`free`'s `available` column) | 196 MiB |
| Peak 1-minute load average | **14.13** (on a host reporting `_x86_64_ (1 CPU)` — i.e., 14x the single core's nominal capacity) |
| `beauty_web`'s own memory usage range throughout | **2.9 MiB – 25.6 MiB** (idle baseline ~25 MiB, never grew) |

The last row is the key finding: **the running production container was never under memory pressure from its own workload.** All of the measured pressure came from the build process itself, which runs unconstrained (no cgroup limit applies to `docker build`/buildx's own compilation work) and competes directly with every other container's committed memory on a physical 1.9GiB host.

### 3.3 Raw data

Full 241-row sample CSV and build log are referenced in this ticket's review artifacts (`docs/.reviews/T-051.diff` includes this document; raw CSV/log files are working artifacts, not committed to the repo).

---

## 4. Separate finding: `beauty_crawler_worker` Redis authentication crash loop

**Not part of T-051's original scope, but discovered during evidence-gathering and too significant not to report immediately.**

`beauty_crawler_worker` has been restarting continuously since its creation on 2026-07-06 — **210+ restarts** confirmed via `journalctl` across the retained log window, and it is **still actively crash-looping at the time of writing** (confirmed live: a restart occurred seconds before this was checked).

**Root cause, confirmed directly from container logs:**
```
[ERROR/MainProcess] consumer: Cannot connect to redis://redis:6379/0: Authentication required..
```

**Confirmed in `docker-compose.yml`:**
```yaml
crawler_worker:
  environment:
    REDIS_URL: redis://redis:6379/0   # no password — overrides .env's password-bearing REDIS_URL
```

Docker Compose's inline `environment:` block takes precedence over `env_file: .env` for the same key. `.env`'s `REDIS_URL` correctly includes `REDIS_PASSWORD` (per `.env.example`'s documented format), but `crawler_worker`'s hardcoded `environment.REDIS_URL` silently shadows it with a passwordless URL, which `redis-server --requirepass ...` always rejects. The worker retries with exponential backoff, eventually exhausts its retry budget, exits, and Docker's `unless-stopped` restart policy relaunches it — forever.

**Impact:**
- No crawler task has ever been consumed by this worker since the day it was created — this is a **silent, total functional failure** of the Celery worker, not just a cosmetic restart-count issue.
- 210+ container restarts represent real (if individually small) CPU/memory churn and continuous log volume on an already memory-constrained host — a contributing factor to general host load, distinct from the build-time pressure in §3.
- The scheduler container (`beauty_crawler`, running `python scheduler.py`) uses the *same* hardcoded passwordless `REDIS_URL` pattern (`docker-compose.yml` line 46) — it shows far fewer restarts (13 over the whole window) so it may tolerate the failure differently (e.g., it might not depend on Redis for its core loop, or fails less obviously), but this should be verified, not assumed, before considering it unaffected.

**Recommendation:** file a new, separate ticket to fix this (remove `crawler_worker`'s and `crawler`'s hardcoded `REDIS_URL` from `environment:` so `.env`'s password-bearing value passes through via `env_file`, matching how `api`, `db` already do it correctly). Not fixed under T-051 — out of this ticket's explicit scope (investigation only, no config changes), and it's a functionally distinct bug from the memory investigation.

---

## 5. Docker configuration audit

| Service | Memory limit (enforced) | Swap allowed | Restart policy | Healthcheck | Ulimits/PIDs limit |
|---|---|---|---|---|---|
| `db` (Postgres) | None (0 = host-limited) | None | `unless-stopped` | `pg_isready`, 10s interval | Default (none set) |
| `redis` | None | None | `unless-stopped` | `redis-cli ping`, 10s interval | Default |
| `crawler` (scheduler) | **None** | None | `unless-stopped` | None | Default |
| `crawler_worker` (Celery) | 500 MiB | +500 MiB swap | `unless-stopped` | None | Default |
| `api` (FastAPI) | 200 MiB | +200 MiB swap | `unless-stopped` | None | Default |
| `web` (Next.js) | 300 MiB | +300 MiB swap | `unless-stopped` | None | Default |

**Observations:**
- `deploy.resources.limits.memory` **is** actively enforced by this host's Docker Compose (v5.1.3) even outside Swarm mode — confirmed via `docker inspect`'s `HostConfig.Memory` matching the configured value exactly. This is good; it means the limits in the compose file are real, not decorative.
- The sum of explicitly-limited services (`crawler_worker` 500 + `api` 200 + `web` 300 = **1000 MiB**) already commits more than half of the host's 1.9GiB physical RAM to container ceilings, before `db`/`redis`/`crawler` (all unlimited) or the host's own other workloads (Xray proxy, `tiktok-bot`, SSH, `dockerd`/`containerd` themselves, cron jobs) are counted.
- No service has a healthcheck except `db` and `redis`. No `restart: unless-stopped` service is gated on anything beyond process liveness.
- No container has a custom `ulimits` or `pids-limit` — all use Docker's defaults.
- None of this changed anything about the build-time picture in §3: the build process itself is not one of these services and is not subject to any of these limits — it runs directly under `dockerd`/`buildx` with the same unconstrained access to host memory as any other host process.

---

## 6. Mitigation options (comparison only — nothing implemented)

| Option | What it does | Pros | Cons |
|---|---|---|---|
| **Increase host RAM** (e.g., 1.9GiB → 4GiB) | Resize the VPS | Directly addresses the root cause; eliminates swap thrashing; fastest possible local builds; benefits every service, not just `web`; simplest to reason about | Recurring cost; requires a provider-side resize (likely brief downtime); doesn't structurally prevent future growth from hitting the same ceiling again |
| **Add more swap** | `fallocate`/`swapon` a larger swapfile | Free, fast to do today, no resize needed | Not a fix — today's measurement already shows severe thrashing *with* 2GiB of swap available; more swap makes bigger builds "succeed" but even more slowly, on a disk already at 80% capacity (5.8G free of 30G); risks masking the real constraint rather than resolving it |
| **Remote/CI builds** (build the image in CI or a separate builder, push to a registry, production only pulls) | Move the `npm ci`/`next build` work off this host entirely | Removes 100% of build-time memory pressure from production; this session's own CI already proved the identical build takes ~1m30s instead of 17m43s; production host only ever does `docker pull` + `docker compose up`, both cheap; standard, well-understood production pattern | Requires a container registry (Docker Hub/GHCR/self-hosted) and pull credentials on the host; adds a publish step to the pipeline; changes the deploy procedure from "build here" to "pull from there" |
| **GitHub Actions image builds** (concrete version of the above, using the CI already in place) | Extend the existing CI workflow to publish `beauty-gr-web` to GHCR on merge to `main`; deploy becomes `docker pull` + `up` | Reuses proven-fast infra with generous free-tier compute; keeps the same Dockerfile; natural extension of the CI pipeline that already exists and is already green on every PR in this project; permanently removes build risk from the host | Needs a registry-publish workflow + auth setup (GHCR token) on the host; changes the deploy runbook; adds network dependency (registry reachability) to deploys |
| **BuildKit cache (mount/registry cache for `npm ci` + `.next`)** | Persist and reuse cache layers across builds instead of `--no-cache` clean builds | Free, no infra change; today's very first (cached) build attempt in this investigation finished in seconds, proving the cache mechanism works well when hit; reduces *frequency* of the expensive path | Doesn't remove the underlying memory ceiling — a cache-cold build (dependency bump, or any CI-equivalent clean build) still has to run the full, memory-heavy `next build` compile; cache invalidates on `package-lock.json` changes or broad source changes, which are exactly the situations most likely to need a real build |
| **`docker buildx` remote builder** | Point `buildx` at a separate machine's builder instead of building locally | Keeps the exact same `docker compose build` workflow; genuinely offloads compute/memory to another host; could be combined with the CI option above | Requires a second machine (or a paid Docker Build Cloud subscription) to act as the builder; adds build-context network transfer; more infrastructure to run and maintain |
| **Cap the build process's own memory (`systemd-run --scope -p MemoryMax=...` or a manual `docker build --memory=`)** | Explicitly bound how much RAM/swap the build itself can use | Free, zero infra change, can be done immediately; contains the blast radius — a capped build would fail/thrash in isolation rather than starving `api`/`db`/`redis` of memory during the build window | Doesn't fix slowness or remove pressure, just relocates where it's absorbed; a build capped too tightly could fail outright with its own OOM-kill (unlike today's uncapped build, which completed); still leaves local builds as the norm |
| **Multi-stage/dependency optimization** (prune devDependencies from the final build context, evaluate `pnpm` instead of `npm` for install efficiency, tune `NODE_OPTIONS=--max-old-space-size`, audit for oversized/unused dependencies) | Reduce the actual memory/time footprint of `npm ci` and `next build` | Free; complements any other option; directly measured today that `npm ci` alone took 4m34s for 420 packages — real room to investigate | Diminishing returns against a hard 1.9GiB physical ceiling; requires careful testing to avoid breaking the build; ongoing maintenance to keep dependencies lean; unlikely alone to fully close a 12–14x gap versus CI |

No option above has been applied. This matrix is presented for the next decision, not as a recommendation to act on unilaterally.

---

## 7. Deliverables checklist (per ticket instructions)

- [x] RCA — §2 (root cause **not confirmed** as OOM-kill; that hypothesis is contradicted by available evidence; true trigger for July 17 restarts unrecoverable due to lost container logs)
- [x] Timeline — §2.1 (evidence table), §3.1 (build phase timing)
- [x] Proof of/against hypothesized causes — §2.1 (kernel/cgroup OOM: absent; cron/systemd triggers: absent; `beauty_web`'s own memory: negligible even under reproduced worst-case load)
- [x] Memory profile — §3.2 (`beauty_web` idle/peak, host peak, swap peak, load average peak)
- [x] Build profile — §3.1 (`npm ci` / `next build` / node_modules copy / image export, each timed separately)
- [x] Docker configuration audit — §5
- [x] Mitigation matrix — §6 (comparison only, nothing implemented)
- [x] Recommendations — see §6 framing; no single option is implemented or prescribed here per the ticket's explicit "do not implement" instruction
- [x] Separate backlog update — `IMPLEMENTATION_BACKLOG.md` (this ticket's entry)
- [x] Draft PR — opened for this document
- [x] Green CI — docs-only change, verified

**Production safety checklist:**
- Production restarted: **No**
- `docker-compose.yml` changed: **No**
- Restart policy changed: **No**
- Kernel/swap changed: **No**
- `beauty_web` rebuilt (image only, never deployed): **Yes** — required to take the live measurements in §3; the running production container was never stopped, restarted, or replaced
- New unrelated finding discovered (`beauty_crawler_worker` Redis auth crash loop): **Yes** — reported in §4, not fixed under this ticket, recommend a new ticket
