from django.contrib import admin

# Register your models here.

from .models import SocialAccount

admin.site.register(SocialAccount)
