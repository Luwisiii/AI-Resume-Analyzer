import numpy as np
from apps.resumes.models import Resume
from apps.jobs.models import Job

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two lists/vectors"""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))

def match_resume_to_job(resume: Resume, job: Job):
    """Return similarity score between 0 and 1"""
    # Check if embeddings exist and are non-empty
    if resume.embedding is None or job.embedding is None:
        return 0.0

    # If embeddings are NumPy arrays, ensure they are not empty
    if isinstance(resume.embedding, np.ndarray) and resume.embedding.size == 0:
        return 0.0
    if isinstance(job.embedding, np.ndarray) and job.embedding.size == 0:
        return 0.0

    # Compute similarity
    return cosine_similarity(resume.embedding, job.embedding)
