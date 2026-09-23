# Deploying

Two options, both built from the root `Dockerfile`:

- **Render free tier**: a live demo for $0, no card needed. Covered first.
- **One VM with Docker Compose** (Oracle Always Free or any VPS): runs everything
  yourself, including a local LLM. See the end of this file.

## Render free tier (live demo)

| Piece | Service | Free-tier catch |
|---|---|---|
| Web app (Django + React) | Render web service | Sleeps after 15 min idle; first visit takes ~1 min to wake |
| Database (Postgres + pgvector) | Neon | 0.5 GB storage |
| LLM | Groq API | Per-minute rate limits |
| Weekly job refresh | GitHub Actions | GitHub disables schedules after 60 days of no repo activity |

Uploaded PDFs are stored on Render's disk, which is wiped on every deploy or
restart. They are processed within seconds of upload, so results are kept.
Only the original file is lost.

### 1. Groq API key
Sign up at [console.groq.com](https://console.groq.com) → **API Keys** → **Create API Key**.
Copy it (starts with `gsk_`). It is shown once.

### 2. Neon database
1. Sign up at [neon.tech](https://neon.tech) → create a project (region: AWS Singapore).
2. **Connect** → pick the **direct** connection (not pooled) and note the
   host, database, user and password.

The pgvector extension is enabled by the app's first migration. Nothing to do here.

### 3. Render web service
1. Sign up at [render.com](https://render.com) with GitHub.
2. **New → Blueprint** → pick this repo. Render reads `render.yaml`.
3. Fill in the values it asks for: `LLM_API_KEY` (step 1), `DB_HOST`, `DB_NAME`,
   `DB_USER`, `DB_PASSWORD` (step 2), and `JOOBLE_API_KEY` (optional, leave blank
   for Remotive-only postings).
4. **Apply**. The first build takes ~5 minutes. The site is at
   `https://ai-resume-analyzer-XXXX.onrender.com`.

### 4. Fill in the job postings
Matching needs postings in the database, refreshed at least every 14 days.
1. GitHub repo → **Settings → Secrets and variables → Actions** → add secrets
   `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `LLM_API_KEY`, `JOOBLE_API_KEY`
   (same values as on Render).
2. **Actions → Refresh job postings → Run workflow**. After that it runs weekly (Sundays).

## One VM with Docker Compose

The whole stack (Caddy for HTTPS, Django, Celery worker + beat, Redis,
Postgres/pgvector, Ollama) on one machine with ~8 GB+ RAM. For free, use an Oracle
Cloud Always Free Ampere VM (4 OCPU / 24 GB, Ubuntu 24.04, 100 GB boot volume).

1. Open TCP 80 and 443. On Oracle, open them both in the subnet's security list
   and on the VM itself:
   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```
2. Point a domain at the VM's IP (free: [DuckDNS](https://www.duckdns.org)).
3. Install Docker and start:
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER && newgrp docker
   git clone <your repo url> app && cd app
   cp .env.production.example .env && nano .env   # DOMAIN, SECRET_KEY, DB_PASSWORD, JOOBLE_API_KEY
   docker compose up -d --build
   ```
   The first boot downloads the model (~5 GB): `docker compose logs -f ollama-pull`.
4. Fill in job postings: `docker compose exec worker celery -A core call apps.jobs.tasks.refresh_jobs`.
   Celery beat refreshes them nightly after that.

| Task | Command |
|---|---|
| Deploy a new version | `git pull && docker compose up -d --build` |
| Logs | `docker compose logs -f web worker` |
| Back up the database | `docker compose exec db pg_dump -U postgres ai_resume_db > backup.sql` |
