from django.contrib import admin


# Register your models here.
from .models import Artist, Album, Track, Channel

admin.site.register(Artist)
admin.site.register(Album)
admin.site.register(Track)
admin.site.register(Channel)
