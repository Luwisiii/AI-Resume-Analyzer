from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Resume
from .serializers import ResumeSerializer
from .tasks import process_resume
from apps.jobs.models import Job


def get_resume_feedback(resume_skills, jobs):
    feedback = []
    resume_skills_set = {s.strip().lower() for s in resume_skills if s}

    for job in jobs:
        job_skills_set = (
            {s.strip().lower() for s in job.skills.split(",")}
            if job.skills else set()
        )

        if not job_skills_set:
            strength = 0
            matched_skills = set()
            missing_skills = set()
        else:
            matched_skills = resume_skills_set & job_skills_set
            missing_skills = job_skills_set - resume_skills_set
            strength = int((len(matched_skills) / len(job_skills_set)) * 100)

        feedback.append({
            "job_title": job.title,
            "resume_strength": strength,
            "matched_skills": sorted(matched_skills),
            "missing_skills": sorted(missing_skills),
        })

    return feedback


@api_view(["POST"])
def upload_resume(request):
    files = request.FILES.getlist("file")
    uploaded = []

    for f in files:
        resume = Resume.objects.create(
            file=f,
            user=request.user if request.user.is_authenticated else None
        )

        # async processing
        process_resume.delay(resume.id)

        uploaded.append(ResumeSerializer(resume).data)

    return Response({"data": uploaded}, status=status.HTTP_201_CREATED)




@api_view(["GET"])
def resume_detail(request, resume_id):
    try:
        resume = Resume.objects.get(id=resume_id)
        serialized = ResumeSerializer(resume).data

        # ✅ ADD job feedback as a DIFFERENT FIELD
        resume_skills = (
            [s.strip().lower() for s in resume.skills.split(",")]
            if resume.skills else []
        )

        jobs = Job.objects.all()
        serialized["job_feedback"] = get_resume_feedback(resume_skills, jobs)

        return Response(serialized)
    
    except Resume.DoesNotExist:
        return Response({"error": "Resume not found"}, status=404)



@api_view(["GET"])
def resume_job_match_view(request, resume_id, job_id):
    try:
        resume = Resume.objects.get(id=resume_id)
        job = Job.objects.get(id=job_id)

        resume_skills = (
            {s.strip().lower() for s in resume.skills.split(",")}
            if resume.skills else set()
        )

        job_skills = (
            {s.strip().lower() for s in job.skills.split(",")}
            if job.skills else set()
        )

        if not job_skills:
            return Response({"match_score": 0})

        matched = resume_skills & job_skills
        score = (len(matched) / len(job_skills)) * 100

        return Response({"match_score": round(score, 2)})

    except Resume.DoesNotExist:
        return Response({"error": "Resume not found"}, status=404)
    except Job.DoesNotExist:
        return Response({"error": "Job not found"}, status=404)
