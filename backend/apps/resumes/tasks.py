from celery import shared_task
from .models import Resume
from sentence_transformers import SentenceTransformer
from apps.ai.utils import ask_model
from apps.ai.resume_prompts import skill_extraction_prompt
import logging
import fitz

logger = logging.getLogger(__name__)

# Load once
model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text("text") or ""
    return text.strip()


@shared_task
def process_resume(resume_id):
    """
    1️⃣ Extract text
    2️⃣ AI skill extraction 
    3️⃣ Generate embeddings
    """

    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        return f"Resume {resume_id} not found"

    # 1️⃣ Extract text
    text = extract_text_from_pdf(resume.file.path)

    if not text:
        resume.ai_feedback = "No readable text found (scanned PDF)"
        resume.save()
        return f"Resume {resume_id} has no extractable text"

    resume.extracted_text = text
    
    # 2️⃣ AI SKILL EXTRACTION (🔥 FIX)
    ai_result = ask_model(skill_extraction_prompt(text))
    skills = ai_result.get("skills", [])

    if not isinstance(skills, list):
        skills = []

    # Normalize + dedupe
    normalized_skills = sorted(set(s.strip() for s in skills if s.strip()))

    resume.skills = ", ".join(normalized_skills)

    logger.warning("EXTRACTED SKILLS (AI):")
    logger.warning(normalized_skills)

    # 3️⃣ Generate embeddings (UNCHANGED)
    try:
        embedding = model.encode(text)
        resume.embedding = embedding  # pgvector compatible
    except Exception as e:
        resume.ai_feedback = f"Embedding failed: {str(e)}"
        resume.save()
        return f"Resume {resume_id} embedding failed"

    resume.ai_feedback = "Resume processed successfully using AI"
    resume.save()

    return f"Resume {resume_id} processed successfully"
