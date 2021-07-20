from django.contrib import admin


# Register your models here.
from .models import Artist, Album, Track
# from .models import Track

admin.site.register(Artist)
admin.site.register(Album)
admin.site.register(Track)
