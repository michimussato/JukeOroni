from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from player.jukeoroni.jukeoroni import JukeOroni


PIMORONI_SATURATION = 1.0
FONT_SIZE = 24
SLEEP_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
STANDARD_COVER = '/data/django/jukeoroni/player/static/cover_std.png'
PIMORONI_FONT = '/data/django/jukeoroni/player/static/gotham-black.ttf'


jukeoroni = JukeOroni()
jukeoroni.test = False
jukeoroni.turn_on()
jukeoroni.jukebox.set_auto_update_tracklist_on()


# Create your views here.
# TODO: rmove player for unittesting new juke
class JukeOroniView(View):

    def get(self, request):
        global jukeoroni
        return HttpResponse('Hello JukeOroni')

    # def switch_mode(self):
    #     return HttpResponseRedirect('/player')
    #
    # def play_next(self):
    #     return HttpResponseRedirect('/player')
    #
    # def stop(self):
    #     return HttpResponseRedirect('/player')
    #
    # def albums(self):
    #     return HttpResponseRedirect('/player')
    #
    # def play_album(self, album_id):
    #     return HttpResponseRedirect('/player')
