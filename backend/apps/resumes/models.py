from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from pgvector.django import VectorField
from django.contrib.postgres.fields import JSONField

User = get_user_model()

class Resume(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to="resumes/")
    extracted_text = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    ai_feedback = models.JSONField(blank=True, null=True)
    embedding = VectorField(dimensions=384, null=True)
    uploaded_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.file.name
    
    @property
    def skills_list(self):
        return [s.strip() for s in self.skills.split(",")] if self.skills else []
