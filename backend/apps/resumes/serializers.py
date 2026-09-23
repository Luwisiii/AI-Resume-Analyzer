import os

from rest_framework import serializers
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    # The name only, never the storage path or a media URL.
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        # Explicit, not "__all__": extracted_text is the candidate's full resume
        # and embedding is 384 floats — neither belongs in a response the client
        # polls every second.
        fields = ["id", "file_name", "skills", "ai_feedback", "uploaded_at"]
        read_only_fields = fields

    def get_file_name(self, resume):
        return os.path.basename(resume.file.name)
