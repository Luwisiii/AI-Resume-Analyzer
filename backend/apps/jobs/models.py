from datetime import timedelta

from django.db import models
from pgvector.django import VectorField
from django.utils import timezone

# A posting that has stopped appearing in its feed has almost certainly closed.
# ponytail: one window for every source. Split it per-source if their listings
# turn over at very different rates.
JOB_STALE_AFTER = timedelta(days=14)


class Job(models.Model):
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    url = models.URLField(max_length=500, unique=True, null=True, blank=True)
    source = models.CharField(max_length=50, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    description = models.TextField(default="")
    skills = models.TextField(blank=True)
    embedding = VectorField(dimensions=384, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    # Touched every time a fetch re-confirms the posting is still listed.
    # created_at cannot serve this: update_or_create leaves it at its original value.
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @classmethod
    def fresh(cls):
        """Postings confirmed present recently — the only ones worth matching against."""
        return cls.objects.filter(last_seen__gte=timezone.now() - JOB_STALE_AFTER)

    @property
    def skills_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()]
