import logging

from django.conf import settings
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle

from .models import Resume
from .serializers import ResumeSerializer
from .tasks import process_resume

logger = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"
MAX_FILES_PER_UPLOAD = 5


class UploadThrottle(UserRateThrottle):
    scope = "upload"


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
@throttle_classes([UploadThrottle])
def upload_resume(request):
    files = request.FILES.getlist("file")
    if not files:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)
    if len(files) > MAX_FILES_PER_UPLOAD:
        return Response(
            {"error": f"Upload at most {MAX_FILES_PER_UPLOAD} files at a time"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    errors = {f.name: error for f in files if (error := validate_pdf(f))}
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    uploaded = []
    for f in files:
        resume = Resume.objects.create(file=f, user=request.user)
        try:
            process_resume.delay(resume.id)
        except Exception:
            # Broker down: nothing will ever process this row, so don't keep it.
            logger.exception("Could not queue resume processing")
            resume.file.delete(save=False)
            resume.delete()
            return Response(
                {"error": "The analysis service is unavailable right now. Please try again shortly."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
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
