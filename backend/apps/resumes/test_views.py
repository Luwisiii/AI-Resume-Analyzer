import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from unittest.mock import patch

from apps.resumes.models import Resume

User = get_user_model()

PDF = b"%PDF-1.4 fake body"


# Without this, every run writes its fake uploads into the real backend/media/.
@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ResumeAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("owner", password="pw-for-tests-1")
        self.stranger = User.objects.create_user("stranger", password="pw-for-tests-2")
        self.resume = Resume.objects.create(
            user=self.owner, file=SimpleUploadedFile("resume.pdf", PDF)
        )

    def test_anonymous_cannot_read_a_resume(self):
        assert self.client.get(f"/api/resumes/{self.resume.id}/").status_code == 401

    def test_stranger_cannot_read_someone_elses_resume(self):
        # Ids are sequential, so this is the walk-the-table case.
        self.client.force_login(self.stranger)
        response = self.client.get(f"/api/resumes/{self.resume.id}/")
        assert response.status_code == 404

    def test_owner_can_read_their_own_resume(self):
        self.client.force_login(self.owner)
        response = self.client.get(f"/api/resumes/{self.resume.id}/")
        assert response.status_code == 200
        assert response.json()["id"] == self.resume.id

    def test_response_omits_extracted_text_embedding_and_storage_path(self):
        self.resume.extracted_text = "Jane Doe, 12 Somewhere St, 0917..."
        self.resume.embedding = [0.0] * 384
        self.resume.save()

        self.client.force_login(self.owner)
        body = self.client.get(f"/api/resumes/{self.resume.id}/").json()

        assert "extracted_text" not in body
        assert "embedding" not in body
        assert "file" not in body
        assert body["file_name"].endswith(".pdf") and "/" not in body["file_name"]

    def test_uploaded_files_are_not_publicly_served(self):
        assert self.client.get(f"/media/{self.resume.file.name}").status_code == 404

    def test_jobs_list_requires_authentication(self):
        assert self.client.get("/api/jobs/").status_code == 401

    def test_anonymous_cannot_upload(self):
        response = self.client.post(
            "/api/resumes/upload/", {"file": SimpleUploadedFile("r.pdf", PDF)}
        )
        assert response.status_code == 401


@override_settings(MAX_RESUME_BYTES=1024, MEDIA_ROOT=tempfile.mkdtemp())
class UploadValidationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("uploader", password="pw-for-tests-3")
        self.client.force_login(self.user)

        patcher = patch("apps.resumes.views.process_resume")
        self.mock_task = patcher.start()
        self.addCleanup(patcher.stop)

    def upload(self, name, body):
        return self.client.post("/api/resumes/upload/", {"file": SimpleUploadedFile(name, body)})

    def test_accepts_a_real_pdf_and_queues_processing(self):
        assert self.upload("resume.pdf", PDF).status_code == 201
        assert Resume.objects.count() == 1
        self.mock_task.delay.assert_called_once()

    def test_rejects_a_non_pdf_renamed_to_pdf(self):
        # accept=".pdf" in the browser is a hint, not a constraint.
        response = self.upload("payload.pdf", b"<?php echo 1; ?>")
        assert response.status_code == 400
        assert "not a valid PDF" in str(response.json())
        assert Resume.objects.count() == 0

    def test_rejects_a_non_pdf_extension(self):
        assert self.upload("resume.exe", PDF).status_code == 400

    def test_rejects_an_oversized_file(self):
        response = self.upload("resume.pdf", PDF + b"x" * 2048)
        assert response.status_code == 400
        assert "limit" in str(response.json())

    def test_rejects_an_empty_file(self):
        assert self.upload("resume.pdf", b"").status_code == 400

    def test_rejects_a_request_with_no_file(self):
        assert self.client.post("/api/resumes/upload/", {}).status_code == 400

    def test_rejects_too_many_files_at_once(self):
        files = [SimpleUploadedFile(f"r{i}.pdf", PDF) for i in range(6)]
        assert self.client.post("/api/resumes/upload/", {"file": files}).status_code == 400

    def test_upload_requires_csrf_token(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        response = strict.post("/api/resumes/upload/", {"file": SimpleUploadedFile("r.pdf", PDF)})
        assert response.status_code == 403

    def test_broker_outage_returns_503_and_keeps_no_orphan(self):
        self.mock_task.delay.side_effect = ConnectionError("redis down")
        assert self.upload("resume.pdf", PDF).status_code == 503
        assert Resume.objects.count() == 0

    def test_uploads_are_throttled(self):
        statuses = [self.upload("resume.pdf", PDF).status_code for _ in range(11)]
        assert statuses[-1] == 429
