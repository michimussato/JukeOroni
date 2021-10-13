import base64
import signal
import time
import io
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

        # # return HttpResponse('Hello JukeOroni')
        # ret = '<html>\n'
        # ret += '  <head>\n'
        # ret += '    <meta http-equiv="refresh" content="10" >\n'
        # ret += '  </head>\n'
        # ret += '  <body>\n'

        # if isinstance(jukeoroni.inserted_media, JukeboxTrack):
        if jukeoroni.mode == MODES['radio']['standby'] \
                or jukeoroni.mode == MODES['radio']['on_air']:

            return HttpResponseRedirect('radio/')

        elif jukeoroni.mode == MODES['jukebox']['standby']['album'] \
                or jukeoroni.mode == MODES['jukebox']['standby']['random'] \
                or jukeoroni.mode == MODES['jukebox']['on_air']['album'] \
                or jukeoroni.mode == MODES['jukebox']['on_air']['random']:

            return HttpResponseRedirect('jukebox/')

        elif jukeoroni.mode == MODES['jukeoroni']['standby'] \
                or jukeoroni.mode == MODES['jukeoroni']['off']:

            ret = '<html>\n'
            ret += '  <head>\n'
            ret += '    <meta http-equiv="refresh" content="10" >\n'
            ret += '  </head>\n'
            ret += '  <body>\n'
            ret += '<div style=\"text-align:center\">Hello JukeOroni</div>\n'
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_jukebox\';\">Activate Jukebox</button>\n'
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_radio\';\">Activate Radio</button>\n'

            data = io.BytesIO()
            img = jukeoroni.layout_standby.get_layout(labels=jukeoroni.LABELS)
            img = img.rotate(270, expand=True)
            img.save(data, "PNG")
            encoded_img_data = base64.b64encode(data.getvalue())

            # print(encoded_img_data)
            # print(encoded_img_data)
            # print(encoded_img_data)
            # print(encoded_img_data)

            ret += '<img id="picture" style="display:block;margin-left:auto;margin-right:auto;" src="data:image/jpeg;base64,{0}">\n'.format(str(encoded_img_data).lstrip('b\'').rstrip('\''))
            ret += '</body>\n'
            ret += '</html>\n'

            return HttpResponse(ret)

        # else:
        #
    def set_jukebox(self):
        global jukeoroni

        jukeoroni.mode = MODES['jukebox']['standby'][jukeoroni.jukebox.loader_mode]

        return HttpResponseRedirect('/jukeoroni/jukebox')

    def set_radio(self):
        global jukeoroni

        jukeoroni.mode = MODES['radio']['standby']

        return HttpResponseRedirect('/jukeoroni/radio')

    def set_standby(self):
        global jukeoroni

        jukeoroni.mode = MODES['jukeoroni']['standby']

        return HttpResponseRedirect('/jukeoroni')

    def jukebox_index(self):

        global jukeoroni

        if not jukeoroni.mode == MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['album']:

        # if jukeoroni.mode != MODES['radio']['standby'] \
        #         and jukeoroni.mode != MODES['radio']['on_air']:

            return HttpResponseRedirect('/jukeoroni')

        # if self.jukeoroni.inserted_media is None:
        #     ret += f'<div>{str(self.jukeoroni.inserted_media)}</div>'
        # else:

        # if jukeoroni.inserted_media is None:
        #     return HttpResponseRedirect('/jukeoroni')

        ret = '<html>\n'
        ret += '  <head>\n'
        ret += '    <meta http-equiv="refresh" content="10" >\n'
        ret += '  </head>\n'
        ret += '  <body>\n'
        ret += f'<button style=\"width:100%; \" onclick=\"window.location.href = \'/jukeoroni/set_standby\';\">Back to Standby</button>\n'
        ret += '<hr>\n'

        _success = False

        data = io.BytesIO()
        if jukeoroni.mode == MODES['jukebox']['standby']['album'] \
                or jukeoroni.mode == MODES['jukebox']['standby']['random']:
            img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS)
        elif jukeoroni.mode == MODES['jukebox']['on_air']['album'] \
                or jukeoroni.mode == MODES['jukebox']['on_air']['random']:
            # if self.inserted_media is None:
            try:
                img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.inserted_media.cover_album,
                                                    artist=jukeoroni.inserted_media.cover_artist)
            except AttributeError:
                img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS, loading=True)
                # LOG.exception('inserted_media problem: ')
        img = img.rotate(270, expand=True)
        img.save(data, "PNG")
        encoded_img_data = base64.b64encode(data.getvalue())

        # print(encoded_img_data)
        # print(encoded_img_data)
        # print(encoded_img_data)
        # print(encoded_img_data)

        ret += '<img id="picture" style="display:block;margin-left:auto;margin-right:auto;" src="data:image/jpeg;base64,{0}">\n'.format(
            str(encoded_img_data).lstrip('b\'').rstrip('\''))

        ret += f'<hr>'


        # while not _success:
        #     try:

        # if jukeoroni.inserted_media is None:
        #     return HttpResponseRedirect('/jukeoroni')
        if jukeoroni.inserted_media is not None:
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
                    # _success = True
            # except AttributeError as err:
            #     print(err)
            #     time.sleep(1.0)

        ret += f'<hr>'
        ret += '<div>Currently loading: {0}</div>'.format(False if jukeoroni.jukebox.loading_track is None else jukeoroni.jukebox.loading_track)
        ret += f'<hr>'
        ret += '<div>Tracks in queue:</div>'

        ret += f'<ol>'
        ret += f'<table>'
        for track in jukeoroni.jukebox.tracks:
            ret += f'<tr>'
            ret += f'<td>'
            ret += '<li>&nbsp;</li>'
            ret += f'</td>'
            ret += '<td>{0}</td>'.format(track)
            ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/jukebox/{0}/as_first\';\">Set 1st</button></td>'.format(str(jukeoroni.jukebox.tracks.index(track)))
            ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/jukebox/{0}/pop\';\">Remove from Queue</button></td>'.format(str(jukeoroni.jukebox.tracks.index(track)))
            ret += f'</tr>'
        ret += f'</table>'
        ret += f'</ol>'
        ret += f'<hr>'
        # if not jukeoroni.jukebox.tracks and bool(jukeoroni.jukebox.loading_process):
        #     ret += '<div><img src=\"file://{0}\" alt=\"Loading {1}...\"></div>'.format(_JUKEBOX_LOADING_IMAGE, str(jukeoroni.jukebox.loading_process._kwargs['track']))
        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/switch_mode\';\">Mode: {0}</button>\n'.format(str(jukeoroni.jukebox.loader_mode))
        # if bool(jukeoroni.jukebox.tracks):

        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/play_next\';\">{0}</button>\n'.format(jukeoroni.mode['buttons']['0X00'])
        # else:
        #     ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/play_next\';\" disabled>{0}</button>\n'.format(jukeoroni.mode['buttons']['0X00'])
        if jukeoroni.mode == MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]:
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/stop\';\">Stop</button>\n'
        else:
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/stop\';\" disabled>Stop</button>\n'
        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/albums\';\">Albums</button>\n'
        ret += '  </body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def pop_track_from_queue(self, queue_index):
        global jukeoroni

        jukeoroni.jukebox.tracks.pop(queue_index)

        return HttpResponseRedirect('/jukeoroni')

    def set_first_in_queue(self, queue_index):

        global jukeoroni

        jukeoroni.jukebox.tracks.insert(0, jukeoroni.jukebox.tracks.pop(queue_index))

        return HttpResponseRedirect('/jukeoroni')

    def switch_mode(self):
        global jukeoroni

        if jukeoroni.mode == MODES['jukebox']['standby']['random']:
            jukeoroni.mode = MODES['jukebox']['standby']['album']
        elif jukeoroni.mode == MODES['jukebox']['on_air']['random']:
            jukeoroni.mode = MODES['jukebox']['on_air']['album']
        elif jukeoroni.mode == MODES['jukebox']['standby']['album']:
            jukeoroni.mode = MODES['jukebox']['standby']['random']
        elif jukeoroni.mode == MODES['jukebox']['on_air']['album']:
            jukeoroni.mode = MODES['jukebox']['on_air']['random']
            # return HttpResponseRedirect('/jukeoroni')
            # while
        # elif jukeoroni.jukebox.loader_mode == 'random':
        #     jukeoroni.mode = MODES['jukebox']['standby']['random']
        # elif jukeoroni.jukebox.loader_mode == 'album':
        #     jukeoroni.jukebox.set_loader_mode_random()

        return HttpResponseRedirect('/jukeoroni')

    def play_next(self):
        global jukeoroni

        # if not bool(jukeoroni.jukebox.tracks)

        # jukeoroni.set_mode_jukebox()
        if jukeoroni.mode != MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]:
            # if not bool(jukeoroni.jukebox.tracks):
            #     return HttpResponseRedirect('/jukeoroni')
            jukeoroni.mode = MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]
        else:
            # if jukeoroni.inserted_media is not None:
                # jukeoroni._next = channel
            jukeoroni._flag_next = True
        # jukeoroni.play()

        # player.button_3_value = BUTTON_3['Play']
        # # while player._playback_thread is None:
        # #     time.sleep(1.0)
        # # time.sleep(1.0)
        return HttpResponseRedirect('/jukeoroni')

    def stop(self):
        global jukeoroni

        jukeoroni.mode = MODES['jukebox']['standby'][jukeoroni.jukebox.loader_mode]
        return HttpResponseRedirect('/jukeoroni')
    #
    # def albums(self):
    #     global jukeoroni
    #     albums = Album.objects.all()
    #
    #     ret = '<html>\n'
    #     # ret += '  <head>\n'
    #     # ret += '    <meta http-equiv="refresh" content="10" >\n'
    #     # ret += '  </head>\n'
    #     ret += '  <body>\n'
    #     previous_artist = None
    #     for album in albums:
    #         ret += '  <div>\n'
    #         if album.artist != previous_artist:
    #             ret += f'{album.artist}'
    #         previous_artist = album.artist
    #         # ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/player/stop\';\">Stop</button>\n'
    #         # ret += f'    <button style=\"width:100%\">{album.album_title}</button>\n'
    #         ret += f'        <button style=\"width:100%\" onclick=\"window.location.href = \'{album.id}\';\">{album.album_title}</button>\n'
    #         ret += '  </div>\n'
    #     ret += '  </body>\n'
    #     ret += '</html>\n'
    #     return HttpResponse(ret)
    #
    # def play_album(self, album_id):
    #     global jukeoroni
    #
    #     jukeoroni.jukebox.play_album(album_id=album_id)
    #     # jukeoroni.set_mode_jukebox()
    #
    #     # jukeoroni.jukebox.kill_loading_process()
    #
    #     # # jukeoroni.jukebox.kill_loading_process()
    #     # # if not jukeoroni.jukebox.loader_mode == 'album':
    #     # # print(jukeoroni.jukebox.loading_process.pid)
    #     # # print(jukeoroni.jukebox.loading_process.pid)
    #     # # print(jukeoroni.jukebox.loading_process.pid)
    #     # # print(jukeoroni.jukebox.loading_process.pid)
    #     # # import pdb;pdb.set_trace()
    #     # # signal.pthread_kill(jukeoroni.jukebox.loading_process.pid, signal.SIGINT.value)
    #     # # if jukeoroni.jukebox.loader_mode != 'album':
    #     # #     jukeoroni.jukebox.set_loader_mode_album()
    #     # # jukeoroni.jukebox._need_first_album_track = False
    #     # jukeoroni.jukebox.requested_album_id = album_id
    #     # jukeoroni.jukebox.set_loader_mode_album()
    #     # # jukeoroni.insert(jukeoroni.jukebox.next_track)
    #     # # self.jukeoroni.mode = MODES['jukebox']['on_air'][self.jukeoroni.jukebox.loader_mode]
    #     # jukeoroni.set_mode_jukebox()
    #     # # self.switch_mode()
    #     jukeoroni.play()
    #     jukeoroni.set_mode_jukebox()
    #     # self.jukeoroni.button_1_value = 'Albm -> Rand'
    #
    #     # self.jukeoroni.set_image(track=self.jukeoroni.playing_track)
    #
    #     return HttpResponseRedirect('/jukeoroni')

    def radio_index(self):
        global jukeoroni

        if jukeoroni.mode != MODES['radio']['standby'] \
                and jukeoroni.mode != MODES['radio']['on_air']:

            return HttpResponseRedirect('/jukeoroni')

        stations = Station.objects.all().order_by('display_name')

        ret = '<html>\n'
        ret += '<head>\n'
        ret += '<meta http-equiv="refresh" content="10" >\n'
        ret += '</head>\n'
        ret += '<body>\n'
        ret += f'<button style=\"width:100%; \" onclick=\"window.location.href = \'/jukeoroni/set_standby\';\">Back to Standby</button>\n'
        ret += '<hr>\n'

        data = io.BytesIO()
        img = jukeoroni.layout_radio.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.radio.cover, title=jukeoroni.radio.stream_title)
        img = img.rotate(270, expand=True)
        img.save(data, "PNG")
        encoded_img_data = base64.b64encode(data.getvalue())

        # print(encoded_img_data)
        # print(encoded_img_data)
        # print(encoded_img_data)
        # print(encoded_img_data)

        ret += '<img id="picture" style="display:block;margin-left:auto;margin-right:auto;" src="data:image/jpeg;base64,{0}">\n'.format(
            str(encoded_img_data).lstrip('b\'').rstrip('\''))
        ret += '<hr>\n'
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

        # try:
        #     for c in Channel.objects.filter(last_played=True):
        #         c.last_played = False
        #         c.save()
        # except Channel.DoesNotExist:
        #     pass

        channel = Channel.objects.get(display_name_short=display_name_short)

        # if jukeoroni.mode != MODES['radio']['standby']:
        # jukeoroni.mode = MODES['radio']['standby']

        # while jukeoroni.radio.is_on_air is not None and jukeoroni.inserted_media is not None:  # or time_out <= 0.0:
        #     time.sleep(0.1)
        # if jukeoroni.inserted_media is not None:
        #     if jukeoroni.radio.is_on_air:
        #         jukeoroni.stop()
        #     jukeoroni.eject()
        if jukeoroni.inserted_media is not None:
            jukeoroni._next = channel
            jukeoroni._flag_next = True
        else:
            jukeoroni._next = channel
            # jukeoroni.insert(media=channel)

        # channel.last_played = True
        # channel.save()

        jukeoroni.mode = MODES['radio']['on_air']

        # time_out = 10.0
        while not jukeoroni.radio.is_on_air == channel:  # or time_out <= 0.0:
            time.sleep(0.1)
            # time_out -= 0.1
        # try:
        # jukeoroni.play()
        # except Exception:

        # jukeoroni.set_display_radio()

        return HttpResponseRedirect('/jukeoroni')

    def radio_stop(self):
        global jukeoroni

        jukeoroni.mode = MODES['radio']['standby']
        # jukeoroni.eject()

        # jukeoroni.mode = MODES['radio']['standby']

        # time_out = 10.0
        while jukeoroni.radio.is_on_air is not None:  # or time_out <= 0.0:
            time.sleep(0.1)
            # time_out -= 0.1

        return HttpResponseRedirect('/jukeoroni')
