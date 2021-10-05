from django.db import models


# Create your models here.
# class MediaType(models.Model):
#     """
#     type can "music", "meditation", "audiobook" etc.
#     (maybe even "channel"?? "channel" is not a local media though... we'll see)
#     """
#     media_type = models.CharField(max_length=200, unique=True, blank=False, null=False, default=None)
#
#     def __str__(self):
#         return self.media_type


class Artist(models.Model):
    name = models.CharField(max_length=200, unique=True, blank=False, null=False)
    cover_online = models.CharField(max_length=200, unique=False, blank=True, null=True)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Album(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT)
    album_title = models.CharField(max_length=200, unique=False, blank=False)
    year = models.CharField(max_length=200, unique=False, blank=True, null=False)
    # audio_format = models.CharField(max_length=200, unique=False)
    cover = models.CharField(max_length=200, unique=False, blank=True, null=True)

    cover_online = models.CharField(max_length=200, unique=False, blank=True, null=True)

    def __str__(self):
        # return '{0} ({1})'.format(self.album_title, self.artist_id.name)
        return f'{self.album_title} ({self.artist.name})'

    def __repr__(self):
        # return '{0} ({1})'.format(self.album_title, self.artist_id.name)
        return f'{self.album_title} ({self.artist.name})'


class Track(models.Model):
    album = models.ForeignKey(Album, on_delete=models.PROTECT, null=True)
    # media_type = models.ForeignKey(MediaType, on_delete=models.PROTECT, null=True)
    # track_title = models.CharField(max_length=200, unique=False)
    audio_source = models.CharField(max_length=200, unique=True, blank=False, null=False)
    # title = models.CharField(max_length=200, unique=False, blank=False, null=False)
    played = models.IntegerField(default=0, unique=False)

    def __str__(self):
        return self.audio_source

    def __repr__(self):
        return self.audio_source


class Channel(models.Model):
    display_name = models.CharField(max_length=200, unique=True, null=False, blank=False)
    display_name_short = models.CharField(max_length=200, unique=True, null=False, blank=False)
    url = models.URLField(max_length=200, unique=True, null=False, blank=False)
    url_logo = models.URLField(max_length=200, unique=False, null=True, blank=True)
    is_enabled = models.BooleanField(default=True)
    last_played = models.BooleanField(default=False)
    show_rds = models.BooleanField(default=True)

    def __str__(self):
        return self.display_name_short

    def __repr__(self):
        return self.display_name_short
