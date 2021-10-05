from django.contrib import admin


# Register your models here.
from .models import Artist, Album, Track, Channel, Station


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


admin.site.register(Artist)
admin.site.register(Album)
admin.site.register(Track)
admin.site.register(Station)
admin.site.register(Channel)
