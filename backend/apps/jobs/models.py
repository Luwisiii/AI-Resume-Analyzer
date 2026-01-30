from django.db import models
from pgvector.django import VectorField
from django.utils import timezone

class Job(models.Model):
    title = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True)
    description = models.TextField(default="")
    skills = models.TextField(blank=True)
    embedding = VectorField(dimensions=384, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
