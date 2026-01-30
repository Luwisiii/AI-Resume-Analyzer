from celery import shared_task
from apps.ai.job_prompts import job_generation_prompt
from apps.ai.utils import ask_model
from sentence_transformers import SentenceTransformer
from .models import Job
import time, json, re

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def parse_json_array(text: str):
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if not match:
        return []
    raw = match.group()
    fixed = raw.replace("'", '"')
    fixed = re.sub(r",\s*]", "]", fixed)
    fixed = re.sub(r",\s*}", "}", fixed)
    try:
        data = json.loads(fixed)
        if isinstance(data, list):
            return data
        return []
    except Exception as e:
        print("❌ JSON parse failed:", e)
        return []


def ask_model_safe(prompt: str):
    text = ask_model(prompt)
    if isinstance(text, list):
        return text
    elif isinstance(text, str):
        return parse_json_array(text)
    else:
        return []


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={"max_retries": 3})
def generate_jobs(self, count=50):
    print("🔥 generate_jobs called with count =", count)

    batch_size = 5
    created_total = 0
    received_total = 0

    # Track existing jobs to avoid duplicates
    existing_jobs = set(
        (job.title.lower().strip(), job.skills.lower().strip())
        for job in Job.objects.all()
    )
    existing_industries = set(
        job.industry.lower().strip() for job in Job.objects.all()
    )

    for offset in range(0, count, batch_size):
        current_count = min(batch_size, count - offset)

        # Retry THIS batch up to 3 times
        batch_jobs = []
        for attempt in range(3):
            print(f"🔄 Batch {offset // batch_size + 1}, attempt {attempt + 1}")
            
            # Prompt encourages diversity but allows IT jobs
            prompt = job_generation_prompt(current_count)
            batch_jobs = ask_model_safe(prompt)

            if batch_jobs:
                break

            print("⚠️ Batch returned empty or invalid JSON, retrying...")
            time.sleep(2)

        if not batch_jobs:
            print("⚠️ Empty batch after 3 attempts, skipping")
            continue

        received_total += len(batch_jobs)

        for job in batch_jobs:
            title = (job.get("title") or "").strip()
            industry = (job.get("industry") or "").strip()
            skills = job.get("skills", [])

            if not title or not isinstance(skills, list):
                continue

            normalized_skills = sorted(set(s.strip() for s in skills if s.strip()))
            skills_text = ", ".join(normalized_skills)

            job_key = (title.lower(), skills_text.lower())
            if job_key in existing_jobs:
                continue
            existing_jobs.add(job_key)

            # Create DB entry
            obj, created = Job.objects.get_or_create(
                title=title,
                industry=industry,
                defaults={"skills": skills_text},
            )

            if created:
                try:
                    embed_text = f"{title} {industry} {skills_text}"
                    obj.embedding = embedding_model.encode(embed_text)
                    obj.save(update_fields=["embedding"])
                    created_total += 1
                except Exception as e:
                    print("❌ Embedding failed:", e)

    print("✅ generate_jobs finished")
    return {
        "requested": count,
        "received": received_total,
        "created": created_total,
    }
