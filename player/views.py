import base64
import random
import time
import io
from django.db.models.functions import Lower
from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from player.jukeoroni.jukeoroni import JukeOroni
from player.models import Album, Channel, Station, Artist, Track
from player.jukeoroni.settings import Settings


PIMORONI_SATURATION = 1.0
FONT_SIZE = 24
SLEEP_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
STANDARD_COVER = '/data/django/jukeoroni/player/static/cover_std.png'
PIMORONI_FONT = '/data/django/jukeoroni/player/static/gotham-black.ttf'


jukeoroni = JukeOroni(test=False)
jukeoroni.turn_on(disable_track_loader=False)
# jukeoroni.jukebox.set_auto_update_tracklist_on()
# jukeoroni.meditationbox.set_auto_update_tracklist_on()
# jukeoroni.episodicbox.set_auto_update_tracklist_on()
# jukeoroni.jukebox.track_list_generator_thread()


# def index_redirect(request):
#     return redirect('/jukeoroni')


def get_bg_color(rgb):
    # _hex = None
    # if len(rgb) == 3:
    #     _hex = '%02x%02x%02x' % rgb
    # elif len(rgb) == 4:
    #     _hex = '%02x%02x%02x%02x' % rgb
    # # return _hex
    return '606060'  # TODO: constant until solution to avoid black text on black bg


def encoded_screen(img):
    data = io.BytesIO()
    # img = jukeoroni.layout_radio.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.radio.cover,
    #                                         title=jukeoroni.radio.stream_title)
    img = img.rotate(270, expand=True)
    img.save(data, "PNG")
    encoded_img_data = base64.b64encode(data.getvalue())
    return encoded_img_data


def get_active_box(_jukeoroni):
    if _jukeoroni.mode == Settings.MODES['jukebox']['standby']['random'] \
            or _jukeoroni.mode == Settings.MODES['jukebox']['standby']['album'] \
            or _jukeoroni.mode == Settings.MODES['jukebox']['on_air']['random'] \
            or _jukeoroni.mode == Settings.MODES['jukebox']['on_air']['album']:
        box = _jukeoroni.jukebox
    elif _jukeoroni.mode == Settings.MODES['meditationbox']['standby']['random'] \
            or _jukeoroni.mode == Settings.MODES['meditationbox']['standby']['album'] \
            or _jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['random'] \
            or _jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['album']:
        box = _jukeoroni.meditationbox
    elif _jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['random'] \
            or _jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['album'] \
            or _jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['random'] \
            or _jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['album']:
        box = _jukeoroni.audiobookbox
    else:
        # LOG.error(_jukeoroni.mode)
        raise NotImplementedError('No Box!!!')
    return box


# Create your views here.
# TODO: rmove player for unittesting new juke
class JukeOroniView(View):

    def get(self, request):
        global jukeoroni

        if jukeoroni.mode == Settings.MODES['radio']['standby'] \
                or jukeoroni.mode == Settings.MODES['radio']['on_air']:

            return HttpResponseRedirect('radio/')

        elif jukeoroni.mode == Settings.MODES['jukebox']['standby']['album'] \
                or jukeoroni.mode == Settings.MODES['jukebox']['standby']['random'] \
                or jukeoroni.mode == Settings.MODES['jukebox']['on_air']['album'] \
                or jukeoroni.mode == Settings.MODES['jukebox']['on_air']['random']:

            return HttpResponseRedirect('jukebox/')

        elif jukeoroni.mode == Settings.MODES['meditationbox']['standby']['album'] \
                or jukeoroni.mode == Settings.MODES['meditationbox']['standby']['random'] \
                or jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['album'] \
                or jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['random']:

            return HttpResponseRedirect('meditationbox/')

        elif jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['album'] \
            or jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['random'] \
            or jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['album'] \
            or jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['random']:

            return HttpResponseRedirect('audiobookbox/')

        elif jukeoroni.mode == Settings.MODES['jukeoroni']['standby'] \
                or jukeoroni.mode == Settings.MODES['jukeoroni']['off']:

            bg_color = get_bg_color(jukeoroni.layout_standby.bg_color)

            ret = '<html>\n'
            ret += '<head>\n'
            ret += '<meta http-equiv="refresh" content="10" >\n'
            ret += '<link rel="icon" type="image/x-icon" href="/jukeoroni/favicon.ico">\n'
            ret += '</head>\n'
            ret += '<body style="background-color:#{0};">\n'.format(bg_color)
            ret += '<center>'
            ret += '<table border="0" cellspacing="0" style="text-align:center;margin-left:auto;margin-right:auto;border-collapse: collapse;">'
            ret += '<tr style="border: none;">'

            ret += '<td style="border-right: solid 1px #000;border-left: solid 1px #000;padding: 5px 10px;">'
            ret += '<a href="/admin" target="_blank">Admin</a>'
            ret += '</td>'

            ret += '<td style="border-right: solid 1px #000;border-left: solid 1px #000;padding: 5px 10px;">'  #  border-right: solid 1px #f00; border-left: solid 1px #f00;
            ret += '<a href="/transmission" target="_blank">Transmission</a>'
            ret += '</td>'

            ret += '<td style="border-right: solid 1px #000;border-left: solid 1px #000;padding: 5px 10px;">'
            ret += '<a href="/webmin" target="_blank">Webmin</a>'
            ret += '</td>'

            ret += '</tr>'
            ret += '</table>'
            ret += '</center>'

            ret += '<hr>\n'

            # ret += '<center><h1>Hello JukeOroni</h1></center>\n'
            if any([Settings.ENABLE_JUKEBOX, Settings.ENABLE_RADIO, Settings.ENABLE_MEDITATION, Settings.ENABLE_EPISODIC]):
                if Settings.ENABLE_JUKEBOX:
                    ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_jukebox\';\">JukeBox</button>\n'
                if Settings.ENABLE_RADIO:
                    ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_radio\';\">Radio</button>\n'
                if Settings.ENABLE_MEDITATION:
                    ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_meditationbox\';\">MeditationBox</button>\n'
                if Settings.ENABLE_EPISODIC:
                    ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/set_audiobookbox\';\">AudiobookBox</button>\n'

                ret += '<hr>\n'

            img = jukeoroni.layout_standby.get_layout(labels=jukeoroni.LABELS)
            encoded_img_data = encoded_screen(img)

            ret += '<img id="picture" style="display:block;margin-left:auto;margin-right:auto;" src="data:image/jpeg;base64,{0}">\n'.format(str(encoded_img_data).lstrip('b\'').rstrip('\''))
            ret += '</body>\n'
            ret += '</html>\n'

            return HttpResponse(ret)

    def set_jukebox(self):
        global jukeoroni

        jukeoroni.mode = Settings.MODES['jukebox']['standby'][jukeoroni.jukebox.loader_mode]

        return HttpResponseRedirect('/jukeoroni/jukebox')

    def set_meditationbox(self):
        global jukeoroni

        jukeoroni.mode = Settings.MODES['meditationbox']['standby'][jukeoroni.meditationbox.loader_mode]

        return HttpResponseRedirect('/jukeoroni/meditationbox')

    def set_audiobookbox(self):
        global jukeoroni

        jukeoroni.mode = Settings.MODES['audiobookbox']['standby'][jukeoroni.audiobookbox.loader_mode]

        return HttpResponseRedirect('/jukeoroni/audiobookbox')

    def set_radio(self):
        global jukeoroni

        jukeoroni.mode = Settings.MODES['radio']['standby']

        return HttpResponseRedirect('/jukeoroni/radio')

    def set_standby(self):
        global jukeoroni

        jukeoroni.mode = Settings.MODES['jukeoroni']['standby']

        return HttpResponseRedirect('/jukeoroni')

    def box_index(self):

        global jukeoroni

        if not jukeoroni.mode == Settings.MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['album']:

            return HttpResponseRedirect('/jukeoroni')

        box = get_active_box(jukeoroni)

        bg_color = get_bg_color(box.layout.bg_color)

        ret = '<html>\n'
        ret += '<head>\n'
        ret += '<meta http-equiv="refresh" content="10" >\n'
        ret += '<link rel="icon" type="image/x-icon" href="/jukeoroni/favicon.ico">\n'
        ret += '</head>\n'
        ret += '<body style="background-color:#{0};">\n'.format(bg_color)
        ret += f'<button style=\"width:100%; \" onclick=\"window.location.href = \'/jukeoroni/set_standby\';\">Back to Menu</button>\n'
        ret += '<hr>\n'

        _success = False

        img = None
        # data = io.BytesIO()
        if jukeoroni.mode == Settings.MODES[box.box_type]['standby']['album'] \
                or jukeoroni.mode == Settings.MODES[box.box_type]['standby']['random']:
            img = box.layout.get_layout(labels=jukeoroni.LABELS)
        elif jukeoroni.mode == Settings.MODES[box.box_type]['on_air']['album'] \
                or jukeoroni.mode == Settings.MODES[box.box_type]['on_air']['random']:
            try:
                img = box.layout.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.inserted_media.cover_album,
                                                    artist=jukeoroni.inserted_media.cover_artist)
            except AttributeError:
                img = box.layout.get_layout(labels=jukeoroni.LABELS, loading=True)
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
            ret += f'<div style="text-align: center;">(ID: {str(jukeoroni.inserted_media.django_track.id)})</div>'
        else:
            ret += '<div style="text-align: center;">None</div>'

        if box.loading_track is not None:
            ret += '<hr>'
            ret += '<center><div>Loading</div></center>'
            ret += '<center><div>{0}</div></center>'.format(f'{box.loading_track.artist} - {box.loading_track.album} ({box.loading_track.year}) - {box.loading_track.track_title} ({str(round(box.loading_track.size_cached / (1024.0 * 1024.0), 1))} of {str(round(box.loading_track.size / (1024.0 * 1024.0), 1))} MB)')
        ret += '<hr>'
        ret += '<center><div>Queue</div></center>'

        ret += '<ol>'
        ret += '<center><table border="0" cellspacing="0">'
        for track in box.tracks:
            ret += '<tr>'
            ret += '<td>'
            ret += '<li>&nbsp;</li>'
            ret += '</td>'
            ret += '<td>{0} (ID: {1})</td>'.format(track, track.django_track.id)
            if box.tracks.index(track) == 0:
                ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/{1}/{0}/as_first\';\" disabled>Set 1st</button></td>'.format(str(box.tracks.index(track)), str(box.box_type))
            else:
                ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/{1}/{0}/as_first\';\">Set 1st</button></td>'.format(str(box.tracks.index(track)), str(box.box_type))
            ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/{1}/{0}/pop\';\">Remove from Queue</button></td>'.format(str(box.tracks.index(track)), str(box.box_type))
            ret += f'</tr>'
        ret += f'</table></center>'
        ret += f'</ol>'
        ret += f'<hr>'

        if box.track_list_updater_running:
            ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/update_track_list\';\"  disabled>Update Track List</button>\n'.format(str(box.box_type))
        else:
            ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/update_track_list\';\">Update Track List</button>\n'.format(str(box.box_type))

        ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{1}/switch_mode\';\">Mode: {0}</button>\n'.format(str(box.loader_mode).capitalize(), str(box.box_type))
        ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{1}/play_next\';\">{0}</button>\n'.format(jukeoroni.mode['buttons']['0X00'], str(box.box_type))

        if jukeoroni.paused:
            ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/resume\';\">Resume</button>\n'
        else:
            if jukeoroni.mode == Settings.MODES[box.box_type]['on_air'][box.loader_mode]:
                ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\">Pause</button>\n'
            else:
                ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\" disabled>Pause</button>\n'
        if jukeoroni.mode == Settings.MODES[box.box_type]['on_air'][box.loader_mode]:
            ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/stop\';\">Stop</button>\n'.format(str(box.box_type))
        else:
            ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/stop\';\" disabled>Stop</button>\n'.format(str(box.box_type))

        ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/albums\';\">Albums</button>\n'.format(str(box.box_type))
        # ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/tracks\';\">Tracks</button>\n'.format(str(box.box_type))
        ret += '</body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def update_track_list(self):
        global jukeoroni

        box = get_active_box(jukeoroni)

        box.run_tracklist_generator_flag = True

        return HttpResponseRedirect('/jukeoroni')

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

        box = get_active_box(jukeoroni)

        box.tracks.pop(queue_index)

        return HttpResponseRedirect('/jukeoroni')

    def set_first_in_queue(self, queue_index):

        global jukeoroni

        box = get_active_box(jukeoroni)

        box.tracks.insert(0, box.tracks.pop(queue_index))

        return HttpResponseRedirect('/jukeoroni')

    def switch_mode(self):
        global jukeoroni

        if jukeoroni.mode == Settings.MODES['jukebox']['standby']['random']:
            jukeoroni.mode = Settings.MODES['jukebox']['standby']['album']
        elif jukeoroni.mode == Settings.MODES['jukebox']['on_air']['random']:
            jukeoroni.mode = Settings.MODES['jukebox']['on_air']['album']
        elif jukeoroni.mode == Settings.MODES['jukebox']['standby']['album']:
            jukeoroni.mode = Settings.MODES['jukebox']['standby']['random']
        elif jukeoroni.mode == Settings.MODES['jukebox']['on_air']['album']:
            jukeoroni.mode = Settings.MODES['jukebox']['on_air']['random']

        elif jukeoroni.mode == Settings.MODES['meditationbox']['standby']['random']:
            jukeoroni.mode = Settings.MODES['meditationbox']['standby']['album']
        elif jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['random']:
            jukeoroni.mode = Settings.MODES['meditationbox']['on_air']['album']
        elif jukeoroni.mode == Settings.MODES['meditationbox']['standby']['album']:
            jukeoroni.mode = Settings.MODES['meditationbox']['standby']['random']
        elif jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['album']:
            jukeoroni.mode = Settings.MODES['meditationbox']['on_air']['random']

        # Audiobooks should never be random, always album/sequential
        elif jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['random']:
            pass
            # jukeoroni.mode = MODES['audiobookbox']['standby']['album']
        elif jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['random']:
            pass
            # jukeoroni.mode = MODES['audiobookbox']['on_air']['album']
        elif jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['album']:
            pass
            # jukeoroni.mode = MODES['audiobookbox']['standby']['random']
        elif jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['album']:
            pass
            # jukeoroni.mode = MODES['audiobookbox']['on_air']['random']

        return HttpResponseRedirect('/jukeoroni')

    def play_next(self):
        global jukeoroni

        box = get_active_box(jukeoroni)

        # TODO
        # if jukeoroni.mode == MODES['meditationbox']['standby'][jukeoroni.meditationbox.loader_mode] \
        #         or jukeoroni.mode == MODES['meditationbox']['on_air'][jukeoroni.meditationbox.loader_mode]:
        #     jukeoroni.meditationbox.tracks.insert(0, jukeoroni.jukebox.tracks.pop(queue_index))
        #
        # elif jukeoroni.mode == MODES['jukebox']['standby'][jukeoroni.jukebox.loader_mode] \
        #         or jukeoroni.mode == MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]:

        if not jukeoroni.mode == Settings.MODES[box.box_type]['on_air'][box.loader_mode]:
            jukeoroni.mode = Settings.MODES[box.box_type]['on_air'][box.loader_mode]
        else:
            jukeoroni._flag_next = True

        return HttpResponseRedirect('/jukeoroni')

    def stop(self):
        global jukeoroni

        box = get_active_box(jukeoroni)

        if jukeoroni.mode == Settings.MODES[box.box_type]['on_air'][box.loader_mode]:
            jukeoroni.mode = Settings.MODES[box.box_type]['standby'][box.loader_mode]
        # elif jukeoroni.mode == MODES['jukebox']['on_air'][jukeoroni.jukebox.loader_mode]:
        #     jukeoroni.mode = MODES['jukebox']['standby'][jukeoroni.jukebox.loader_mode]
        return HttpResponseRedirect('/jukeoroni')

    # def tracks(self):
    #     global jukeoroni
    #
    #     if not jukeoroni.mode == MODES['jukebox']['standby']['random'] \
    #             and not jukeoroni.mode == MODES['jukebox']['standby']['album'] \
    #             and not jukeoroni.mode == MODES['jukebox']['on_air']['random'] \
    #             and not jukeoroni.mode == MODES['jukebox']['on_air']['album']:
    #
    #         return HttpResponseRedirect('/jukeoroni')
    #
    #     tracks = Track.objects.all().order_by('album')
    #
    #     bg_color = get_bg_color(jukeoroni.jukebox.layout.bg_color)
    #
    #     ret = '<html>\n'
    #
    #     ret += '<head>\n'
    #     # ret += '    <meta http-equiv="refresh" content="10" >\n'
    #     ret += '<link rel="icon" type="image/x-icon" href="/jukeoroni/favicon.ico">\n'
    #     ret += '</head>\n'
    #
    #     ret += '<body style="background-color:#{0};">\n'.format(bg_color)
    #     ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni\';\">Back</button>\n'
    #     ret += f'<hr>'
    #     # ret += f'<table>'
    #     ret += f'<div>{len(tracks)} tracks</div>'
    #     ret += f'<hr>'
    #
    #     ret += f'<table border="0" cellspacing="0">'
    #     ret += f'<tr>'
    #     ret += f'<td>ID</td>'
    #     ret += f'<td>Play</td>'
    #     ret += f'<td>Track</td>'
    #     ret += f'<td>Album</td>'
    #     ret += f'<td>Artist</td>'
    #     ret += f'<td>Year</td>'
    #     ret += f'<td>Times played</td>'
    #     ret += f'<td>Path</td>'
    #     ret += f'<td></td>'
    #     ret += f'</tr>'
    #     # i = 0
    #     for track in tracks:
    #         # if i >= 20:
    #         #     break
    #         ret += f'<tr>'
    #         ret += f'<td>{track.id}</td>'
    #         # ret += f'<td>{track.id}</td>'
    #         ret += f'<td><button onclick=\"window.location.href = \'play_track/{track.id}\';\" disabled>Play</button></td>'
    #         ret += f'<td>{track.track_title}</td>'
    #         ret += f'<td>{track.album}</td>'
    #         ret += f'<td>{track.album.artist}</td>'
    #         ret += f'<td>{track.album.year}</td>'
    #         ret += f'<td>{track.played}</td>'
    #         ret += f'<td>{track}</td>'
    #         ret += f'</tr>'
    #
    #     ret += f'</table>\n'
    #     ret += '</body>\n'
    #     ret += '</html>\n'
    #     return HttpResponse(ret)

    def albums(self):
        global jukeoroni

        if not jukeoroni.mode == Settings.MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['album']:

            return HttpResponseRedirect('/jukeoroni')

        box = get_active_box(jukeoroni)

        # artists = Artist.objects.all().order_by('name')
        # sort artist list by name. if not lowercase: Apples, Cherries, bananas...
        #      DjangoTrack.objects.filter(album__album_type=self.album_type)
        artists = Artist.objects.all().annotate(lower_name=Lower('name')).order_by('lower_name')

        bg_color = get_bg_color(box.layout.bg_color)

        ret = '<html>\n'
        ret += '<head>\n'
        # ret += '    <meta http-equiv="refresh" content="10" >\n'
        ret += '<link rel="icon" type="image/x-icon" href="/jukeoroni/favicon.ico">\n'
        ret += '</head>\n'
        ret += '<body style="background-color:#{0};">\n'.format(bg_color)
        ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni\';\">Back</button>\n'
        # random_albums = random.sample(list(Album.objects.all()), RANDOM_ALBUMS)
        random_albums = random.sample(list(Album.objects.filter(album_type=box.album_type)), Settings.RANDOM_ALBUMS)
        if bool(random_albums):
            ret += f'<hr>'
            ret += f'<center><h4>Suggestions :)</h4></center>'
            for random_album in random_albums:
                ret += '<div>\n'
                ret += f'<button style=\"width:100%\" onclick=\"window.location.href = \'{random_album.id}\';\">{random_album.artist} - {random_album.year} - {random_album.album_title}</button>\n'
                ret += '</div>\n'
            # ret += f'<hr>'

        for artist in artists:
            albums = Album.objects.filter(artist=artist, album_type=box.album_type).order_by('year', 'album_title')
            if not bool(albums):
                continue
            ret += f'<hr>'
            ret += f'<center><h1>{artist.name}</h1></center>'
            year = None
            for album in albums:
                if year != album.year:
                    ret += f'<div><center>{album.year}</center></div>'
                    year = album.year
                ret += '<div>\n'
                ret += f'<button style=\"width:100%\" onclick=\"window.location.href = \'{album.id}\';\">{album.album_title}</button>\n'
                ret += '</div>\n'
        ret += '</body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def play_album(self, album_id):
        global jukeoroni

        if not jukeoroni.mode == Settings.MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['album']:

            return HttpResponseRedirect('/jukeoroni')

        box = get_active_box(jukeoroni)

        jukeoroni.mode = Settings.MODES[box.box_type]['on_air']['album']
        if box.loader_mode != 'album':
            box.set_loader_mode_album()
        box.play_album(album_id=album_id)

        return HttpResponseRedirect('/jukeoroni')

    def radio_index(self):
        global jukeoroni

        if not jukeoroni.mode == Settings.MODES['radio']['standby'] \
                and not jukeoroni.mode == Settings.MODES['radio']['on_air']:

            return HttpResponseRedirect('/jukeoroni')

        stations = Station.objects.all().order_by('display_name')

        bg_color = get_bg_color(jukeoroni.layout_radio.bg_color)

        ret = '<html>\n'
        ret += '<head>\n'
        ret += '<meta http-equiv="refresh" content="10" >\n'
        ret += '<link rel="icon" type="image/x-icon" href="/jukeoroni/favicon.ico">\n'
        ret += '</head>\n'
        ret += '<body style="background-color:#{0};">\n'.format(bg_color)
        ret += f'<button style=\"width:100%; \" onclick=\"window.location.href = \'/jukeoroni/set_standby\';\">Back to Menu</button>\n'
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
           ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/resume\';\">Resume</button>\n'
        else:
            if jukeoroni.mode == Settings.MODES['radio']['on_air']:
                ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\">Pause</button>\n'
            else:
                ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\" disabled>Pause</button>\n'
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
        # if bool(stations):
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

        # in case the channel has no station assigned
        channels_unstationed = Channel.objects.filter(station=None).order_by('display_name')
        if channels_unstationed:
            ret += f'<center><h2>Uncategorized</h2></center>\n'
        for channel_unstationed in channels_unstationed:
            if channel_unstationed.is_enabled:
                if channel_unstationed == jukeoroni.radio.is_on_air:
                    ret += f'<button style=\"width:100%; background-color:green; \" onclick=\"window.location.href = \'stop\';\">{channel_unstationed.display_name}</button>\n'
                else:
                    ret += f'<button style=\"width:100%\" onclick=\"window.location.href = \'{channel_unstationed.display_name_short}/play\';\">{channel_unstationed.display_name}</button>\n'

        ret += '</body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

    def radio_play(self, display_name_short):
        global jukeoroni

        if not jukeoroni.mode == Settings.MODES['radio']['standby'] \
                and not jukeoroni.mode == Settings.MODES['radio']['on_air']:

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

        jukeoroni.mode = Settings.MODES['radio']['on_air']

        # time_out = 10.0
        while not jukeoroni.radio.is_on_air == channel:  # or time_out <= 0.0:
            time.sleep(0.1)
            # time_out -= 0.1

        return HttpResponseRedirect('/jukeoroni')

    def radio_stop(self):
        global jukeoroni

        if not jukeoroni.mode == Settings.MODES['radio']['standby'] \
                and not jukeoroni.mode == Settings.MODES['radio']['on_air']:

            return HttpResponseRedirect('/jukeoroni')

        jukeoroni.mode = Settings.MODES['radio']['standby']

        # time_out = 10.0
        while jukeoroni.radio.is_on_air is not None:  # or time_out <= 0.0:
            time.sleep(0.1)
            # time_out -= 0.1

        return HttpResponseRedirect('/jukeoroni')
