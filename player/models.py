from django.db import models


# Create your models here.
# class Artist(models.Model):
#     name = models.CharField(max_length=200, unique=True)
#
#
# class Album(models.Model):
#     artist = models.ForeignKey(Artist, on_delete=models.PROTECT)
#     album_title = models.CharField(max_length=200, unique=False)
#     year = models.CharField(max_length=200, unique=False)
#     audio_format = models.CharField(max_length=200, unique=False)


class Track(models.Model):
    # album = models.ForeignKey(Album, on_delete=models.PROTECT)
    # track_title = models.CharField(max_length=200, unique=False)
    audio_source = models.FilePathField(max_length=200, unique=True, blank=False)

    # def __str__(self):
    #     return self.audio_source
