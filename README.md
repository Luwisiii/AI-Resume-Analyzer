This is a web application that evaluates resumes using AI and provides instant, structured feedback on content quality, skills alignment, and overall effectiveness. It helps job seekers optimize their resumes based on intelligent analysis rather than guesswork. It uses vector embeddings and a locally hosted LLM.

The system accepts a PDF resume upload, extracts the text, analyzes it using an AI model, and returns actionable insights such as:

Resume strengths and weaknesses
Skills detected vs. missing
ATS (Applicant Tracking System) friendliness
Suggestions for improvement
Overall resume quality score

System Flow
1. Upload

The user uploads a resume PDF through the React interface.

2. Store & Extract

The backend built with Django saves the file and extracts the resume text.

3. Create Embeddings
Resume text → embedding vector
Job description → embedding vector
Stored in PostgreSQL using pgvector
4. Semantic Matching (Cosine Similarity)
resume_embedding ⋅ job_embedding
-------------------------------- = similarity score
  ||resume|| × ||job||

This measures semantic meaning, not keyword matching.

5. AI Resume Critique (Local LLM)

The extracted resume text is sent to Ollama, running qwen2.5:7b by default.
Override with the `OLLAMA_MODEL` and `OLLAMA_URL` environment variables.

The prompt forces structured JSON output:

strengths
weaknesses
improvements
detected skills
6. Real Job Postings

Job listings are pulled from public job APIs into the Job table and embedded, so
every match links to a live posting you can apply to:

- Jooble — Philippine (or any country's) roles, free key from
  https://jooble.org/api/about (`JOOBLE_API_KEY`, 500-request default quota).
  Paged 20 postings per request, so a `--limit 200` fetch spends 10 of them.
- Remotive — remote-worldwide roles, free, no API key. Returns at most 15
  postings per call regardless of `--limit`, so treat it as a small supplement.

```
python manage.py fetch_jobs                                  # every configured source
python manage.py fetch_jobs --source jooble --search "nurse"
python manage.py fetch_jobs --source jooble --location "Cebu" --limit 200
python manage.py fetch_jobs --source remotive
```

Re-running upserts by posting URL, so it is safe on a schedule.

Keeping listings fresh

Every posting carries a `last_seen` stamp, refreshed whenever a fetch confirms it
is still listed. Postings that stop appearing have almost certainly closed, so
after 14 days (`JOB_STALE_AFTER` in apps/jobs/models.py) they are pruned, and
matching only ever considers `Job.fresh()` — a candidate is never handed an apply
link for a posting that has aged out. The results panel shows "seen 2 days ago"
next to each link so the age is visible rather than assumed.

`--source all` fetches then prunes; a single-source run only fetches, since the
other source's postings would all look stale to it. Pruning is skipped entirely
when no source returned anything, so a run of failed fetches cannot empty the
table. Schedule the nightly refresh with Celery beat alongside the worker:

```
celery -A core.celery_app worker --pool=solo -l info
celery -A core.celery_app beat -l info
```

Beat only queues; the worker executes. Running beat alone means 3am passes and
tasks pile up in Redis until a worker starts. On Windows the worker needs
`--pool=solo` — Celery's default prefork pool does not work there. Drop that flag
on Linux, where prefork gives you real concurrency.

A source whose credential is missing is skipped with a warning, so `--source all`
still works with only some of them configured.

Remotive tags its postings with skills; Jooble does not, so new Jooble postings
have skills pulled from the snippet by Ollama, 20 at a time — keep Ollama running
for those fetches. Postings already stored with skills are reused, so re-runs cost
nothing, and postings imported while Ollama was down get their skills on a re-fetch.

Expect roughly half of Jooble postings to end up with no skills. Its API returns a
~270-character excerpt from the middle of the posting, which often lands on company
boilerplate rather than requirements, and the extractor is instructed not to invent
skills it cannot see. Those postings still match on their embedding — they just show
no "Missing skills" line. Remotive postings are unaffected; their skills come from
real tags.

7. Background Processing

Heavy tasks (embedding, AI analysis) run asynchronously using Celery with Redis.

8. Results

Django returns the similarity score and AI feedback to the React frontend for display.

▶️ How to Run the Project Locally
Prerequisites
Python
Node.js
PostgreSQL (port 5433) with the pgvector extension — e.g. via Docker:
`docker run -d --name ai_resume_db -p 5433:5432 -e POSTGRES_DB=ai_resume_db
-e POSTGRES_PASSWORD=<your-password> --restart unless-stopped pgvector/pgvector:pg16`
Redis
Ollama installed locally, with the model pulled: `ollama pull qwen2.5:7b`
(~4.7GB, wants ~8GB RAM; set `OLLAMA_MODEL=phi3:mini` for a lighter machine and
drop JOB_SKILL_BATCH_SIZE in backend/apps/jobs/tasks.py toward 10)

Configuration

Both halves read their settings from a `.env` file; copy the templates and fill
them in. Nothing is hard-coded any more, so the app will not start in production
without a real `SECRET_KEY`.

```
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Accounts

Resumes are private to the account that uploaded them, so the API requires a
token on every request:

```
POST /api/auth/register/   {username, email, password}  -> {token}
POST /api/auth/login/      {username, password}         -> {token}
GET  /api/auth/me/         Authorization: Token <key>
```

The React app handles this for you — register or sign in on first load, and the
token is stored in the browser and attached to each request.

Deploying

`DEBUG=False` requires `SECRET_KEY`, `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
to be set, and turns on HTTPS redirect, HSTS and secure cookies. Serve with:

```
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn core.wsgi:application --bind 0.0.0.0:8000
```

Uploaded resumes are private documents and are only served through the API's
per-owner check; Django serves the media directory directly in DEBUG only.

NOTE: This AI Resume Analyzer is currently under active development.

Some features, including AI scoring, job matching, and UI components, are still being improved and may change without notice. The current version is functional but not yet production-ready.

Feedback and suggestions are welcome as the project evolves.

## License

MIT — see [LICENSE](LICENSE).