from django.conf import settings
from django.db import models


class SocialAccount(models.Model):
    """A Google or GitHub identity that signs in as `user`. Keyed on the provider's
    own stable id, not the email, which the user can change on the provider."""

    provider = models.CharField(max_length=20)
    uid = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="social_accounts")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["provider", "uid"], name="unique_provider_uid")]

    def __str__(self):
        return f"{self.provider}:{self.uid}"
