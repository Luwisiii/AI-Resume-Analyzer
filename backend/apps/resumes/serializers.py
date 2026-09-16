from rest_framework import serializers
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        # Explicit, not "__all__": extracted_text is the candidate's full resume
        # and embedding is 384 floats — neither belongs in a response the client
        # polls every two seconds.
        fields = ["id", "file", "skills", "ai_feedback", "uploaded_at"]
        read_only_fields = fields
