from datetime import timedelta
from unittest.mock import patch

import numpy as np
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from .models import JOB_STALE_AFTER, Job
from .tasks import (
    JOB_SKILL_BATCH_SIZE,
    JOOBLE_PAGE_SIZE,
    extract_skills_batch,
    fetch_jooble_jobs,
    fetch_remotive_jobs,
    normalize_jooble,
    normalize_remotive,
    prune_stale_jobs,
    refresh_jobs,
    strip_html,
)

REMOTIVE_SAMPLE = {
    "jobs": [
        {
            "url": "https://remotive.com/remote-jobs/software-dev/backend-dev-1",
            "title": "Backend Developer",
            "company_name": "Acme",
            "candidate_required_location": "Worldwide",
            "category": "Software Development",
            "description": "<p>Build <b>APIs</b> &amp; services.</p>",
            "tags": ["Python", "django", " ", "python"],
        },
        {"url": "", "title": "No URL"},            # dropped
        {"url": "https://x.test/1", "title": ""},  # dropped
    ]
}

JOOBLE_SAMPLE = {
    "totalCount": 1,
    "jobs": [
        {
            "title": "Data Analyst",
            "location": "Makati, Metro Manila",
            "snippet": "Work with <b>SQL</b> &amp; dashboards.",
            "company": "Globe",
            "link": "https://ph.jooble.org/jdp/123",
            "salary": "",
        }
    ],
}


class NormalizeTests(SimpleTestCase):
    def test_strip_html_unescapes_and_collapses(self):
        assert strip_html("<p>Build  <b>APIs</b> &amp; services.</p>") == "Build APIs & services."

    def test_strip_html_truncates(self):
        assert len(strip_html("word " * 500, limit=20)) == 20

    def test_remotive_dedupes_and_lowercases_tags(self):
        row = normalize_remotive(REMOTIVE_SAMPLE["jobs"][0])
        assert row["skills"] == "django, python"
        assert row["company"] == "Acme"
        assert row["description"] == "Build APIs & services."
        assert row["source"] == "remotive"

    def test_remotive_drops_spam_tag_lists(self):
        posting = {**REMOTIVE_SAMPLE["jobs"][0], "tags": [f"stack{i}" for i in range(50)]}
        assert normalize_remotive(posting)["skills"] == ""

    def test_remotive_rejects_postings_without_url_or_title(self):
        assert normalize_remotive(REMOTIVE_SAMPLE["jobs"][1]) is None
        assert normalize_remotive(REMOTIVE_SAMPLE["jobs"][2]) is None

    def test_jooble_maps_link_and_snippet(self):
        row = normalize_jooble(JOOBLE_SAMPLE["jobs"][0])
        assert row["url"] == "https://ph.jooble.org/jdp/123"
        assert row["location"] == "Makati, Metro Manila"
        assert row["description"] == "Work with SQL & dashboards."
        assert row["source"] == "jooble"

    def test_oversized_url_is_dropped_not_truncated(self):
        assert normalize_jooble({"link": "https://x.test/" + "a" * 500, "title": "Dev"}) is None


class ExtractSkillsBatchTests(SimpleTestCase):
    def extract(self, model_result, count=2):
        with patch("apps.jobs.tasks.ask_model", return_value=model_result) as mock_ask:
            result = extract_skills_batch(["posting a", "posting b"][:count])
            self.prompt = mock_ask.call_args.args[0]
            return result

    def test_maps_numbered_keys_back_to_input_order(self):
        assert self.extract({"0": ["SQL", " Excel ", "sql"], "1": ["Nursing"]}) == [
            "excel, sql",
            "nursing",
        ]

    def test_all_postings_appear_in_one_prompt(self):
        self.extract({"0": [], "1": []})
        assert "posting a" in self.prompt and "posting b" in self.prompt

    def test_skipped_key_holes_instead_of_shifting_later_results(self):
        # The model omitting posting 0 must not slide posting 1's skills onto it.
        assert self.extract({"1": ["Nursing"]}) == ["", "nursing"]

    def test_extra_and_malformed_keys_are_ignored(self):
        assert self.extract({"0": "SQL", "1": ["Excel"], "7": ["Ghost"]}) == ["", "excel"]

    def test_model_failure_yields_one_empty_entry_per_input(self):
        # ask_model returns None when Ollama is down, {} on bad output; neither may abort a fetch.
        assert self.extract(None) == ["", ""]
        assert self.extract({}) == ["", ""]
        assert self.extract([1, 2, 3]) == ["", ""]


class FetchTests(TestCase):
    def setUp(self):
        patcher = patch("apps.jobs.tasks.embed")
        self.mock_model = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_model.side_effect = lambda texts: np.zeros(
            (len(texts), 384), dtype=np.float32
        )

        # No test may reach a real Ollama; tests that care re-patch this.
        ask_patcher = patch("apps.jobs.tasks.ask_model", return_value={})
        ask_patcher.start()
        self.addCleanup(ask_patcher.stop)

    @patch("apps.jobs.tasks.requests.get")
    def test_remotive_upserts_by_url(self, mock_get):
        mock_get.return_value.json.return_value = REMOTIVE_SAMPLE

        assert fetch_remotive_jobs(limit=10)["created"] == 1

        # Re-running must update in place, never duplicate the posting.
        assert fetch_remotive_jobs(limit=10)["created"] == 0
        assert Job.objects.count() == 1
        assert Job.objects.get().url.endswith("backend-dev-1")

    @patch.dict("os.environ", {"JOOBLE_API_KEY": "testkey"})
    @patch("apps.jobs.tasks.requests.post")
    def test_jooble_posts_key_in_url_and_ingests(self, mock_post):
        mock_post.return_value.json.return_value = JOOBLE_SAMPLE

        assert fetch_jooble_jobs(search="data", location="Philippines", limit=10)["created"] == 1

        url, = mock_post.call_args.args
        assert url.endswith("testkey")
        assert mock_post.call_args.kwargs["json"]["location"] == "Philippines"
        assert Job.objects.get().location == "Makati, Metro Manila"

    @patch.dict("os.environ", {"JOOBLE_API_KEY": "testkey"})
    @patch("apps.jobs.tasks.ask_model", return_value={"0": ["SQL", "Dashboards"]})
    @patch("apps.jobs.tasks.requests.post")
    def test_jooble_fills_skills_from_the_snippet(self, mock_post, mock_ask):
        mock_post.return_value.json.return_value = JOOBLE_SAMPLE

        fetch_jooble_jobs(limit=10)

        assert Job.objects.get().skills == "dashboards, sql"
        # The snippet, not the raw HTML, is what the model sees.
        assert "Work with SQL & dashboards." in mock_ask.call_args.args[0]

    @patch.dict("os.environ", {"JOOBLE_API_KEY": "testkey"})
    @patch("apps.jobs.tasks.ask_model", return_value={"0": ["SQL"]})
    @patch("apps.jobs.tasks.requests.post")
    def test_jooble_reuses_stored_skills_on_refetch(self, mock_post, mock_ask):
        mock_post.return_value.json.return_value = JOOBLE_SAMPLE

        fetch_jooble_jobs(limit=10)
        fetch_jooble_jobs(limit=10)

        # Second run must not re-pay the LLM call for a posting already extracted.
        assert mock_ask.call_count == 1
        assert Job.objects.get().skills == "sql"

    @patch.dict("os.environ", {"JOOBLE_API_KEY": "testkey"})
    @patch("apps.jobs.tasks.requests.post")
    def test_jooble_batches_postings_instead_of_one_call_each(self, mock_post):
        count = JOB_SKILL_BATCH_SIZE * 2 + 3
        mock_post.return_value.json.return_value = {
            "jobs": [
                dict(JOOBLE_SAMPLE["jobs"][0], link=f"https://ph.jooble.org/jdp/{i}")
                for i in range(count)
            ]
        }

        with patch("apps.jobs.tasks.ask_model", return_value={}) as mock_ask:
            fetch_jooble_jobs(limit=count)

        assert mock_ask.call_count == 3
        assert Job.objects.count() == count

    @patch.dict("os.environ", {"JOOBLE_API_KEY": "testkey"})
    @patch("apps.jobs.tasks.requests.post")
    def test_jooble_stops_paging_on_short_page(self, mock_post):
        mock_post.return_value.json.return_value = JOOBLE_SAMPLE

        fetch_jooble_jobs(limit=JOOBLE_PAGE_SIZE * 5)

        assert mock_post.call_count == 1

    @patch.dict("os.environ", {"JOOBLE_API_KEY": ""})
    def test_jooble_without_key_raises_instead_of_silently_doing_nothing(self):
        with self.assertRaisesMessage(RuntimeError, "JOOBLE_API_KEY"):
            fetch_jooble_jobs()



class StalenessTests(TestCase):
    def make_job(self, url, days_ago):
        job = Job.objects.create(title="Dev", url=url, embedding=[0.0] * 384)
        # last_seen is auto_now, so it cannot be set on create — write it directly.
        Job.objects.filter(pk=job.pk).update(
            last_seen=timezone.now() - timedelta(days=days_ago)
        )
        return job

    def test_fresh_excludes_postings_past_the_window(self):
        recent = self.make_job("https://x.test/recent", days_ago=1)
        self.make_job("https://x.test/old", JOB_STALE_AFTER.days + 1)

        assert list(Job.fresh()) == [recent]

    def test_prune_removes_only_stale_postings(self):
        self.make_job("https://x.test/recent", days_ago=1)
        self.make_job("https://x.test/old", JOB_STALE_AFTER.days + 1)

        assert prune_stale_jobs() == 1
        assert Job.objects.count() == 1
        assert Job.objects.get().url.endswith("recent")

    @patch("apps.jobs.tasks.embed")
    @patch("apps.jobs.tasks.requests.get")
    def test_refetching_a_posting_marks_it_seen_again(self, mock_get, mock_model):
        mock_model.side_effect = lambda texts: np.zeros(
            (len(texts), 384), dtype=np.float32
        )
        mock_get.return_value.json.return_value = REMOTIVE_SAMPLE
        url = REMOTIVE_SAMPLE["jobs"][0]["url"]

        fetch_remotive_jobs(limit=10)
        Job.objects.filter(url=url).update(last_seen=timezone.now() - timedelta(days=30))
        assert not Job.fresh().exists()

        fetch_remotive_jobs(limit=10)

        # Still listed upstream, so it must come back into the fresh set.
        assert Job.fresh().count() == 1


class RefreshJobsTests(TestCase):
    def setUp(self):
        patcher = patch("apps.jobs.tasks.embed")
        patcher.start().side_effect = lambda texts: np.zeros(
            (len(texts), 384), dtype=np.float32
        )
        self.addCleanup(patcher.stop)

        ask_patcher = patch("apps.jobs.tasks.ask_model", return_value={})
        ask_patcher.start()
        self.addCleanup(ask_patcher.stop)

    def stale_job(self):
        job = Job.objects.create(title="Old", url="https://x.test/old", embedding=[0.0] * 384)
        Job.objects.filter(pk=job.pk).update(
            last_seen=timezone.now() - timedelta(days=JOB_STALE_AFTER.days + 1)
        )

    @patch.dict("os.environ", {"JOOBLE_API_KEY": ""})
    @patch("apps.jobs.tasks.requests.get")
    def test_prunes_when_a_source_returned_postings(self, mock_get):
        mock_get.return_value.json.return_value = REMOTIVE_SAMPLE
        self.stale_job()

        result = refresh_jobs()

        assert result["pruned"] == 1
        assert not Job.objects.filter(url="https://x.test/old").exists()

    @patch.dict("os.environ", {"JOOBLE_API_KEY": ""})
    @patch("apps.jobs.tasks.requests.get")
    def test_does_not_prune_when_every_source_failed(self, mock_get):
        # Pruning behind a failed fetch would empty the table instead of refreshing it.
        mock_get.side_effect = RuntimeError("network down")
        self.stale_job()

        result = refresh_jobs()

        assert result["pruned"] == 0
        assert Job.objects.filter(url="https://x.test/old").exists()

    @patch.dict("os.environ", {"JOOBLE_API_KEY": ""})
    @patch("apps.jobs.tasks.requests.get")
    def test_a_source_without_credentials_does_not_block_the_others(self, mock_get):
        mock_get.return_value.json.return_value = REMOTIVE_SAMPLE

        result = refresh_jobs()

        assert "JOOBLE_API_KEY" in result["jooble"]["skipped"]
        assert result["remotive"]["created"] == 1
