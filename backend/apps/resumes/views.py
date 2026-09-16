from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Resume
from .serializers import ResumeSerializer
from .tasks import process_resume

PDF_MAGIC = b"%PDF-"


def validate_pdf(upload):
    """Returns an error string, or None if the upload looks like a real PDF.

    The frontend's accept=".pdf" is a hint to the file picker, not a constraint,
    so the only check that counts happens here.
    """
    if upload.size == 0:
        return "File is empty"
    if upload.size > settings.MAX_RESUME_BYTES:
        return f"File exceeds the {settings.MAX_RESUME_BYTES // (1024 * 1024)}MB limit"
    if not upload.name.lower().endswith(".pdf"):
        return "Only PDF files are accepted"

    # Content, not just the extension: read the header and rewind for the save.
    header = upload.read(len(PDF_MAGIC))
    upload.seek(0)
    if header != PDF_MAGIC:
        return "File is not a valid PDF"
    return None


@api_view(["POST"])
def upload_resume(request):
    files = request.FILES.getlist("file")
    if not files:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    errors = {f.name: error for f in files if (error := validate_pdf(f))}
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    uploaded = []
    for f in files:
        resume = Resume.objects.create(file=f, user=request.user)
        process_resume.delay(resume.id)
        uploaded.append(ResumeSerializer(resume).data)

    return Response({"data": uploaded}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def resume_detail(request, resume_id):
    # Scoped to the caller: resume ids are sequential, so an unscoped lookup would
    # let anyone walk the table and read every uploaded resume.
    resume = Resume.objects.filter(id=resume_id, user=request.user).first()
    if resume is None:
        return Response({"error": "Resume not found"}, status=status.HTTP_404_NOT_FOUND)

    # Scored matches (with apply links) live in ai_feedback.matches, built once
    # by the Celery task — not recomputed across every job on each poll.
    return Response(ResumeSerializer(resume).data)
