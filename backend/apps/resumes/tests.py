import tempfile

import numpy as np
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from unittest.mock import patch

from apps.resumes.models import Resume
from apps.resumes.keywords import find_skills
from apps.resumes.tasks import process_resume, skill_key


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
    def test_keyword_scan_fills_skills_the_model_missed(self, mock_ask_model, mock_extract_text):
        mock_extract_text.return_value = "Built with ReactJS and TensorFlow"
        mock_ask_model.return_value = {"skills": ["ReactJS"]}

        resume = self.make_resume()
        process_resume(resume.id)
        resume.refresh_from_db()

        # TensorFlow added by the scan; the scan's "React" merged into the model's "ReactJS".
        self.assertEqual(resume.ai_feedback["skills"], ["ReactJS", "TensorFlow"])

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

    @patch("apps.resumes.tasks.extract_text_from_pdf")
    @patch("apps.resumes.tasks.ask_model", return_value=None)
    def test_unreachable_model_fails_instead_of_reporting_zero_skills(
        self, mock_ask_model, mock_extract_text
    ):
        mock_extract_text.return_value = "Experienced Python developer"

        resume = self.make_resume()
        process_resume(resume.id)
        resume.refresh_from_db()

        self.assertIn("Processing failed", resume.ai_feedback["status"])


class SkillKeyTests(SimpleTestCase):
    def test_skill_key_ignores_spelling(self):
        assert skill_key("NodeJS") == skill_key("node.js") == skill_key("Node JS")
        assert skill_key("React") == skill_key("react js") == skill_key("React.js")
        assert skill_key("C++") != skill_key("C#") != skill_key("C")
        assert skill_key("JavaScript") != skill_key("Java")
        assert skill_key("HTML5") == skill_key("html")


class FindSkillsTests(SimpleTestCase):
    def test_finds_skills_in_resume_shorthand(self):
        found = find_skills(
            "Machine Learning (Python) with TensorFlow, Keras. "
            "Full-Stack (VanillaJS/NodeJS&Express/MongoDB). Git&GitHub, HTML5, CSS3"
        )
        for skill in ["Python", "TensorFlow", "Keras", "Node.js", "Express",
                      "MongoDB", "Git", "GitHub", "HTML", "CSS", "Machine Learning"]:
            assert skill in found, skill

    def test_skips_substrings_and_everyday_words(self):
        found = find_skills("JavaScript developer who can excel at express delivery; digital")
        assert "Java" not in found
        assert "Excel" not in found
        assert "Express" not in found
        assert "Git" not in found
