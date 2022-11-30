import base64
import sys
import re
import os
import random
import time
import io
import alsaaudio
import logging
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotModified, JsonResponse
from django.views import View
from player.jukeoroni.jukeoroni import JukeOroni
from player.models import Album, Channel, Station, Artist, Track, Video
from player.jukeoroni.lyric_genius import get_lyrics
from player.jukeoroni.settings import Settings


PIMORONI_SATURATION = 1.0
FONT_SIZE = 24
SLEEP_IMAGE = os.path.join(Settings.BASE_DIR, 'player', 'static', 'zzz.jpg')
LOADING_IMAGE = os.path.join(Settings.BASE_DIR, 'player', 'static', 'loading.jpg')
STANDARD_COVER = os.path.join(Settings.BASE_DIR, 'player', 'static', 'cover_std.png')
PIMORONI_FONT = os.path.join(Settings.BASE_DIR, 'player', 'static', 'gotham-black.ttf')


padding = '2px 5px'
BUTTON_HEIGHT = '100px'
BUTTON_ICON_SIZE_FACTOR = 2.0
COLUMN_WIDTH = 101


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


# TODO:
#  <img width="{int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR)}" height="{int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR)}" src="{Settings.BUTTON_ICONS[n]}" />


if '/data/venv/bin/gunicorn' in sys.argv:
    ######################################
    # Comment this block to do DB migrations
    #  as well as:
    #  sudo systemctl stop nginx.service
    jukeoroni = JukeOroni(test=False)
    jukeoroni.turn_on(disable_track_loader=Settings.DISABLE_TRACK_LOADER)
    jukeoroni.jukebox.set_auto_update_tracklist_on()
    jukeoroni.meditationbox.set_auto_update_tracklist_on()
    # jukeoroni.episodicbox.set_auto_update_tracklist_on()
    # jukeoroni.jukebox.track_list_generator_thread()
    ######################################
else:
    jukeoroni = None


def get_bg_color(rgb):
    # _hex = None
    # if len(rgb) == 3:
    #     _hex = '%02x%02x%02x' % rgb
    # elif len(rgb) == 4:
    #     _hex = '%02x%02x%02x%02x' % rgb
    # # return _hex
    return '606060'  # TODO: constant until solution to avoid black text on black bg


def get_eq_btn_color(vol_equal):
    percent = float(vol_equal) / 100.0
    max = 255.0
    _hex = '#%02x%02x%02x' % (round(max * percent), round(max * percent), round(max * percent))
    return _hex


def encode_image(img):
    data = io.BytesIO()
    img.save(data, "PNG")
    encoded_img_data = base64.b64encode(data.getvalue())
    return encoded_img_data.decode('ascii')


def encoded_screen(img):
    data = io.BytesIO()
    # img = jukeoroni.layout_radio.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.radio.cover,
    #                                         title=jukeoroni.radio.stream_title)
    img = img.rotate(270, expand=True)
    img.save(data, "PNG")
    encoded_img_data = base64.b64encode(data.getvalue())
    return encoded_img_data.decode('ascii')


def get_active_box(_jukeoroni):
    if _jukeoroni.mode == Settings.MODES['jukebox']['standby']['random'] \
            or _jukeoroni.mode == Settings.MODES['jukebox']['standby']['album'] \
            or _jukeoroni.mode == Settings.MODES['jukebox']['on_air']['random'] \
            or _jukeoroni.mode == Settings.MODES['jukebox']['on_air']['album']:
        box = _jukeoroni.jukebox
    elif _jukeoroni.mode == Settings.MODES['radio']['standby']['random'] \
            or _jukeoroni.mode == Settings.MODES['radio']['on_air']['random']:
        box = _jukeoroni.radio
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
    elif _jukeoroni.mode == Settings.MODES['podcastbox']['standby']['random'] \
            or _jukeoroni.mode == Settings.MODES['podcastbox']['standby']['album'] \
            or _jukeoroni.mode == Settings.MODES['podcastbox']['on_air']['random'] \
            or _jukeoroni.mode == Settings.MODES['podcastbox']['on_air']['album']:
        box = _jukeoroni.podcastbox
    elif _jukeoroni.mode == Settings.MODES['videobox']['standby']['random'] \
            or _jukeoroni.mode == Settings.MODES['videobox']['on_air']['pause'] \
            or _jukeoroni.mode == Settings.MODES['videobox']['on_air']['random']:
        box = _jukeoroni.videobox
    else:
        LOG.error('No Box determined, setting to box = None')
        box = None
    return box


def get_volume_values(context):
    m = alsaaudio.Mixer('Digital')

    vol = m.getvolume()[0]

    context['volume'] = {'vol': vol, 'color': get_eq_btn_color(vol)}

    _m = alsaaudio.mixers(device='equal')
    # ['00. 31 Hz', '01. 63 Hz', '02. 125 Hz', '03. 250 Hz', '04. 500 Hz', '05. 1 kHz', '06. 2 kHz', '07. 4 kHz',
    #  '08. 8 kHz', '09. 16 kHz']

    m_equal_31hz = alsaaudio.Mixer(_m[0], device='equal')
    m_equal_63hz = alsaaudio.Mixer(_m[1], device='equal')
    m_equal_125hz = alsaaudio.Mixer(_m[2], device='equal')
    m_equal_250hz = alsaaudio.Mixer(_m[3], device='equal')
    m_equal_500hz = alsaaudio.Mixer(_m[4], device='equal')
    m_equal_1khz = alsaaudio.Mixer(_m[5], device='equal')
    m_equal_2khz = alsaaudio.Mixer(_m[6], device='equal')
    m_equal_4khz = alsaaudio.Mixer(_m[7], device='equal')
    m_equal_8khz = alsaaudio.Mixer(_m[8], device='equal')
    m_equal_16khz = alsaaudio.Mixer(_m[9], device='equal')

    vol_equal_31hz = m_equal_31hz.getvolume()[0]
    vol_equal_63hz = m_equal_63hz.getvolume()[0]
    vol_equal_125hz = m_equal_125hz.getvolume()[0]
    vol_equal_250hz = m_equal_250hz.getvolume()[0]
    vol_equal_500hz = m_equal_500hz.getvolume()[0]
    vol_equal_1khz = m_equal_1khz.getvolume()[0]
    vol_equal_2khz = m_equal_2khz.getvolume()[0]
    vol_equal_4khz = m_equal_4khz.getvolume()[0]
    vol_equal_8khz = m_equal_8khz.getvolume()[0]
    vol_equal_16khz = m_equal_16khz.getvolume()[0]

    context['eq'] = dict()

    context['eq']['eq_31hz'] = {'vol': vol_equal_31hz, 'color': get_eq_btn_color(vol_equal_31hz)}
    context['eq']['eq_63hz'] = {'vol': vol_equal_63hz, 'color': get_eq_btn_color(vol_equal_63hz)}
    context['eq']['eq_125hz'] = {'vol': vol_equal_125hz, 'color': get_eq_btn_color(vol_equal_125hz)}
    context['eq']['eq_250hz'] = {'vol': vol_equal_250hz, 'color': get_eq_btn_color(vol_equal_250hz)}
    context['eq']['eq_500hz'] = {'vol': vol_equal_500hz, 'color': get_eq_btn_color(vol_equal_500hz)}
    context['eq']['eq_1khz'] = {'vol': vol_equal_1khz, 'color': get_eq_btn_color(vol_equal_1khz)}
    context['eq']['eq_2khz'] = {'vol': vol_equal_2khz, 'color': get_eq_btn_color(vol_equal_2khz)}
    context['eq']['eq_4khz'] = {'vol': vol_equal_4khz, 'color': get_eq_btn_color(vol_equal_4khz)}
    context['eq']['eq_8khz'] = {'vol': vol_equal_8khz, 'color': get_eq_btn_color(vol_equal_8khz)}
    context['eq']['eq_16khz'] = {'vol': vol_equal_16khz, 'color': get_eq_btn_color(vol_equal_16khz)}

    return context


# def get_header(bg_color, refresh=True):
#     # bg_color = get_bg_color(jukeoroni.layout_standby.bg_color)
#
#     ret = '<html>\n'
#     ret += '<head>\n'
#     if refresh:
#         ret += '<meta http-equiv="refresh" content="10" >\n'
#     ret += '<link rel="icon" type="image/x-icon" href="/jukeoroni/favicon.ico">\n'
#     ret += '</head>\n'
#     ret += '<body style="background-color:#{0};">\n'.format(bg_color)
#
#     return ret


# def get_footer(ret):
#     ret += '<hr>\n'
#     ret += '<center>'
#     ret += '<table border="0" cellspacing="0" style="text-align:center;margin-left:auto;margin-right:auto;border-collapse: collapse;">'
#     ret += '<tr style="border: none;">'
#
#     # if back is not None:
#     #     ret += '<td style="border-right: solid 1px #000;border-left: solid 1px #000;padding: 5px 10px;">'
#     #     ret += f'<a href="{back}" target="_self">Back</a>'
#     #     ret += '</td>'
#
#     ret += '<td style="border-right: solid 1px #000;border-left: solid 1px #000;padding: 5px 10px;">'
#     ret += '<a href="/admin" target="_blank">Admin</a>'
#     ret += '</td>'
#
#     ret += '<td style="border-right: solid 1px #000;border-left: solid 1px #000;padding: 5px 10px;">'  # border-right: solid 1px #f00; border-left: solid 1px #f00;
#     ret += '<a href="/transmission" target="_blank">Transmission</a>'
#     ret += '</td>'
#
#     ret += '<td style="border-right: solid 1px #000;border-left: solid 1px #000;padding: 5px 10px;">'
#     ret += '<a href="/webmin" target="_blank">Webmin</a>'
#     ret += '</td>'
#
#     ret += '</tr>'
#     ret += '</table>'
#     ret += '</center>'
#
#     return ret


# Create your views here.
# TODO: rmove player for unittesting new juke
class JukeOroniView(View):

    def get(self, request):
        global jukeoroni

        context = dict()

        try:
            jukeoroni.mode
        except (NameError,):
            return HttpResponse('JukeOroni web interface is not available.')

        if jukeoroni.mode == Settings.MODES['radio']['standby']['random'] \
                or jukeoroni.mode == Settings.MODES['radio']['on_air']['random']:

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

        elif jukeoroni.mode == Settings.MODES['podcastbox']['standby']['album'] \
                or jukeoroni.mode == Settings.MODES['podcastbox']['standby']['random'] \
                or jukeoroni.mode == Settings.MODES['podcastbox']['on_air']['album'] \
                or jukeoroni.mode == Settings.MODES['podcastbox']['on_air']['random']:

            return HttpResponseRedirect('podcastbox/')

        elif jukeoroni.mode == Settings.MODES['videobox']['standby']['random'] \
                or jukeoroni.mode == Settings.MODES['videobox']['on_air']['pause'] \
                or jukeoroni.mode == Settings.MODES['videobox']['on_air']['random']:

            return HttpResponseRedirect('videobox/')

        elif jukeoroni.mode == Settings.MODES['jukeoroni']['standby'] \
                or jukeoroni.mode == Settings.MODES['jukeoroni']['off']:

            bg_color = get_bg_color(jukeoroni.layout_standby.bg_color)
            context['bg_color'] = bg_color

            _items_enabled = 0

            context['buttons'] = list()

            if any([
                        Settings.ENABLE_JUKEBOX,
                        Settings.ENABLE_RADIO,
                        Settings.ENABLE_MEDITATION,
                        Settings.ENABLE_EPISODIC,
                        Settings.ENABLE_VIDEO,
                    ]):

                if Settings.ENABLE_JUKEBOX:
                    context['buttons'].append(
                        {
                            'class': 'btn_header',
                            'column_width': COLUMN_WIDTH,
                            'padding': padding,

                            'button_title': 'JukeBox',
                            'onclick': 'window.location.href = \'/jukeoroni/set_jukebox\'',
                            'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Player"])}',

                            'button_height': BUTTON_HEIGHT,

                        }
                    )
                    _items_enabled += 1

                if Settings.ENABLE_RADIO:
                    context['buttons'].append(
                        {
                            'class': 'btn_header',
                            'column_width': COLUMN_WIDTH,
                            'padding': padding,

                            'button_title': 'Radio',
                            'onclick': 'window.location.href = \'/jukeoroni/set_radio\'',
                            'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Radio"])}',

                            'button_height': BUTTON_HEIGHT,

                        }
                    )
                    _items_enabled += 1

                if Settings.ENABLE_MEDITATION:
                    context['buttons'].append(
                        {
                            'class': 'btn_header',
                            'column_width': COLUMN_WIDTH,
                            'padding': padding,

                            'button_title': 'Meditation',
                            'onclick': 'window.location.href = \'/jukeoroni/set_meditationbox\'',
                            'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Meditation"])}',

                            'button_height': BUTTON_HEIGHT,

                        }
                    )
                    _items_enabled += 1

                if Settings.ENABLE_AUDIOBOOK:
                    context['buttons'].append(
                        {
                            'class': 'btn_header',
                            'column_width': COLUMN_WIDTH,
                            'padding': padding,

                            'button_title': 'Audiobook',
                            'onclick': 'window.location.href = \'/jukeoroni/set_audiobookbox\'',
                            'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Audiobook"])}',

                            'button_height': BUTTON_HEIGHT,

                        }
                    )
                    _items_enabled += 1

                if Settings.ENABLE_PODCAST:
                    context['buttons'].append(
                        {
                            'class': 'btn_header',
                            'column_width': COLUMN_WIDTH,
                            'padding': padding,

                            'button_title': 'Podcast',
                            'onclick': 'window.location.href = \'/jukeoroni/set_podcastbox\'',
                            'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Podcast"])}',

                            'button_height': BUTTON_HEIGHT,

                        }
                    )
                    _items_enabled += 1

                if Settings.ENABLE_VIDEO:
                    context['buttons'].append(
                        {
                            'class': 'btn_header',
                            'column_width': COLUMN_WIDTH,
                            'padding': padding,

                            'button_title': 'Video',
                            'onclick': 'window.location.href = \'/jukeoroni/set_videobox\'',
                            'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                            'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Video"])}',

                            'button_height': BUTTON_HEIGHT,

                        }
                    )
                    _items_enabled += 1

                while _items_enabled < 4:
                    context['buttons'].append(
                        {
                            # 'class': 'btn_header',
                            'column_width': COLUMN_WIDTH,
                            'padding': padding,

                            'button_title': '',
                            'onclick': '',
                            'img_width': None,
                            'img_height': None,
                            'img_src': f'',

                            'button_height': BUTTON_HEIGHT,

                        }
                    )
                    _items_enabled += 1

            img = jukeoroni.layout_standby.get_layout(labels=jukeoroni.LABELS, buttons=False)
            encoded_img_data = encoded_screen(img)
            context['encoded_img_data'] = encoded_img_data
            context['encoded_img_data_class'] = 'box_image'

            context['enable_volume'] = Settings.ENABLE_VOLUME

            if Settings.ENABLE_VOLUME:
                context = get_volume_values(context=context)

            return render(request=request, template_name='player/box_base.html', context=context)

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

    def set_podcastbox(self):
        global jukeoroni

        jukeoroni.mode = Settings.MODES['podcastbox']['standby'][jukeoroni.podcastbox.loader_mode]

        return HttpResponseRedirect('/jukeoroni/podcastbox')

    def set_videobox(self):
        global jukeoroni

        jukeoroni.mode = Settings.MODES['videobox']['standby'][jukeoroni.videobox.loader_mode]

        return HttpResponseRedirect('/jukeoroni/videobox')

    def set_radio(self):
        global jukeoroni

        jukeoroni.mode = Settings.MODES['radio']['standby']['random']

        return HttpResponseRedirect('/jukeoroni/radio')

    def set_standby(self):
        global jukeoroni

        jukeoroni.mode = Settings.MODES['jukeoroni']['standby']

        return HttpResponseRedirect('/jukeoroni')

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

        elif jukeoroni.mode == Settings.MODES['podcastbox']['standby']['random']:
            jukeoroni.mode = Settings.MODES['podcastbox']['standby']['album']
        elif jukeoroni.mode == Settings.MODES['podcastbox']['on_air']['random']:
            jukeoroni.mode = Settings.MODES['podcastbox']['on_air']['album']
        elif jukeoroni.mode == Settings.MODES['podcastbox']['standby']['album']:
            jukeoroni.mode = Settings.MODES['podcastbox']['standby']['random']
        elif jukeoroni.mode == Settings.MODES['podcastbox']['on_air']['album']:
            jukeoroni.mode = Settings.MODES['podcastbox']['on_air']['random']

        return HttpResponseRedirect('/jukeoroni')

    def play(self):
        global jukeoroni

        box = get_active_box(jukeoroni)

        if box == jukeoroni.videobox:
            # if jukeoroni.videobox.omxplayer is None:
            #     return HttpResponseRedirect('/jukeoroni')
            if jukeoroni.mode == Settings.MODES[box.box_type]['standby'][box.loader_mode]:
                jukeoroni.mode = Settings.MODES[box.box_type]['on_air'][box.loader_mode]
            elif jukeoroni.mode == Settings.MODES[box.box_type]['on_air']['pause']:
                jukeoroni.mode = Settings.MODES[box.box_type]['on_air']['random']
            elif jukeoroni.mode == Settings.MODES[box.box_type]['on_air']['random']:
                jukeoroni.mode = Settings.MODES[box.box_type]['on_air']['pause']

            return HttpResponseRedirect('/jukeoroni')

        if not jukeoroni.mode == Settings.MODES[box.box_type]['on_air'][box.loader_mode]:
            jukeoroni.mode = Settings.MODES[box.box_type]['on_air'][box.loader_mode]

        return HttpResponseRedirect('/jukeoroni')

    def load_movie_by_title(self, video_title):
        global jukeoroni

        box = get_active_box(jukeoroni)

        try:
            video = Video.objects.get(video_title=video_title)
        except Exception:
            box.LOG.exception('Could not get video by video_title: ')
            return HttpResponseRedirect('/jukeoroni')

        if box == jukeoroni.videobox:
            if jukeoroni.mode != Settings.MODES[box.box_type]['standby']['random']:
                jukeoroni.mode = Settings.MODES[box.box_type]['standby']['random']
                time.sleep(1.0)

            jukeoroni.insert(video)
            # video = Video.objects.get(video_title=video_title)
            # jukeoroni.videobox.omx_player_thread(video_file=os.path.join(Settings.VIDEO_DIR, video.video_source))
            # jukeoroni.videobox.omxplayer.load(source=os.path.join(Settings.VIDEO_DIR, video.video_source), pause=True)
            jukeoroni.play()

        while video.omxplayer is None:
            time.sleep(0.1)

        return HttpResponseRedirect('/jukeoroni')

    # def pause(self):
    #     global jukeoroni
    #
    #     box = get_active_box(jukeoroni)
    #
    #     if not jukeoroni.mode == Settings.MODES[box.box_type]['standby'][box.loader_mode]:
    #         jukeoroni.mode = Settings.MODES[box.box_type]['standby'][box.loader_mode]
    #
    #     # box.omxplayer.play_pause()
    #
    #     return HttpResponseRedirect('/+jukeoroni')

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

        if box == jukeoroni.videobox:
            jukeoroni.mode = Settings.MODES[box.box_type]['standby']['random']

            return HttpResponseRedirect('/jukeoroni')

        if jukeoroni.mode == Settings.MODES[box.box_type]['on_air'][box.loader_mode]:
            jukeoroni.mode = Settings.MODES[box.box_type]['standby'][box.loader_mode]

        return HttpResponseRedirect('/jukeoroni')


class AlbumView(View):
    def get(self, request):

        query = self.request.GET.get("q", None)
        search_for = self.request.GET.get("type", None)

        global jukeoroni
        box = get_active_box(jukeoroni)

        if box is None \
                or box is not jukeoroni.jukebox \
                and box is not jukeoroni.meditationbox:
            return HttpResponseRedirect('/jukeoroni')

        context = dict()

        context['box_type'] = box.box_type

        bg_color = get_bg_color(box.layout.bg_color)

        context['bg_color'] = bg_color

        context['buttons'] = list()
        context['buttons'].append(
            {
                'class': 'btn_back',
                'column_width': COLUMN_WIDTH,
                'padding': padding,

                'button_title': 'Back',
                'onclick': 'window.location.href = \'/jukeoroni\'',
                'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Back"])}',

                'button_height': BUTTON_HEIGHT,

            }
        )

        for i in range(3):
            # empty, invisible buttons
            context['buttons'].append(
                {
                    # 'class': 'btn_back',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': '',
                    'onclick': '',
                    'img_width': None,
                    'img_height': None,
                    'img_src': f'',

                    'button_height': BUTTON_HEIGHT,

                }
            )

        img = box.layout.get_layout(labels=jukeoroni.LABELS, buttons=False)
        context['encoded_img_data'] = encoded_screen(img)
        context['encoded_img_data_class'] = 'box_image'

        context['random_albums'] = random.sample(list(Album.objects.filter(album_type=box.album_type)), Settings.RANDOM_ALBUMS)

        # TODO 2 - optimize performance
        albums = Album.objects.filter(album_type=box.album_type).order_by('album_title')

        if query:
            # albums = albums.filter(Q(album_title__icontains=query) | Q(artist__name__icontains=query) | Q(track__track_title__icontains=query)).order_by('year', 'album_title')

            if search_for == "albums":
                albums = albums.filter(Q(album_title__icontains=query)).order_by('year', 'album_title').distinct()

            elif search_for == "artists":
                albums = albums.filter(Q(artist__name__icontains=query)).order_by('year', 'album_title').distinct()

            elif search_for == "tracks":
                albums = albums.filter(Q(track__track_title__icontains=query)).order_by('year', 'album_title').distinct()

            elif search_for is None or search_for == "everything":
                albums = albums.filter(Q(album_title__icontains=query) | Q(artist__name__icontains=query) | Q(track__track_title__icontains=query)).order_by('year', 'album_title').distinct()
        # else:
            # albums = Album.objects.filter(album_type=box.album_type).order_by('album_title').distinct()

        context['query'] = {'query': query, 'search_for': search_for}

        context['tags'] = list()
        for album in albums:
            res = re.findall(r'\[.*?\]', album.album_title)
            context['tags'] += res

        context['tags'] = list(set(context['tags']))

        paginator = Paginator(albums, 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['page_obj'] = page_obj

        context['page_range'] = paginator.page_range

        return render(request=request, template_name='player/albums.html', context=context)

    def play_album(self, album_id):
        global jukeoroni
        box = get_active_box(jukeoroni)

        if box is not jukeoroni.jukebox \
                and box is not jukeoroni.meditationbox:
            return HttpResponseRedirect('/jukeoroni')

        jukeoroni.mode = Settings.MODES[box.box_type]['on_air']['album']
        if box.loader_mode != 'album':
            box.set_loader_mode_album()
        box.play_album(album_id=album_id)

        return HttpResponseRedirect('/jukeoroni')


class BoxView(View):
    def get(self, request):

        global jukeoroni

        context = dict()

        try:
            jukeoroni.mode
        except (NameError, ):
            return HttpResponse('JukeOroni web interface is not available.')

        if not jukeoroni.mode == Settings.MODES['jukebox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['jukebox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['radio']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['radio']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['meditationbox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['audiobookbox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['podcastbox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['podcastbox']['standby']['album'] \
                and not jukeoroni.mode == Settings.MODES['podcastbox']['on_air']['random'] \
                and not jukeoroni.mode == Settings.MODES['podcastbox']['on_air']['album'] \
                and not jukeoroni.mode == Settings.MODES['videobox']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['videobox']['on_air']['pause'] \
                and not jukeoroni.mode == Settings.MODES['videobox']['on_air']['random']:
            return HttpResponseRedirect('/jukeoroni')

        box = get_active_box(jukeoroni)

        context['box'] = box

        bg_color = get_bg_color(box.layout.bg_color)

        context['bg_color'] = bg_color

        context['buttons'] = list()

        # if box == jukeoroni.videobox:
        if jukeoroni.mode == Settings.MODES['videobox']['on_air']['pause']:
            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': 'Back',
                    'onclick': 'window.location.href = \'/jukeoroni/videobox/stop\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Stop"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        elif jukeoroni.mode == Settings.MODES[box.box_type]['on_air'][box.loader_mode]:

            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': 'Stop',
                    'onclick': f'window.location.href = \'/jukeoroni/{box.box_type}/stop\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Stop"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        else:

            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': 'Back',
                    'onclick': 'window.location.href = \'/jukeoroni/set_standby\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Menu"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        if jukeoroni.mode == Settings.MODES['videobox']['standby']['random']:

            if jukeoroni.videobox.omxplayer is None:

                context['buttons'].append(
                    {
                        'class': 'btn_header',
                        'column_width': COLUMN_WIDTH,
                        'padding': padding,

                        'button_title': jukeoroni.mode['buttons']['0X00'],
                        'onclick': 'window.location.href = \'/jukeoroni/videobox/play\'',
                        'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                        'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                        'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Play"])}',

                        'button_height': BUTTON_HEIGHT,
                    }
                )

            else:

                context['buttons'].append(
                    {
                        'class': 'btn_header',
                        'column_width': COLUMN_WIDTH,
                        'padding': padding,

                        'button_title': jukeoroni.mode['buttons']['0X00'],
                        'onclick': 'window.location.href = \'/jukeoroni/videobox/play\'',
                        'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                        'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                        'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Play"])}',

                        'button_height': BUTTON_HEIGHT,
                    }
                )

        elif jukeoroni.mode == Settings.MODES['videobox']['on_air']['pause']:
            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': jukeoroni.mode['buttons']['0X00'],
                    'onclick': 'window.location.href = \'/jukeoroni/videobox/play\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Play"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        elif jukeoroni.mode == Settings.MODES['videobox']['on_air']['random']:
            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': jukeoroni.mode['buttons']['0X00'],
                    'onclick': 'window.location.href = \'/jukeoroni/videobox/play\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Pause"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        else:
            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': jukeoroni.mode['buttons']['0X00'],
                    'onclick': f'window.location.href = \'/jukeoroni/{box.box_type}/play_next\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Next"])}' if jukeoroni.mode ==
                                                                                                                   Settings.MODES[
                                                                                                                       box.box_type][
                                                                                                                       'on_air'][
                                                                                                                       box.loader_mode] else f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Play"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        if jukeoroni.mode == Settings.MODES['videobox']['standby']['random'] \
                or jukeoroni.mode == Settings.MODES['videobox']['on_air']['pause'] \
                or jukeoroni.mode == Settings.MODES['videobox']['on_air']['random']:

            context['buttons'].append(
                {
                    # 'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': '',
                    'onclick': '',
                    'img_width': None,
                    'img_height': None,
                    'img_src': f'',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        else:

            context['buttons'].append(
                {
                    # 'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': '',
                    'onclick': '',
                    'img_width': None,
                    'img_height': None,
                    'img_src': f'',

                    'button_height': BUTTON_HEIGHT,
                }
            )

            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': str(box.loader_mode).capitalize(),
                    'onclick': f'window.location.href = \'/jukeoroni/{box.box_type}/switch_mode\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Random -> Album"])}' if str(box.loader_mode) == 'random' else f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Album -> Random"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        _success = False

        # context['vol'] = list()
        #
        # context['vol'].append(
        #     {
        #         'button_title': 'vol_dow',
        #         'onclick': f'window.location.href = \'/jukeoroni/vol_down\'',
        #     }
        # )
        #
        # context['vol'].append(
        #     {
        #         'button_title': 'vol_reset',
        #         'onclick': f'window.location.href = \'/jukeoroni/vol_reset\'',
        #     }
        # )
        #
        # context['vol'].append(
        #     {
        #         'button_title': 'vol_up',
        #         'onclick': f'window.location.href = \'/jukeoroni/vol_up\'',
        #     }
        # )

        img = None

        # if hasattr(jukeoroni, 'videobox'):
        #
        #     if box == jukeoroni.videobox:
        #         if jukeoroni.mode == Settings.MODES['videobox']['standby']['random']:
        #             img = box.layout.get_layout(labels=jukeoroni.LABELS)
        #         elif jukeoroni.mode == Settings.MODES['videobox']['on_air']['pause'] \
        #                 or jukeoroni.mode == Settings.MODES['videobox']['on_air']['random']:
        #             img = box.layout.get_layout(labels=jukeoroni.LABELS, cover=Resource().VIDEO_ON_AIR_DEFAULT_IMAGE)

        if jukeoroni.mode == Settings.MODES['radio']['standby']['random']:
            img = box.layout.get_layout(labels=jukeoroni.LABELS, cover=box.cover, title=box.stream_title, buttons=False)

        elif jukeoroni.mode == Settings.MODES[box.box_type]['standby']['album'] \
                or jukeoroni.mode == Settings.MODES[box.box_type]['standby']['random']:
            img = box.layout.get_layout(labels=jukeoroni.LABELS, buttons=False)

        elif jukeoroni.mode == Settings.MODES[box.box_type]['on_air']['album'] \
                or jukeoroni.mode == Settings.MODES[box.box_type]['on_air']['random']:
            try:
                img = box.layout.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.inserted_media.cover_album,
                                            artist=jukeoroni.inserted_media.cover_artist, buttons=False)
            except AttributeError:
                img = box.layout.get_layout(labels=jukeoroni.LABELS, loading=True, buttons=False)

        if img is not None:
            encoded_img_data = encoded_screen(img)
            context['encoded_img_data'] = encoded_img_data
            context['encoded_img_data_class'] = 'box_image'

        context['inserted_media'] = jukeoroni.inserted_media
        context['loading_track'] = box.loading_track
        context['queue'] = box.tracks

        #     ret += '<center><div>Inserted/Playing</div></center>'
    #     if jukeoroni.inserted_media is not None:
    #         ret += f'<div style="text-align: center;">{str(jukeoroni.inserted_media.artist)}</div>'
    #         ret += f'<div style="text-align: center;">{str(jukeoroni.inserted_media.album)}</div>'
    #         ret += f'<div style="text-align: center;">{str(jukeoroni.inserted_media.track_title)}</div>'
    #         ret += f'<div style="text-align: center;">(ID: {str(jukeoroni.inserted_media.django_track.id)})</div>'
    #     else:
    #         ret += '<div style="text-align: center;">None</div>'
    #
    #     if box.loading_track is not None:
    #         ret += '<hr>'
    #         ret += '<center><div>Loading</div></center>'
    #         ret += '<center><div>{0}</div></center>'.format(f'{box.loading_track.artist} - {box.loading_track.album} ({box.loading_track.year}) - {box.loading_track.track_title} ({str(round(box.loading_track.size_cached / (1024.0 * 1024.0), 1))} of {str(round(box.loading_track.size / (1024.0 * 1024.0), 1))} MB)')
    #     ret += '<hr>'
    #     ret += '<center><div>Queue</div></center>'
    #
    #     ret += '<ol>'
    #     ret += '<center><table border="0" cellspacing="0">'
    #     for track in box.tracks:
    #         ret += '<tr>'
    #         ret += '<td>'
    #         ret += '<li>&nbsp;</li>'
    #         ret += '</td>'
    #         ret += '<td>{0} (ID: {1})</td>'.format(track, track.django_track.id)
    #         if box.tracks.index(track) == 0:
    #             ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/{1}/{0}/as_first\';\" disabled>Set 1st</button></td>'.format(str(box.tracks.index(track)), str(box.box_type))
    #         else:
    #             ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/{1}/{0}/as_first\';\">Set 1st</button></td>'.format(str(box.tracks.index(track)), str(box.box_type))
    #         ret += '<td><button onclick=\"window.location.href = \'/jukeoroni/{1}/{0}/pop\';\">Remove from Queue</button></td>'.format(str(box.tracks.index(track)), str(box.box_type))
    #         ret += f'</tr>'
    #     ret += f'</table></center>'
    #     ret += f'</ol>'
    #     ret += f'<hr>'
    #
    #     if box.track_list_updater_running:
    #         ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/update_track_list\';\"  disabled>Update Track List</button>\n'.format(str(box.box_type))
    #     else:
    #         ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/update_track_list\';\">Update Track List</button>\n'.format(str(box.box_type))
    #
    #     if jukeoroni.paused:
    #         ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/resume\';\">Resume</button>\n'
    #     else:
    #         if jukeoroni.mode == Settings.MODES[box.box_type]['on_air'][box.loader_mode]:
    #             ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\">Pause</button>\n'
    #         else:
    #             ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/pause\';\" disabled>Pause</button>\n'
    #
    #     ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/albums\';\">Albums</button>\n'.format(str(box.box_type))
    #     # ret += '<button style=\"width:100%\" onclick=\"window.location.href = \'/jukeoroni/{0}/tracks\';\">Tracks</button>\n'.format(str(box.box_type))

        context['albums_buttons'] = list()

        context['albums_buttons'].append(
            {
                    'class': 'btn_albums',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': 'Library/Albums',
                    'onclick': f'window.location.href = \'/jukeoroni/{box.box_type}/albums\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Library"])}',

                    'button_height': BUTTON_HEIGHT,
                }
        )

        context['enable_volume'] = Settings.ENABLE_VOLUME

        if Settings.ENABLE_VOLUME:

            context = get_volume_values(context=context)

        # if jukeoroni.inserted_media is not None:
        #
        #     context['lyrics'] = jukeoroni.inserted_media.lyrics
        #
        # else:
        #     context['lyrics'] = ''

        return render(request=request, template_name='player/box_base.html', context=context)


class BoxViewRadio(View):
    def get(self, request):

        global jukeoroni

        context = dict()

        try:
            jukeoroni.mode
        except (NameError, ):
            return HttpResponse('JukeOroni web interface is not available.')

        if not jukeoroni.mode == Settings.MODES['radio']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['radio']['on_air']['random']:
            return HttpResponseRedirect('/jukeoroni')

        context['bg_color'] = get_bg_color(jukeoroni.layout_radio.bg_color)

        context['buttons'] = list()

        stations = Station.objects.all().order_by('display_name')
        context['stations'] = list(stations)

        if jukeoroni.radio.is_on_air:
            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': 'Stop',
                    'onclick': 'window.location.href = \'stop\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Stop"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        else:
            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': 'Back',
                    'onclick': 'window.location.href = \'/jukeoroni/set_standby\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Menu"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        last_played = jukeoroni.radio.last_played
        if last_played is None or jukeoroni.radio.is_on_air:
            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': 'Next (Random)',
                    'onclick': 'window.location.href = \'random/play\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Next"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        else:
            context['buttons'].append(
                {
                    'class': 'btn_header',
                    'column_width': COLUMN_WIDTH,
                    'padding': padding,

                    'button_title': f'Last played ({last_played.display_name})',
                    'onclick': f'window.location.href = \'{last_played.display_name_short}/play\'',
                    'img_width': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_height': int(Settings.BUTTONS_HEIGHT * BUTTON_ICON_SIZE_FACTOR),
                    'img_src': f'/jukeoroni/buttons_overlay/{os.path.basename(Settings.BUTTONS_ICONS["Play"])}',

                    'button_height': BUTTON_HEIGHT,
                }
            )

        context['buttons'].append(
            {
                # 'class': 'btn_header',
                'column_width': COLUMN_WIDTH,
                'padding': padding,

                'button_title': '',
                'onclick': '',
                'img_width': None,
                'img_height': None,
                'img_src': f'',

                'button_height': BUTTON_HEIGHT,
            }
        )

        context['buttons'].append(
            {
                # 'class': 'btn_header',
                'column_width': COLUMN_WIDTH,
                'padding': padding,

                'button_title': '',
                'onclick': '',
                'img_width': None,
                'img_height': None,
                'img_src': f'',

                'button_height': BUTTON_HEIGHT,
            }
        )

        img = jukeoroni.layout_radio.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.radio.cover,
                                                title=jukeoroni.radio.stream_title, buttons=False)
        context['encoded_img_data'] = encoded_screen(img)
        context['encoded_img_data_class'] = 'box_image'

        # context['stations'] = dict()

        context['channels_stationed'] = list()
        if bool(stations):
            # ret += '<center><h1>Channels</h1></center>\n'
            # if bool(stations):
            for station in stations:

                station_dict = {str(station.display_name): list()}

                channels = Channel.objects.filter(station=station).order_by('display_name')
                # context['channels'] = channels
                # if channels:
                #     ret += f'<center><h2>{station.display_name}</h2></center>\n'
                for channel in channels:
                    if channel.is_enabled:
                        if channel == jukeoroni.radio.is_on_air:
                            # context['channels'].append(
                            station_dict[str(station.display_name)].append(
                                {
                                    'class': 'btn_channel_on_air',
                                    'channel': channel,
                                    'onclick': f'window.location.href = \'stop\'',

                                    # 'style': '\"width:100%; background-color:green; \"',
                                }
                            )

                        else:
                            # context['channels'].append(
                            station_dict[str(station.display_name)].append(
                                {
                                    'class': 'btn_channel_default',
                                    'channel': channel,
                                    'onclick': f'window.location.href = \'{channel.display_name_short}/play\'',
                                    # 'style': '\"width:100%\"',
                                }
                            )

                context['channels_stationed'].append(station_dict.copy())

        # in case the channel has no station assigned
        channels_unstationed = Channel.objects.filter(station=None).order_by('display_name')
        context['channels_unstationed'] = list()
        # if channels_unstationed:
        #     ret += f'<center><h2>Uncategorized</h2></center>\n'
        for channel_unstationed in channels_unstationed:
            if channel_unstationed.is_enabled:
                if channel_unstationed == jukeoroni.radio.is_on_air:

                    context['channels_unstationed'].append(
                        {
                            'class': 'btn_channel_on_air',
                            'channel_unstationed': channel_unstationed,
                            'onclick': f'window.location.href = \'stop\'',
                            # 'style': '\"width:100%; background-color:green; \"',
                        }
                    )

                else:

                    context['channels_unstationed'].append(
                        {
                            'class': 'btn_channel_default',
                            'channel_unstationed': channel_unstationed,
                            'onclick': f'window.location.href = \'{channel_unstationed.display_name_short}/play\'',
                        }
                    )

        return render(request=request, template_name='player/box_radio.html', context=context)

    def radio_play(self, display_name_short):
        global jukeoroni

        if not jukeoroni.mode == Settings.MODES['radio']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['radio']['on_air']['random']:
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

        jukeoroni.mode = Settings.MODES['radio']['on_air']['random']

        # time_out = 10.0
        while not jukeoroni.radio.is_on_air == channel:  # or time_out <= 0.0:
            time.sleep(0.1)
            # time_out -= 0.1

        return HttpResponseRedirect('/jukeoroni')

    def radio_stop(self):
        global jukeoroni

        if not jukeoroni.mode == Settings.MODES['radio']['standby']['random'] \
                and not jukeoroni.mode == Settings.MODES['radio']['on_air']['random']:
            return HttpResponseRedirect('/jukeoroni')

        jukeoroni.mode = Settings.MODES['radio']['standby']['random']

        # time_out = 10.0
        while jukeoroni.radio.is_on_air is not None:  # or time_out <= 0.0:
            time.sleep(0.1)
            # time_out -= 0.1

        return HttpResponseRedirect('/jukeoroni')


def vol_up(request):
    m = alsaaudio.Mixer('Digital')

    vol = m.getvolume()[0]
    m.setvolume(vol + 1)

    new_vol = m.getvolume()[0]

    response = {'new_vol': new_vol}

    return JsonResponse(response, status=200)


def vol_reset(request):
    m = alsaaudio.Mixer('Digital')

    m.setvolume(90)

    new_vol = m.getvolume()[0]

    response = {'new_vol': new_vol}

    return JsonResponse(response, status=200)


def vol_down(request):
    m = alsaaudio.Mixer('Digital')

    vol = m.getvolume()[0]
    m.setvolume(vol - 1)

    new_vol = m.getvolume()[0]

    response = {'new_vol': new_vol}

    return JsonResponse(response, status=200)


# ['00. 31 Hz', '01. 63 Hz', '02. 125 Hz', '03. 250 Hz', '04. 500 Hz', '05. 1 kHz', '06. 2 kHz', '07. 4 kHz', '08. 8 kHz', '09. 16 kHz']

# 31 Hz
def up_31hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[0], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_31hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[0], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_31hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[0], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)
# 63 Hz
def up_63hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[1], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_63hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[1], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_63hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[1], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)
# 125 Hz
def up_125hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[2], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_125hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[2], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_125hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[2], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)
# 250 Hz
def up_250hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[3], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_250hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[3], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_250hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[3], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)
# 500 Hz
def up_500hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[4], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_500hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[4], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_500hz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[4], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)
# 1 kHz
def up_1khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[5], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_1khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[5], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_1khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[5], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)
# 2 kHz
def up_2khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[6], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_2khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[6], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_2khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[6], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)

# 4 kHz
def up_4khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[7], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_4khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[7], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_4khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[7], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)
# 8 kHz
def up_8khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[8], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_8khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[8], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_8khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[8], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)
# 16 kHz
def up_16khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[9], device='equal')
    vol = max(m.getvolume())
    m.setvolume(min([vol + 3, 100]))
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def reset_16khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[9], device='equal')
    # m = alsaaudio.Mixer('06. 2 kHz', device='equal')
    m.setvolume(66)
    new_vol = max(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def down_16khz(request):
    _m = alsaaudio.mixers(device='equal')
    m = alsaaudio.Mixer(_m[9], device='equal')
    vol = min(m.getvolume())
    m.setvolume(max([vol - 3, 0]))
    new_vol = min(m.getvolume())
    response = {'new_vol': new_vol}
    return JsonResponse(response, status=200)


def display_lyrics(request):


    return
