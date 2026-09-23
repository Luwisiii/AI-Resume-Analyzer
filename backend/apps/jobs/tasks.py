import html
import logging
import os
import re

import requests
from celery import shared_task
from django.utils import timezone

from apps.ai.job_prompts import job_skill_extraction_prompt
from apps.ai.utils import ask_model, embed

from .models import JOB_STALE_AFTER, Job

logger = logging.getLogger(__name__)


REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
JOOBLE_URL = "https://jooble.org/api/"
JOOBLE_PAGE_SIZE = 20

# ponytail: sized for qwen2.5:7b (the LLM_MODEL default), which holds strict JSON
# well at this width. Drop it back toward 10 for a smaller model — a batch that comes
# back malformed loses skills for every posting in it.
JOB_SKILL_BATCH_SIZE = 20

TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text, limit=2000):
    """Job descriptions arrive as HTML; embeddings want plain text."""
    return " ".join(html.unescape(TAG_RE.sub(" ", text or "")).split())[:limit]


def _row(url, title, **fields):
    """Shared Job field dict, or None if the posting is unusable."""
    url = (url or "").strip()
    title = (title or "").strip()
    # A truncated link is a broken link, so drop it rather than store it.
    if not url or not title or len(url) > 500:
        return None
    return {"url": url, "title": title, **fields}


# Real postings carry 1-19 tags; some agencies (Lemon.io) tag every posting with
# ~50 stacks they hire for, which would list .NET and Unity as "missing" for a QA role.
MAX_REMOTIVE_TAGS = 30


def normalize_remotive(posting):
    tags = posting.get("tags") or []
    if len(tags) > MAX_REMOTIVE_TAGS:
        tags = []  # no skills list beats a wrong one; the embedding still matches
    return _row(
        posting.get("url"),
        posting.get("title"),
        company=(posting.get("company_name") or "").strip()[:255],
        location=(posting.get("candidate_required_location") or "").strip()[:255],
        industry=(posting.get("category") or "").strip()[:100],
        description=strip_html(posting.get("description")),
        skills=", ".join(sorted({t.strip().lower() for t in tags if t and t.strip()})),
        source="remotive",
    )


def normalize_skills(value):
    """Model output -> the comma-joined form Job.skills stores.

    Lowercased to stay subtractable from the resume's skill set in match scoring.
    """
    if not isinstance(value, list):
        return ""
    return ", ".join(sorted({s.strip().lower() for s in value if isinstance(s, str) and s.strip()}))


def extract_skills_batch(descriptions):
    """Skills for several postings in one model call.

    Always returns one entry per input, in order. Best effort: a model hiccup, or a
    posting key the model skipped, costs that posting its skills — never the fetch.
    """
    result = ask_model(job_skill_extraction_prompt(descriptions))
    if not isinstance(result, dict):
        logger.warning("skill extraction gave no JSON object: %.200r", result)
        return [""] * len(descriptions)

    skills = [normalize_skills(result.get(str(i))) for i in range(len(descriptions))]
    empty = sum(1 for s in skills if not s)
    if empty:
        logger.warning("skill extraction returned nothing for %s of %s postings in batch",
                       empty, len(descriptions))
    return skills


def fill_missing_skills(rows, batch_size=JOB_SKILL_BATCH_SIZE):
    """Sources without a tags list (Jooble) get skills off the description instead.

    Postings already stored with skills are reused, so a scheduled re-run does not
    re-pay for them; the rest go to the model in batches, not one call each.

    Roughly half of Jooble postings legitimately yield nothing: its API returns a
    ~270-char excerpt from the middle of the posting, which often lands on company
    boilerplate ("~14,000+ teammates globally") rather than requirements. Two fixes
    were measured and rejected:
      - Smaller batches did not rescue them (4 -> 0/11, 8 -> 1/11).
      - Prepending the title raised the fill rate but the model just echoed the
        title back ("full stack developer"), which would then surface to candidates
        as a *missing skill*. Empty is better than wrong.
    Those postings still match on their embedding; they just carry no skills list.
    """
    todo = [r for r in rows if not r["skills"]]
    if not todo:
        return

    known = dict(
        Job.objects.filter(url__in=[r["url"] for r in todo])
        .exclude(skills="")
        .values_list("url", "skills")
    )

    pending = []
    for row in todo:
        row["skills"] = known.get(row["url"], "")
        if not row["skills"] and row["description"]:
            pending.append(row)

    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        extracted = extract_skills_batch([r["description"] for r in batch])
        for row, skills in zip(batch, extracted):
            row["skills"] = skills

    calls = -(-len(pending) // batch_size)
    logger.info("fill_missing_skills: %s reused, %s extracted in %s call(s)",
                len(todo) - len(pending), len(pending), calls)


def normalize_jooble(posting):
    # Jooble exposes no skills/tags list; fill_missing_skills() derives them
    # from the snippet before ingest.
    return _row(
        posting.get("link"),
        posting.get("title"),
        company=(posting.get("company") or "").strip()[:255],
        location=(posting.get("location") or "").strip()[:255],
        industry="",
        description=strip_html(posting.get("snippet")),
        skills="",
        source="jooble",
    )


def ingest(rows):
    """Embed normalized postings and upsert them by URL."""
    if not rows:
        return {"created": 0, "updated": 0}

    vectors = embed(
        [f"{r['title']} {r['company']} {r['location']} {r['skills']} {r['description']}" for r in rows]
    )

    created = updated = 0
    for row, vector in zip(rows, vectors):
        row = dict(row)
        url = row.pop("url")
        row["embedding"] = vector.tolist()
        _, was_created = Job.objects.update_or_create(url=url, defaults=row)
        created += was_created
        updated += not was_created

    logger.info("ingest: %s created, %s updated", created, updated)
    return {"created": created, "updated": updated}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={"max_retries": 3})
def fetch_remotive_jobs(self, search=None, limit=100):
    """Remote-worldwide postings from Remotive (free, no API key)."""
    params = {"limit": limit}
    if search:
        params["search"] = search

    response = requests.get(REMOTIVE_URL, params=params, timeout=60)
    response.raise_for_status()
    postings = response.json().get("jobs", [])

    rows = [r for r in map(normalize_remotive, postings) if r]
    if not rows:
        logger.warning("remotive: no usable postings for search=%r", search)
    return {"received": len(postings), **ingest(rows)}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={"max_retries": 3})
def fetch_jooble_jobs(self, search="", location="Philippines", limit=100):
    """Philippine (or any country's) postings from Jooble. Needs JOOBLE_API_KEY."""
    api_key = os.environ.get("JOOBLE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "JOOBLE_API_KEY is not set. Get a free key at https://jooble.org/api/about"
        )

    postings = []
    for page in range(1, (limit + JOOBLE_PAGE_SIZE - 1) // JOOBLE_PAGE_SIZE + 1):
        response = requests.post(
            JOOBLE_URL + api_key,
            json={"keywords": search, "location": location, "page": str(page)},
            timeout=60,
        )
        response.raise_for_status()
        batch = response.json().get("jobs") or []
        postings.extend(batch)
        if len(batch) < JOOBLE_PAGE_SIZE or len(postings) >= limit:
            break

    postings = postings[:limit]
    rows = [r for r in map(normalize_jooble, postings) if r]
    if not rows:
        logger.warning("jooble: no usable postings for search=%r location=%r", search, location)
    fill_missing_skills(rows)
    return {"received": len(postings), **ingest(rows)}


def prune_stale_jobs():
    """Drop postings no fetch has re-confirmed inside the staleness window."""
    cutoff = timezone.now() - JOB_STALE_AFTER
    deleted, _ = Job.objects.filter(last_seen__lt=cutoff).delete()
    if deleted:
        logger.info("prune_stale_jobs: removed %s postings last seen before %s", deleted, cutoff)
    return deleted


@shared_task
def refresh_jobs(search="", location="Philippines", limit=100):
    """Refresh every configured source, then drop postings that have gone away.

    This is the scheduled entry point. A source without credentials is skipped and
    a source that errors is recorded, so one bad source never blocks the others.
    """
    sources = {
        "remotive": lambda: fetch_remotive_jobs(search=search or None, limit=limit),
        "jooble": lambda: fetch_jooble_jobs(search=search, location=location, limit=limit),
    }

    results = {}
    for name, call in sources.items():
        try:
            results[name] = call()
        except RuntimeError as exc:
            results[name] = {"skipped": str(exc)}
        except Exception as exc:
            logger.exception("refresh_jobs: %s failed", name)
            results[name] = {"error": str(exc)}

    # Prune only behind a fetch that actually saw postings. Pruning after a run of
    # failures would quietly empty the table instead of refreshing it.
    received = sum(r.get("received", 0) for r in results.values())
    results["pruned"] = prune_stale_jobs() if received else 0
    if not received:
        logger.warning("refresh_jobs: no source returned postings, skipping prune")

    return results
