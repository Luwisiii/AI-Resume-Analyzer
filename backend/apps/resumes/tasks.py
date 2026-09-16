from celery import shared_task
from .models import Resume
from apps.jobs.models import Job
from apps.analysis.matching import match_resume_to_job
from sentence_transformers import SentenceTransformer
from apps.ai.utils import ask_model
from apps.ai.resume_prompts import skill_extraction_prompt
from functools import lru_cache
import logging
import fitz

logger = logging.getLogger(__name__)


# Load embedding model once, on first use (importing this module must not hit the network)
@lru_cache(maxsize=1)
def model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text("text") or ""
    return text.strip()


@shared_task
def process_resume(resume_id):
    """Every exit path must leave a terminal ai_feedback.status behind: the client
    polls for one, and without it a crash here shows as a five-minute hang."""
    try:
        return _process_resume(resume_id)
    except Exception as e:
        logger.exception(f"Resume {resume_id} processing failed")
        Resume.objects.filter(id=resume_id).update(
            ai_feedback={
                "status": f"Processing failed: {e}",
                "skills": [],
                "matches": [],
                "overall_score": 0,
            }
        )
        return f"Resume {resume_id} failed: {e}"


def _process_resume(resume_id):
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return f"Resume {resume_id} not found"

    # 1️⃣ Extract text
    text = extract_text_from_pdf(resume.file.path)
    if not text:
        resume.ai_feedback = {
            "status": "No readable text found (scanned PDF)",
            "skills": [],
            "matches": []
        }
        resume.save(update_fields=["ai_feedback"])
        return f"Resume {resume_id} has no extractable text"

    resume.extracted_text = text

    # 2️⃣ AI Skill Extraction
    try:
        ai_result = ask_model(skill_extraction_prompt(text))
        logger.warning(f"RAW AI RESULT: {ai_result}")

        if isinstance(ai_result, dict):
            skills = ai_result.get("skills", [])
        elif isinstance(ai_result, list):
            skills = ai_result
        else:
            skills = []

        # A model that answers {"skills": "python, django"} would otherwise be
        # iterated character by character into single-letter "skills".
        if not isinstance(skills, list):
            logger.warning(f"AI returned a non-list skills value: {skills!r:.200}")
            skills = []

    except Exception as e:
        logger.error(f"AI extraction failed: {str(e)}")
        skills = []

    normalized_skills = sorted({
        s.strip() for s in skills if isinstance(s, str) and s.strip()
    })

    resume.skills = ", ".join(normalized_skills)

    # 3️⃣ Generate embedding
    try:
        embedding = model().encode(text, normalize_embeddings=True)
        resume.embedding = embedding.tolist()  # ✅ store as list for pgvector
        resume.save(update_fields=["extracted_text", "skills", "embedding"])
    except Exception as e:
        resume.ai_feedback = {
            "status": f"Embedding failed: {str(e)}",
            "skills": normalized_skills,
            "matches": []
        }
        resume.save(update_fields=["ai_feedback"])
        return f"Resume {resume_id} embedding failed"

    # 4️⃣ Job Matching (real postings, so each match carries an apply link)
    resume_skill_set = {s.lower() for s in normalized_skills}
    matches = []
    # Job.fresh() only: never hand someone an apply link for a posting that has
    # stopped appearing in its feed and has almost certainly closed.
    jobs = Job.fresh().exclude(embedding__isnull=True)
    for job in jobs:
        score = match_resume_to_job(resume, job)
        if score > 0.3:
            matches.append({
                "job_title": job.title,
                "company": job.company,
                "location": job.location,
                "url": job.url,
                "last_seen": job.last_seen.isoformat(),
                "resume_strength": round(score * 100, 2),
                "missing_skills": sorted(set(job.skills_list) - resume_skill_set),
            })

    matches.sort(key=lambda x: x["resume_strength"], reverse=True)
    matches = matches[:10]

    # 5️⃣ Generate Overall Score
    skill_score = min(len(normalized_skills) * 5, 50)  # max 50 pts

    match_score = 0
    top_matches = matches[:5]
    if top_matches:
        match_score = sum(m["resume_strength"] for m in top_matches) / len(top_matches)
        match_score = min(match_score * 0.5, 50)  # scale to max 50 pts

    overall_score = round(skill_score + match_score)
    
    resume.ai_feedback = {
        "status": "Resume processed successfully using AI",
        "skills": normalized_skills,
        "matches": matches,
        "overall_score": overall_score
    }
    resume.save(update_fields=["ai_feedback"])

    logger.warning(f"EXTRACTED SKILLS: {resume.skills}")
    logger.warning(f"JOB MATCHES: {matches}")

    return f"Resume {resume_id} processed successfully"
