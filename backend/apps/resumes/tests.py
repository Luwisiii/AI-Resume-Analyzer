from django.test import TestCase
from unittest.mock import patch
from apps.resumes.models import Resume
from django.core.files.uploadedfile import SimpleUploadedFile


class TestResumeTasks(TestCase):

    @patch("apps.resumes.tasks.extract_text_from_pdf")
    @patch("apps.resumes.tasks.ask_model")
    @patch("apps.resumes.tasks.model.encode")
    def test_process_resume_success(
        self,
        mock_encode,
        mock_ask_model,
        mock_extract_text,
    ):
        mock_extract_text.return_value = "Experienced Python Django developer"
        mock_ask_model.return_value = {
            "skills": ["Python", "Django", "PostgreSQL"]
        }
        # FIX: Provide a 384-dimensional vector
        mock_encode.return_value = [0.0] * 384

        resume = Resume.objects.create(
            file=SimpleUploadedFile("resume.pdf", b"%PDF fake content")
        )

        from apps.resumes.tasks import process_resume
        result = process_resume(resume.id)

        resume.refresh_from_db()

        self.assertIn("processed successfully", result)
        self.assertEqual(
            resume.skills,
            "Django, PostgreSQL, Python"
        )
        self.assertIsNotNone(resume.embedding)
        self.assertEqual(
            resume.ai_feedback,
            "Resume processed successfully using AI"
        )

    @patch("apps.resumes.tasks.extract_text_from_pdf")
    @patch("apps.resumes.tasks.ask_model")
    @patch("apps.resumes.tasks.model.encode")
    def test_process_resume_invalid_ai_response(
        self,
        mock_encode,
        mock_ask_model,
        mock_extract_text,
    ):
        mock_extract_text.return_value = "Some resume text"
        mock_ask_model.return_value = {"skills": "invalid_string"}
        mock_encode.return_value = [0.0] * 384

        resume = Resume.objects.create(
            file=SimpleUploadedFile("resume.pdf", b"%PDF fake content")
        )

        from apps.resumes.tasks import process_resume
        result = process_resume(resume.id)

        resume.refresh_from_db()

        # Skills should be empty because AI response was invalid
        self.assertEqual(resume.skills, "")
        # Embedding should still exist
        self.assertIsNotNone(resume.embedding)
        # AI feedback indicates failure (case-insensitive)
        self.assertIn("failed to extract skills", resume.ai_feedback.lower())
        self.assertIn("processed", result)
