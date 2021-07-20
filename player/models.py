from django.db import models


# Create your models here.
class Artist(models.Model):
    name = models.CharField(max_length=200, unique=True, blank=False, null=False)

    def __str__(self):
        return self.name


class Album(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT)
    album_title = models.CharField(max_length=200, unique=True, blank=False)
    year = models.CharField(max_length=200, unique=False, blank=True, null=False)
    # audio_format = models.CharField(max_length=200, unique=False)
    cover = models.CharField(max_length=200, unique=False, blank=True, null=False)

    def __str__(self):
        return self.album_title


class Track(models.Model):
    album = models.ForeignKey(Album, on_delete=models.PROTECT)
    # track_title = models.CharField(max_length=200, unique=False)
    audio_source = models.CharField(max_length=200, unique=True, blank=False, null=False)

    def __str__(self):
        return self.audio_source
