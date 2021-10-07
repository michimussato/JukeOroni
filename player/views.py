import signal
import time

from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from player.jukeoroni.jukeoroni import JukeOroni
from player.jukeoroni.juke_box import JukeboxTrack
from player.models import Album, Channel, Station
from player.jukeoroni.settings import (
    _JUKEBOX_LOADING_IMAGE,
    MODES
)


PIMORONI_SATURATION = 1.0
FONT_SIZE = 24
SLEEP_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
STANDARD_COVER = '/data/django/jukeoroni/player/static/cover_std.png'
PIMORONI_FONT = '/data/django/jukeoroni/player/static/gotham-black.ttf'


jukeoroni = JukeOroni(test=False)
jukeoroni.turn_on()
# # jukeoroni.jukebox.set_auto_update_tracklist_on()


# Create your views here.
# TODO: rmove player for unittesting new juke
class JukeOroniView(View):

    # jukeoroni = JukeOroni()
    # jukeoroni.test = False
    # jukeoroni.turn_on()

    # jukeoroni.jukebox.set_auto_update_tracklist_on()

    def get(self, request):
        global jukeoroni

        # return HttpResponse('Hello JukeOroni')
        ret = '<html>\n'
        ret += '  <head>\n'
        ret += '    <meta http-equiv="refresh" content="10" >\n'
        ret += '  </head>\n'
        ret += '  <body>\n'

        # if isinstance(jukeoroni.inserted_media, JukeboxTrack):
        if jukeoroni.mode == MODES['radio']['standby'] \
                or jukeoroni.mode == MODES['radio']['on_air'] \
                or True:

            return HttpResponseRedirect('radio/')

        else:

            # if self.jukeoroni.inserted_media is None:
            #     ret += f'<div>{str(self.jukeoroni.inserted_media)}</div>'
            # else:
            _success = False
            while not _success:
                try:
                    ret += f'<div>'

                    cover_artist = jukeoroni.inserted_media.artist.cover_online
                    # if cover_artist.startswith(os.sep):
                    #     cover_artist = f'file://{parse.quote(cover_artist)}'
                    # # ret += f'<div>Artist: {cover_artist}</div>'
                    # if jukeoroni.inserted_media.album.cover_online or jukeoroni.inserted_media.album.cover:
                    cover_album = jukeoroni.inserted_media.album.cover_online or jukeoroni.inserted_media.album.cover
                    # if cover_album.startswith(os.sep):
                    #     cover_album = f'file://{cover_album}'
                    # # ret += f'<div>Album: {cover_album}</div>'

                    # ret += f'<img src=\"{cover_album}\" alt=\"{str(player.playing_track.path)}\">'
                    if bool(cover_album):
                        ret += f'<img src=\"{str(cover_album)}\" alt=\"{str(cover_album)}\">'
                    # ret += f'<img src=\"{cover_artist}\" alt=\"{str(player.playing_track.path)}\">'
                    if bool(cover_artist):
                        ret += f'<img src=\"{str(cover_artist)}\" alt=\"{str(cover_artist)}\">'
                    ret += f'</div>'
                    ret += f'<div>Artist: {str(jukeoroni.inserted_media.artist)}</div>'
                    ret += f'<div>Album: {str(jukeoroni.inserted_media.album)}</div>'
                    ret += f'<div>Track: {str(jukeoroni.inserted_media.track_title)}</div>'
                    _success = True
                except AttributeError as err:
                    print(err)
                    time.sleep(1.0)

        ret += f'<hr>'
        ret += '<div>Tracks in queue: (loading: {0})</div>'.format(jukeoroni.jukebox.loading_process is not None)
        ret += f'<ol>'
        for track in jukeoroni.jukebox.tracks:
            ret += '<li>{0}</li>'.format(track)
        ret += f'</ol>'
        ret += f'<hr>'
        # if not jukeoroni.jukebox.tracks and bool(jukeoroni.jukebox.loading_process):
        #     ret += '<div><img src=\"file://{0}\" alt=\"Loading {1}...\"></div>'.format(_JUKEBOX_LOADING_IMAGE, str(jukeoroni.jukebox.loading_process._kwargs['track']))
        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/switch_mode\';\">Mode: {0}</button>\n'.format(str(jukeoroni.jukebox.loader_mode))
        if not jukeoroni.mode == MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['album']:
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/play_next\';\">{0}</button>\n'.format('Play')
        else:
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/play_next\';\">{0}</button>\n'.format(jukeoroni.mode['buttons']['0X00'])
        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/stop\';\">Stop</button>\n'
        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/albums\';\">Albums</button>\n'
        ret += '  </body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def switch_mode(self):
        global jukeoroni

        if jukeoroni.jukebox.loader_mode == 'random':
            jukeoroni.jukebox.set_loader_mode_album()
        elif jukeoroni.jukebox.loader_mode == 'album':
            jukeoroni.jukebox.set_loader_mode_random()
        return HttpResponseRedirect('/jukeoroni')

    def play_next(self):
        global jukeoroni

        jukeoroni.set_mode_jukebox()
        jukeoroni.play()

        # player.button_3_value = BUTTON_3['Play']
        # # while player._playback_thread is None:
        # #     time.sleep(1.0)
        # # time.sleep(1.0)
        return HttpResponseRedirect('/jukeoroni')

    def stop(self):
        global jukeoroni

        jukeoroni.stop()
        return HttpResponseRedirect('/jukeoroni')

    def albums(self):
        global jukeoroni
        albums = Album.objects.all()

        ret = '<html>\n'
        # ret += '  <head>\n'
        # ret += '    <meta http-equiv="refresh" content="10" >\n'
        # ret += '  </head>\n'
        ret += '  <body>\n'
        previous_artist = None
        for album in albums:
            ret += '  <div>\n'
            if album.artist != previous_artist:
                ret += f'{album.artist}'
            previous_artist = album.artist
            # ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/player/stop\';\">Stop</button>\n'
            # ret += f'    <button style=\"width:100%\">{album.album_title}</button>\n'
            ret += f'        <button style=\"width:100%\" onclick=\"window.location.href = \'{album.id}\';\">{album.album_title}</button>\n'
            ret += '  </div>\n'
        ret += '  </body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def play_album(self, album_id):
        global jukeoroni

        jukeoroni.jukebox.play_album(album_id=album_id)
        # jukeoroni.set_mode_jukebox()

        # jukeoroni.jukebox.kill_loading_process()

        # # jukeoroni.jukebox.kill_loading_process()
        # # if not jukeoroni.jukebox.loader_mode == 'album':
        # # print(jukeoroni.jukebox.loading_process.pid)
        # # print(jukeoroni.jukebox.loading_process.pid)
        # # print(jukeoroni.jukebox.loading_process.pid)
        # # print(jukeoroni.jukebox.loading_process.pid)
        # # import pdb;pdb.set_trace()
        # # signal.pthread_kill(jukeoroni.jukebox.loading_process.pid, signal.SIGINT.value)
        # # if jukeoroni.jukebox.loader_mode != 'album':
        # #     jukeoroni.jukebox.set_loader_mode_album()
        # # jukeoroni.jukebox._need_first_album_track = False
        # jukeoroni.jukebox.requested_album_id = album_id
        # jukeoroni.jukebox.set_loader_mode_album()
        # # jukeoroni.insert(jukeoroni.jukebox.next_track)
        # # self.jukeoroni.mode = MODES['jukebox']['on_air'][self.jukeoroni.jukebox.loader_mode]
        # jukeoroni.set_mode_jukebox()
        # # self.switch_mode()
        jukeoroni.play()
        jukeoroni.set_mode_jukebox()
        # self.jukeoroni.button_1_value = 'Albm -> Rand'

        # self.jukeoroni.set_image(track=self.jukeoroni.playing_track)

        return HttpResponseRedirect('/jukeoroni')

    def radio_index(self):
        global jukeoroni

        stations = Station.objects.all().order_by('display_name')

        ret = '<html>\n'
        ret += '<head>\n'
        ret += '<meta http-equiv="refresh" content="10" >\n'
        ret += '</head>\n'
        ret += '<body>\n'
        for station in stations:
            channels = Channel.objects.filter(station=station).order_by('display_name')
            if channels:
                ret += f'<h2 style="text-align:center">{station.display_name}</h2>\n'
            for channel in channels:
                if channel.is_enabled:
                    if channel == jukeoroni.radio.is_on_air:
                        ret += f'<button style=\"width:100%; background-color:green; \" onclick=\"window.location.href = \'stop\';\">{channel.display_name}</button>\n'
                    else:
                        ret += f'<button style=\"width:100%\" onclick=\"window.location.href = \'{channel.display_name_short}/play\';\">{channel.display_name}</button>\n'
        ret += '</body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def radio_play(self, display_name_short):
        global jukeoroni

        try:
            for c in Channel.objects.filter(last_played=True):
                c.last_played = False
                c.save()
        except Channel.DoesNotExist:
            pass

        channel = Channel.objects.get(display_name_short=display_name_short)
        if jukeoroni.inserted_media is not None:
            if jukeoroni.radio.is_on_air:
                jukeoroni.stop()
            jukeoroni.eject()
        jukeoroni.insert(media=channel)

        channel.last_played = True
        channel.save()

        jukeoroni.mode = MODES['radio']['on_air']
        # try:
        jukeoroni.play()
        # except Exception:

        jukeoroni.set_display_radio()

        return HttpResponseRedirect('/jukeoroni')

    def radio_stop(self):
        global jukeoroni

        jukeoroni.stop()
        jukeoroni.eject()

        return HttpResponseRedirect('/jukeoroni')
