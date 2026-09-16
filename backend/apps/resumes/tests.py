import tempfile

import numpy as np
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from unittest.mock import patch

from apps.resumes.models import Resume
from apps.resumes.tasks import process_resume


# Without this, every run writes its fake uploads into the real backend/media/.
@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestResumeTasks(TestCase):

    def setUp(self):
        patcher = patch("apps.resumes.tasks.model")
        self.mock_model = patcher.start()
        self.addCleanup(patcher.stop)
        # The task calls .tolist() on this, so it must be an array, not a list.
        self.mock_model.return_value.encode.return_value = np.zeros(384, dtype=np.float32)

    def make_resume(self):
        return Resume.objects.create(
            file=SimpleUploadedFile("resume.pdf", b"%PDF fake content")
        )

    @patch("apps.resumes.tasks.extract_text_from_pdf")
    @patch("apps.resumes.tasks.ask_model")
    def test_process_resume_success(self, mock_ask_model, mock_extract_text):
        mock_extract_text.return_value = "Experienced Python Django developer"
        mock_ask_model.return_value = {"skills": ["Python", "Django", "PostgreSQL"]}

        resume = self.make_resume()
        result = process_resume(resume.id)
        resume.refresh_from_db()

        self.assertIn("processed successfully", result)
        self.assertEqual(resume.skills, "Django, PostgreSQL, Python")
        self.assertIsNotNone(resume.embedding)
        self.assertEqual(
            resume.ai_feedback["status"], "Resume processed successfully using AI"
        )
        self.assertEqual(
            resume.ai_feedback["skills"], ["Django", "PostgreSQL", "Python"]
        )

    @patch("apps.resumes.tasks.extract_text_from_pdf")
    @patch("apps.resumes.tasks.ask_model")
    def test_string_skills_value_is_rejected_not_split_into_letters(
        self, mock_ask_model, mock_extract_text
    ):
        # A bare string here used to be iterated character by character, storing
        # "_, a, d, g, i, l, n, r, s, t, v" as the candidate's skills.
        mock_extract_text.return_value = "Some resume text"
        mock_ask_model.return_value = {"skills": "invalid_string"}

        resume = self.make_resume()
        process_resume(resume.id)
        resume.refresh_from_db()

        self.assertEqual(resume.skills, "")
        self.assertIsNotNone(resume.embedding)

    @patch("apps.resumes.tasks.extract_text_from_pdf")
    @patch("apps.resumes.tasks.ask_model")
    def test_unreadable_pdf_reports_a_terminal_status(
        self, mock_ask_model, mock_extract_text
    ):
        mock_extract_text.return_value = ""

        resume = self.make_resume()
        process_resume(resume.id)
        resume.refresh_from_db()

        self.assertIn("No readable text", resume.ai_feedback["status"])
        mock_ask_model.assert_not_called()
