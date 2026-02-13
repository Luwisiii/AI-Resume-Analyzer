import numpy as np
from apps.resumes.models import Resume
from apps.jobs.models import Job


def cosine_similarity(vec1, vec2):
    # Safe check for None or empty
    if vec1 is None or vec1.size == 0:
        return 0.0
    if vec2 is None or vec2.size == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))


def match_resume_to_job(resume: Resume, job: Job):
    # Convert embeddings to np.array if stored as list
    resume_vec = None
    if resume.embedding is not None:
        if isinstance(resume.embedding, np.ndarray):
            resume_vec = resume.embedding
        else:
            resume_vec = np.array(resume.embedding, dtype=np.float32)

    job_vec = None
    if job.embedding is not None:
        if isinstance(job.embedding, np.ndarray):
            job_vec = job.embedding
        else:
            job_vec = np.array(job.embedding, dtype=np.float32)

    # Avoid truth-value errors with arrays
    if resume_vec is None or resume_vec.size == 0:
        return 0.0
    if job_vec is None or job_vec.size == 0:
        return 0.0

    return cosine_similarity(resume_vec, job_vec)
