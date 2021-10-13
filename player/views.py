import base64
import time
import io
from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from player.jukeoroni.jukeoroni import JukeOroni
from player.models import Album, Channel, Station, Artist
from player.jukeoroni.settings import (
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
jukeoroni.jukebox.set_auto_update_tracklist_on()


# Create your views here.
# TODO: rmove player for unittesting new juke
class JukeOroniView(View):

    def get(self, request):
        global jukeoroni

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

            bg_color = jukeoroni.layout_standby.bg_color

            if len(bg_color) == 3:
                bg_color = '%02x%02x%02x' % bg_color
            elif len(bg_color) == 4:
                bg_color = '%02x%02x%02x%02x' % bg_color

            ret = '<html>\n'
            ret += '  <head>\n'
            ret += '    <meta http-equiv="refresh" content="10" >\n'
            ret += '  </head>\n'
            ret += '  <body style="background-color:#{0};">\n'.format(bg_color)
            ret += '<center><h1>Hello JukeOroni</h1></center>\n'
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_jukebox\';\">Activate Jukebox</button>\n'
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_radio\';\">Activate Radio</button>\n'

            data = io.BytesIO()
            img = jukeoroni.layout_standby.get_layout(labels=jukeoroni.LABELS)
            img = img.rotate(270, expand=True)
            img.save(data, "PNG")
            encoded_img_data = base64.b64encode(data.getvalue())

            ret += '<img id="picture" style="display:block;margin-left:auto;margin-right:auto;" src="data:image/jpeg;base64,{0}">\n'.format(str(encoded_img_data).lstrip('b\'').rstrip('\''))
            ret += '</body>\n'
            ret += '</html>\n'

            return HttpResponse(ret)

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

            return HttpResponseRedirect('/jukeoroni')

        bg_color = jukeoroni.jukebox.layout.bg_color

        if len(bg_color) == 3:
            bg_color = '%02x%02x%02x' % bg_color
        elif len(bg_color) == 4:
            bg_color = '%02x%02x%02x%02x' % bg_color

        ret = '<html>\n'
        ret += '  <head>\n'
        ret += '    <meta http-equiv="refresh" content="10" >\n'
        ret += '  </head>\n'
        ret += '  <body style="background-color:#{0};">\n'.format(bg_color)
        ret += f'<button style=\"width:100%; \" onclick=\"window.location.href = \'/jukeoroni/set_standby\';\">Back</button>\n'
        ret += '<hr>\n'

        _success = False

        data = io.BytesIO()
        if jukeoroni.mode == MODES['jukebox']['standby']['album'] \
                or jukeoroni.mode == MODES['jukebox']['standby']['random']:
            img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS)
        elif jukeoroni.mode == MODES['jukebox']['on_air']['album'] \
                or jukeoroni.mode == MODES['jukebox']['on_air']['random']:
            try:
                img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.inserted_media.cover_album,
                                                    artist=jukeoroni.inserted_media.cover_artist)
            except AttributeError:
                img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS, loading=True)
                # LOG.exception('inserted_media problem: ')
        img = img.rotate(270, expand=True)
        img.save(data, "PNG")
        encoded_img_data = base64.b64encode(data.getvalue())

        ret += '<img id="picture" style="display:block;margin-left:auto;margin-right:auto;" src="data:image/jpeg;base64,{0}">\n'.format(
            str(encoded_img_data).lstrip('b\'').rstrip('\''))

        ret += f'<hr>'

        if jukeoroni.inserted_media is not None:
            ret += f'<div style="text-align: center;">{str(jukeoroni.inserted_media.artist)}</div>'
            ret += f'<div style="text-align: center;">{str(jukeoroni.inserted_media.album)}</div>'
            ret += f'<div style="text-align: center;">{str(jukeoroni.inserted_media.track_title)}</div>'

        ret += f'<hr>'
        ret += '<center><div>Loading</div></center>'
        ret += '<center><div>{0}</div></center>'.format(False if jukeoroni.jukebox.loading_track is None else jukeoroni.jukebox.loading_track)
        ret += f'<hr>'
        ret += '<center><div>Queue</div></center>'

        ret += f'<ol>'
        ret += f'<center><table border="0">'
        for track in jukeoroni.jukebox.tracks:
            ret += f'<tr>'
            ret += f'<td>'
            ret += '<li>&nbsp;</li>'
            ret += f'</td>'
            ret += '<td>{0}</td>'.format(track)
            if jukeoroni.jukebox.tracks.index(track) == 0:
                ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/jukebox/{0}/as_first\';\" disabled>Set 1st</button></td>'.format(str(jukeoroni.jukebox.tracks.index(track)))
            else:
                ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/jukebox/{0}/as_first\';\">Set 1st</button></td>'.format(str(jukeoroni.jukebox.tracks.index(track)))
            ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/jukebox/{0}/pop\';\">Remove from Queue</button></td>'.format(str(jukeoroni.jukebox.tracks.index(track)))
            ret += f'</tr>'
        ret += f'</table></center>'
        ret += f'</ol>'
        ret += f'<hr>'
        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/switch_mode\';\">Mode: {0}</button>\n'.format(str(jukeoroni.jukebox.loader_mode))
        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/play_next\';\">{0}</button>\n'.format(jukeoroni.mode['buttons']['0X00'])
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

        return HttpResponseRedirect('/jukeoroni')

    def play_next(self):
        global jukeoroni

        if jukeoroni.mode != MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]:
            jukeoroni.mode = MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]
        else:
            jukeoroni._flag_next = True

        return HttpResponseRedirect('/jukeoroni')

    def stop(self):
        global jukeoroni

        jukeoroni.mode = MODES['jukebox']['standby'][jukeoroni.jukebox.loader_mode]
        return HttpResponseRedirect('/jukeoroni')

    def albums(self):
        global jukeoroni

        if not jukeoroni.mode == MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['album']:

            return HttpResponseRedirect('/jukeoroni')

        artists = Artist.objects.all().order_by('name')

        bg_color = jukeoroni.jukebox.layout.bg_color

        if len(bg_color) == 3:
            bg_color = '%02x%02x%02x' % bg_color
        elif len(bg_color) == 4:
            bg_color = '%02x%02x%02x%02x' % bg_color

        ret = '<html>\n'
        ret += '  <body style="background-color:#{0};">\n'.format(bg_color)
        ret += '        <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni\';\">Back</button>\n'

        for artist in artists:
            albums = Album.objects.filter(artist=artist).order_by('year', 'album_title')
            ret += f'<hr>'
            ret += f'<center><h1>{artist.name}</h1></center>'
            year = None
            for album in albums:
                if year != album.year:
                    ret += f'<h4><center>{album.year}</center></h4>'
                    year = album.year
                ret += '  <div>\n'
                ret += f'        <button style=\"width:100%\" onclick=\"window.location.href = \'{album.id}\';\">{album.album_title}</button>\n'
                ret += '  </div>\n'
        ret += '  </body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def play_album(self, album_id):
        global jukeoroni

        jukeoroni.mode = MODES['jukebox']['on_air']['album']
        if jukeoroni.jukebox.loader_mode != 'album':
            jukeoroni.jukebox.set_loader_mode_album()
        jukeoroni.jukebox.play_album(album_id=album_id)

        return HttpResponseRedirect('/jukeoroni')

    def radio_index(self):
        global jukeoroni

        if jukeoroni.mode != MODES['radio']['standby'] \
                and jukeoroni.mode != MODES['radio']['on_air']:

            return HttpResponseRedirect('/jukeoroni')

        stations = Station.objects.all().order_by('display_name')

        bg_color = jukeoroni.layout_radio.bg_color

        if len(bg_color) == 3:
            bg_color = '%02x%02x%02x' % bg_color
        elif len(bg_color) == 4:
            bg_color = '%02x%02x%02x%02x' % bg_color

        ret = '<html>\n'
        ret += '<head>\n'
        ret += '<meta http-equiv="refresh" content="10" >\n'
        ret += '</head>\n'
        ret += '<body style="background-color:#{0};">\n'.format(bg_color)
        ret += f'<button style=\"width:100%; \" onclick=\"window.location.href = \'/jukeoroni/set_standby\';\">Back to Standby</button>\n'
        ret += '<hr>\n'

        data = io.BytesIO()
        img = jukeoroni.layout_radio.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.radio.cover, title=jukeoroni.radio.stream_title)
        img = img.rotate(270, expand=True)
        img.save(data, "PNG")
        encoded_img_data = base64.b64encode(data.getvalue())

        ret += '<img id="picture" style="display:block;margin-left:auto;margin-right:auto;" src="data:image/jpeg;base64,{0}">\n'.format(
            str(encoded_img_data).lstrip('b\'').rstrip('\''))
        ret += '<hr>\n'
        for station in stations:
            channels = Channel.objects.filter(station=station).order_by('display_name')
            if channels:
                ret += f'<center><h1>{station.display_name}</h1></center>\n'
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

        channel = Channel.objects.get(display_name_short=display_name_short)

        if jukeoroni.inserted_media is not None:
            jukeoroni._next = channel
            jukeoroni._flag_next = True
        else:
            jukeoroni._next = channel

        jukeoroni.mode = MODES['radio']['on_air']

        # time_out = 10.0
        while not jukeoroni.radio.is_on_air == channel:  # or time_out <= 0.0:
            time.sleep(0.1)
            # time_out -= 0.1

        return HttpResponseRedirect('/jukeoroni')

    def radio_stop(self):
        global jukeoroni

        jukeoroni.mode = MODES['radio']['standby']

        # time_out = 10.0
        while jukeoroni.radio.is_on_air is not None:  # or time_out <= 0.0:
            time.sleep(0.1)
            # time_out -= 0.1

        return HttpResponseRedirect('/jukeoroni')
