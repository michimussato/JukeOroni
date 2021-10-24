import base64
import time
import io
from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from player.jukeoroni.jukeoroni import JukeOroni
from player.models import Album, Channel, Station, Artist, Track
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
# jukeoroni.jukebox.set_auto_update_tracklist_on()


def get_bg_color(rgb):
    _hex = None
    if len(rgb) == 3:
        _hex = '%02x%02x%02x' % rgb
    elif len(rgb) == 4:
        _hex = '%02x%02x%02x%02x' % rgb
    return _hex


def encoded_screen(img):
    data = io.BytesIO()
    # img = jukeoroni.layout_radio.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.radio.cover,
    #                                         title=jukeoroni.radio.stream_title)
    img = img.rotate(270, expand=True)
    img.save(data, "PNG")
    encoded_img_data = base64.b64encode(data.getvalue())
    return encoded_img_data


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

            bg_color = get_bg_color(jukeoroni.layout_standby.bg_color)

            ret = '<html>\n'
            ret += '  <head>\n'
            ret += '    <meta http-equiv="refresh" content="10" >\n'
            ret += '  </head>\n'
            ret += '  <body style="background-color:#{0};">\n'.format(bg_color)
            ret += '<center><h1>Hello JukeOroni</h1></center>\n'
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_jukebox\';\">Jukebox</button>\n'
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_radio\';\">Radio</button>\n'
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/transmission\';\">Transmission</button>\n'

            img = jukeoroni.layout_standby.get_layout(labels=jukeoroni.LABELS)
            encoded_img_data = encoded_screen(img)

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

        bg_color = get_bg_color(jukeoroni.jukebox.layout.bg_color)

        ret = '<html>\n'
        ret += '  <head>\n'
        ret += '    <meta http-equiv="refresh" content="10" >\n'
        ret += '  </head>\n'
        ret += '  <body style="background-color:#{0};">\n'.format(bg_color)
        ret += f'<button style=\"width:100%; \" onclick=\"window.location.href = \'/jukeoroni/set_standby\';\">Quit Jukebox</button>\n'
        ret += '<hr>\n'

        _success = False

        img = None
        # data = io.BytesIO()
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
        # img = img.rotate(270, expand=True)
        # img.save(data, "PNG")
        if img is not None:
            encoded_img_data = encoded_screen(img)

            ret += '<img id="picture" style="display:block;margin-left:auto;margin-right:auto;" src="data:image/jpeg;base64,{0}">\n'.format(
                str(encoded_img_data).lstrip('b\'').rstrip('\''))

        ret += f'<hr>'

        ret += '<center><div>Inserted/Playing</div></center>'
        if jukeoroni.inserted_media is not None:
            ret += f'<div style="text-align: center;">{str(jukeoroni.inserted_media.artist)}</div>'
            ret += f'<div style="text-align: center;">{str(jukeoroni.inserted_media.album)}</div>'
            ret += f'<div style="text-align: center;">{str(jukeoroni.inserted_media.track_title)}</div>'
        else:
            ret += '<div style="text-align: center;">None</div>'

        if jukeoroni.jukebox.loading_track is not None:
            ret += f'<hr>'
            ret += '<center><div>Loading</div></center>'
            ret += '<center><div>{0}</div></center>'.format(f'{jukeoroni.jukebox.loading_track.artist} - {jukeoroni.jukebox.loading_track.album} ({jukeoroni.jukebox.loading_track.year}) - {jukeoroni.jukebox.loading_track.track_title} ({str(round(jukeoroni.jukebox.loading_track.size_cached / (1024.0 * 1024.0), 1))} of {str(round(jukeoroni.jukebox.loading_track.size / (1024.0 * 1024.0), 1))} MB)')
        ret += f'<hr>'
        ret += '<center><div>Queue</div></center>'

        ret += f'<ol>'
        ret += f'<center><table border="0" cellspacing="0">'
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

        if jukeoroni.paused:
           ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/resume\';\">Resume</button>\n'
        else:
            if jukeoroni.mode == MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]:
                ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\">Pause</button>\n'
            else:
                ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\" disabled>Pause</button>\n'
        if jukeoroni.mode == MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]:
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/stop\';\">Stop</button>\n'
        else:
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/stop\';\" disabled>Stop</button>\n'


        # ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/albums\';\">Albums</button>\n'

        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/albums\';\">Albums</button>\n'
        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/jukebox/tracks\';\">Tracks</button>\n'
        ret += '  </body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def pause(self):
        global jukeoroni

        jukeoroni.pause()

        return HttpResponseRedirect('/jukeoroni')

    def resume(self):
        global jukeoroni

        jukeoroni.resume()

        return HttpResponseRedirect('/jukeoroni')

    # def play_track(self, track_id):
    #     global jukeoroni
    #
    #     if not jukeoroni.mode == MODES['jukebox']['standby']['random'] \
    #             and not jukeoroni.mode == MODES['jukebox']['standby']['album'] \
    #             and not jukeoroni.mode == MODES['jukebox']['on_air']['random'] \
    #             and not jukeoroni.mode == MODES['jukebox']['on_air']['album']:
    #
    #         return HttpResponseRedirect('/jukeoroni')
    #
    #     # jukeoroni.mode = MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]
    #
    #     # if jukeoroni.jukebox.loader_mode != 'album':
    #     #     jukeoroni.jukebox.set_loader_mode_album()
    #     jukeoroni.jukebox.play_track_by_id = track_id
    #
    #     # jukeoroni._flag_next = True
    #
    #     return HttpResponseRedirect('/jukeoroni')

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

        if not jukeoroni.mode == MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]:
            jukeoroni.mode = MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]
        else:
            jukeoroni._flag_next = True

        return HttpResponseRedirect('/jukeoroni')

    def stop(self):
        global jukeoroni

        jukeoroni.mode = MODES['jukebox']['standby'][jukeoroni.jukebox.loader_mode]
        return HttpResponseRedirect('/jukeoroni')

    def tracks(self):
        global jukeoroni

        if not jukeoroni.mode == MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['album']:

            return HttpResponseRedirect('/jukeoroni')

        tracks = Track.objects.all().order_by('album')

        bg_color = get_bg_color(jukeoroni.jukebox.layout.bg_color)

        ret = '<html>\n'
        ret += '  <body style="background-color:#{0};">\n'.format(bg_color)
        ret += '        <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni\';\">Back</button>\n'
        ret += f'<hr>'
        # ret += f'<table>'
        ret += f'<div>{len(tracks)} tracks</div>'
        ret += f'<hr>'

        ret += f'<table border="0" cellspacing="0">'
        ret += f'<tr>'
        ret += f'<td>ID</td>'
        ret += f'<td><button>Play</button></td>'
        ret += f'<td>Track</td>'
        ret += f'<td>Album</td>'
        ret += f'<td>Artist</td>'
        ret += f'<td>Year</td>'
        ret += f'<td>Times played</td>'
        ret += f'<td>Path</td>'
        ret += f'<td></td>'
        ret += f'</tr>'
        # i = 0
        for track in tracks:
            # if i >= 20:
            #     break
            ret += f'<tr>'
            ret += f'<td>{track.id}</td>'
            # ret += f'<td>{track.id}</td>'
            ret += f'<td><button onclick=\"window.location.href = \'play_track/{track.id}\';\" disabled>Play</button></td>'
            ret += f'<td>{track.track_title}</td>'
            ret += f'<td>{track.album}</td>'
            ret += f'<td>{track.album.artist}</td>'
            ret += f'<td>{track.album.year}</td>'
            ret += f'<td>{track.played}</td>'
            ret += f'<td>{track}</td>'
            ret += f'</tr>'

        ret += f'</table>'
        ret += '  </body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def albums(self):
        global jukeoroni

        if not jukeoroni.mode == MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['album']:

            return HttpResponseRedirect('/jukeoroni')

        artists = Artist.objects.all().order_by('name')

        bg_color = get_bg_color(jukeoroni.jukebox.layout.bg_color)

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
                    ret += f'<div><center>{album.year}</center></div>'
                    year = album.year
                ret += '  <div>\n'
                ret += f'        <button style=\"width:100%\" onclick=\"window.location.href = \'{album.id}\';\">{album.album_title}</button>\n'
                ret += '  </div>\n'
        ret += '  </body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def play_album(self, album_id):
        global jukeoroni

        if not jukeoroni.mode == MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == MODES['jukebox']['on_air']['album']:

            return HttpResponseRedirect('/jukeoroni')

        jukeoroni.mode = MODES['jukebox']['on_air']['album']
        if jukeoroni.jukebox.loader_mode != 'album':
            jukeoroni.jukebox.set_loader_mode_album()
        jukeoroni.jukebox.play_album(album_id=album_id)

        return HttpResponseRedirect('/jukeoroni')

    def radio_index(self):
        global jukeoroni

        if not jukeoroni.mode == MODES['radio']['standby'] \
                and not jukeoroni.mode == MODES['radio']['on_air']:

            return HttpResponseRedirect('/jukeoroni')

        stations = Station.objects.all().order_by('display_name')

        bg_color = get_bg_color(jukeoroni.layout_radio.bg_color)

        ret = '<html>\n'
        ret += '<head>\n'
        ret += '<meta http-equiv="refresh" content="10" >\n'
        ret += '</head>\n'
        ret += '<body style="background-color:#{0};">\n'.format(bg_color)
        ret += f'<button style=\"width:100%; \" onclick=\"window.location.href = \'/jukeoroni/set_standby\';\">Quit Radio</button>\n'
        ret += '<hr>\n'
        last_played = jukeoroni.radio.last_played
        # ret += f'{last_played}'
        # ret += f'{str(type(last_played))}'
        # ret += f'{last_played}'
        if last_played is None or jukeoroni.radio.is_on_air:
            ret += f'<button style=\"width:100%\" disabled>Last played</button>\n'
        else:
            ret += f'<button style=\"width:100%\" onclick=\"window.location.href = \'{last_played.display_name_short}/play\';\">Last played ({last_played.display_name})</button>\n'
        ret += f'<button style=\"width:100%\" onclick=\"window.location.href = \'random/play\';\">Random</button>\n'
        if jukeoroni.paused:
           ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/resume\';\">Resume</button>\n'
        else:
            if jukeoroni.mode == MODES['radio']['on_air']:
                ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\">Pause</button>\n'
            else:
                ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\" disabled>Pause</button>\n'
        ret += '<hr>\n'

        # data = io.BytesIO()
        # try:
        img = jukeoroni.layout_radio.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.radio.cover, title=jukeoroni.radio.stream_title)
        encoded_img_data = encoded_screen(img)
        # except:
        #     img = None
        # img = img.rotate(270, expand=True)
        # img.save(data, "PNG")

        # if img is not None:
        ret += '<img id="picture" style="display:block;margin-left:auto;margin-right:auto;" src="data:image/jpeg;base64,{0}">\n'.format(
            str(encoded_img_data).lstrip('b\'').rstrip('\''))
        ret += '<hr>\n'
        ret += '<center><h1>Channels</h1></center>\n'
        for station in stations:
            channels = Channel.objects.filter(station=station).order_by('display_name')
            if channels:
                ret += f'<center><h2>{station.display_name}</h2></center>\n'
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

        if not jukeoroni.mode == MODES['radio']['standby'] \
                and not jukeoroni.mode == MODES['radio']['on_air']:

            return HttpResponseRedirect('/jukeoroni')

        if display_name_short == 'random':
            channel = jukeoroni.radio.random_channel
        else:
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

        if not jukeoroni.mode == MODES['radio']['standby'] \
                and not jukeoroni.mode == MODES['radio']['on_air']:

            return HttpResponseRedirect('/jukeoroni')

        jukeoroni.mode = MODES['radio']['standby']

        # time_out = 10.0
        while jukeoroni.radio.is_on_air is not None:  # or time_out <= 0.0:
            time.sleep(0.1)
            # time_out -= 0.1

        return HttpResponseRedirect('/jukeoroni')
