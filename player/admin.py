from django.contrib import admin
from django_object_actions import DjangoObjectActions


# Register your models here.
from .models import Artist, Album, Track, Channel, Station, Podcast, Episode, Video


"""
https://pythonprogramming.net/working-foreign-keys-django-tutorial/?completed=/foreign-keys-django-tutorial/

class TutorialAdmin(admin.ModelAdmin):

    fieldsets = [
        ("Title/date", {'fields': ["tutorial_title", "tutorial_published"]}),
        ("URL", {'fields': ["tutorial_slug"]}),
        ("Series", {'fields': ["tutorial_series"]}),
        ("Content", {"fields": ["tutorial_content"]})
    ]

    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(attrs={'cols': 80, 'rows': 30})},
        }


admin.site.register(TutorialSeries)
admin.site.register(TutorialCategory)
admin.site.register(Tutorial,TutorialAdmin)
"""


class AlbumAdmin(admin.ModelAdmin):
    list_display = ('album_title', 'artist_name', 'year', 'album_type')
    search_fields = ['album_title', 'artist__name']
    ordering = ('artist__name', 'year', 'album_title')

    def artist_name(self, obj):
        return None if obj.artist is None else obj.artist.name

    artist_name.short_description = 'Artist'


class StationAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'channel_count')
    search_fields = ['display_name']

    def channel_count(self, obj):
        channels = Channel.objects.filter(station_id=obj.id)
        return len(channels)

    channel_count.short_description = 'Channels'


class ChannelAdmin(admin.ModelAdmin):
    fieldsets = [('Name', {'fields': ['display_name', 'display_name_short', 'station']}),
                 ('URL\'s', {'fields': ['url', 'url_logo']}),
                 ('Options', {'fields': ['is_enabled', 'show_rds']}),
                 ('Auto Playback', {'fields': ['last_played']})]
    list_display = ('display_name', 'station_display_name', 'show_rds', 'is_enabled')
    search_fields = ['display_name', 'station__display_name']
    # autocomplete_fields = ['display_name']

    def station_display_name(self, obj):
        return None if obj.station is None else obj.station.display_name

    station_display_name.short_description = 'Station'


class AristAdmin(admin.ModelAdmin):
    list_display = ('name', 'album_count', 'track_count')
    search_fields = ['name']
    ordering = ('name',)

    def album_count(self, obj):
        albums = Album.objects.filter(artist_id=obj.id)
        return len(albums)

    album_count.short_description = 'Albums'

    def track_count(self, obj):
        tracks = Track.objects.filter(album__artist_id=obj.id)
        return len(tracks)

    track_count.short_description = 'Tracks'


class TrackAdmin(admin.ModelAdmin):
    list_display = ('artist_name', 'album_year', 'album_album_title', 'track_title')
    search_fields = ['track_title', 'album__album_title', 'album__artist__name']
    ordering = ('album__artist__name', 'album__year', 'album__album_title')

    def album_year(self, obj):
        return None if obj.album is None else obj.album.year

    album_year.short_description = 'Year'

    def album_album_title(self, obj):
        return None if obj.album is None else obj.album.album_title

    album_album_title.short_description = 'Album'

    def artist_name(self, obj):
        if obj.album is None:
            return None
        return None if obj.album.artist is None else obj.album.artist.name

    artist_name.short_description = 'Artist'


class VideoAdmin(DjangoObjectActions, admin.ModelAdmin):
    video = None

    def play_pause(self, request, obj):
        if isinstance(self.video, Video) and self.video is not obj:
            self._stop()
            self.video = None

        if self.video is None:
            self.video = obj
            self.video.play()
        else:
            self.video.play_pause()

    def _stop(self):
        self.video.stop()
        self.video = None

    def stop(self, request, obj):
        if self.video is not None:
            self.video.stop()
            self.video = None

    play_pause.label = 'Play/Pause'
    # play_pause.short_description = 'Desc'

    stop.label = 'Stop'

    list_display = ('video_title', 'video_source')
    search_fields = ['video_title', 'video_source']
    change_actions = ('play_pause', 'stop')


admin.site.register(Artist, AristAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Track, TrackAdmin)
admin.site.register(Station, StationAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Podcast)
admin.site.register(Episode)
