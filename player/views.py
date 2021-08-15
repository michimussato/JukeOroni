from django.http import HttpResponseRedirect
from django.views import View


PIMORONI_SATURATION = 1.0
FONT_SIZE = 24
SLEEP_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
STANDARD_COVER = '/data/django/jukeoroni/player/static/cover_std.png'
PIMORONI_FONT = '/data/django/jukeoroni/player/static/gotham-black.ttf'


# Create your views here.
# TODO: rmove player for unittesting new juke
class PlayerView(View):

    def get(self, request):
        return HttpResponseRedirect('/player')

    def switch_mode(self):
        return HttpResponseRedirect('/player')

    def play_next(self):
        return HttpResponseRedirect('/player')

    def stop(self):
        return HttpResponseRedirect('/player')

    def albums(self):
        return HttpResponseRedirect('/player')

    def play_album(self, album_id):
        return HttpResponseRedirect('/player')
