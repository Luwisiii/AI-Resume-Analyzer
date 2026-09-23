# Deploying to Oracle Cloud Always Free

The whole stack (Caddy + Django + Celery worker/beat + Redis + Postgres/pgvector +
Ollama) runs from `docker-compose.yml` on one VM. Any Linux VPS with ~8 GB+ RAM works
the same way.

## 1. Create the VM

- Oracle Cloud console → Compute → Create instance.
- Image: **Ubuntu 24.04**. Shape: **VM.Standard.A1.Flex** (Ampere), **4 OCPU / 24 GB**.
  If it says "out of capacity", try another availability domain or retry later.
- Boot volume: 100 GB or more (images + the ~5 GB model).
- Networking → the subnet's security list → add ingress rules for TCP **80** and **443** from `0.0.0.0/0`.

## 2. Open the firewall on the VM

Oracle's Ubuntu images ship iptables rules that block everything but SSH:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

## 3. Point a domain at it

Any domain works. The free route is [DuckDNS](https://www.duckdns.org): create
`yourname.duckdns.org` and set it to the VM's public IP. Caddy gets the HTTPS
certificate automatically once the domain resolves to the VM.

## 4. Install Docker and start

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

git clone <your repo url> app && cd app
cp .env.production.example .env
nano .env   # set DOMAIN, SECRET_KEY, DB_PASSWORD, JOOBLE_API_KEY

docker compose up -d --build
```

The first boot downloads the model (~5 GB); watch it with
`docker compose logs -f ollama-pull`. Uploads fail with "AI model unreachable"
until it finishes.

## 5. Optional: admin user and initial jobs

```bash
docker compose exec web python manage.py createsuperuser
docker compose exec worker celery -A core call apps.jobs.tasks.refresh_jobs
```

## Day-to-day

| Task | Command |
|---|---|
| Deploy a new version | `git pull && docker compose up -d --build` |
| Logs | `docker compose logs -f web worker` |
| Back up the database | `docker compose exec db pg_dump -U postgres ai_resume_db > backup.sql` |

Data lives in the named volumes `pgdata`, `media` (uploaded resumes), `ollama`
and `caddy_data`. `docker compose down` keeps them. `down -v` deletes them.
