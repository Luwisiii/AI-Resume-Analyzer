from celery import shared_task
from .models import Resume
from apps.jobs.models import Job
from apps.analysis.matching import match_resume_to_job
from sentence_transformers import SentenceTransformer
from apps.ai.utils import ask_model
from apps.ai.resume_prompts import skill_extraction_prompt
import logging
import fitz
import numpy as np

logger = logging.getLogger(__name__)

# Load embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text("text") or ""
    return text.strip()


@shared_task
def process_resume(resume_id):
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
        resume.save()
        return f"Resume {resume_id} has no extractable text"

    resume.extracted_text = text

    # 2️⃣ AI SKILL EXTRACTION
    ai_result = ask_model(skill_extraction_prompt(text))
    logger.warning(f"RAW AI RESULT: {ai_result}")

    if isinstance(ai_result, dict):
        skills = ai_result.get("skills", [])
    elif isinstance(ai_result, list):
        skills = ai_result
    else:
        logger.error(f"Unexpected AI result format: {type(ai_result)}")
        skills = []

    normalized_skills = sorted({s.strip() for s in skills if isinstance(s, str) and s.strip()})
    resume.skills = ", ".join(normalized_skills)

    # 3️⃣ Generate embeddings and store as list
    try:
        embedding = model.encode(text)
        resume.embedding = embedding.tolist()  # ✅ store as list for DB
        resume.save(update_fields=["extracted_text", "skills", "embedding"])
    except Exception as e:
        resume.ai_feedback = {
            "status": f"Embedding failed: {str(e)}",
            "skills": normalized_skills,
            "matches": []
        }
        resume.save()
        return f"Resume {resume_id} embedding failed"

    # 4️⃣ JOB MATCHING
    matches = []
    jobs = Job.objects.exclude(embedding__isnull=True)
    for job in jobs:
        # Convert job embedding to NumPy array in case stored as list
        score = match_resume_to_job(resume, job)
        if score > 0.4:
            matches.append({
                "job_title": job.title,
                "resume_strength": round(score * 100, 2),
                "missing_skills": []  # optional
            })
    matches = sorted(matches, key=lambda x: x["resume_strength"], reverse=True)

    # Save AI feedback
    resume.ai_feedback = {
        "status": "Resume processed successfully using AI",
        "skills": normalized_skills,
        "matches": matches
    }
    resume.save(update_fields=["ai_feedback"])

    logger.warning("EXTRACTED SKILLS (AI):")
    logger.warning(resume.skills)
    logger.warning("JOB MATCHES:")
    logger.warning(matches)

    return f"Resume {resume_id} processed successfully"
