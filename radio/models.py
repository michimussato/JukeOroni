from django.db import models

# Create your models here.
from django.db import models


class Channel(models.Model):
    display_name = models.CharField(max_length=200, unique=True)
    display_name_short = models.CharField(max_length=200, unique=True)
    url = models.URLField(max_length=200, unique=True)
    url_logo = models.URLField(max_length=200, unique=False, null=True, blank=True)
    is_enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.display_name
