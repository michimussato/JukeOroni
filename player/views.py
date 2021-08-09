import os
import requests
import time
import subprocess
import logging
import threading
from PIL import Image, ImageDraw, ImageFont
from inky.inky_uc8159 import Inky, CLEAN
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from player.displays import Player as PlayerLayout
import radio.models
from player.player import Player, BUTTON_4, BUTTON_3, BUTTON_2, BUTTON_1, _LOADING_IMAGE
from .models import Channel


PIMORONI_SATURATION = 1.0
FONT_SIZE = 24
SLEEP_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
STANDARD_COVER = '/data/django/jukeoroni/player/static/cover_std.png'
PIMORONI_FONT = '/data/django/jukeoroni/player/static/gotham-black.ttf'


player = Player()
player.buttons_watcher_thread()
player.state_watcher_thread()
player.pimoroni_watcher_thread()
player.track_loader_thread()
player.set_image()


# Create your views here.
class PlayerView(View):

    def get(self, request):
        global player

        ret = '<html>\n'
        ret += '  <head>\n'
        ret += '    <meta http-equiv="refresh" content="10" >\n'
        ret += '  </head>\n'
        ret += '  <body>\n'

        # else:

        if player.playing_track is None:
            ret += f'<div>{str(player.playing_track)}</div>'
        else:
            ret += f'<div>'
            ret += f'<img src=\"{str(player.playing_track.cover_album)}\" alt=\"{str(player.playing_track.path)}\">'
            ret += f'<img src=\"{str(player.playing_track.cover_artist)}\" alt=\"{str(player.playing_track.path)}\">'
            ret += f'</div>'
            ret += f'<div>Artist: {str(player.playing_track.artist)}</div>'
            ret += f'<div>Album: {str(player.playing_track.album)}</div>'
            ret += f'<div>Track: {str(player.playing_track.track)}</div>'
        if not player.tracks and bool(player.loading_process):
            ret += f'<div><img src=\"{_LOADING_IMAGE}\" alt=\"Loading...\"></div>'
        if player.button_3_value == BUTTON_3['Next']:
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/player/play\';\">Play</button>\n'
        elif player.button_3_value == BUTTON_3['Play']:
            ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/player/next\';\">Next</button>\n'
        ret += '    <button style=\"width:100%\" onclick=\"window.location.href = \'/player/stop\';\">Stop</button>\n'
        ret += '  </body>\n'
        ret += '</html>\n'
        return HttpResponse(ret)

        # global player
        # print(player.playing_track)
        # if player.playing_track is None:
        #     return HttpResponse(f'{str(player.playing_track)}')
        # else:
        #     return HttpResponse(f'{str(player.playing_track.path)}')

    def play(self):
        global player

        player.button_3_value = BUTTON_3['Play']
        # while player._playback_thread is None:
        #     time.sleep(1.0)
        return HttpResponseRedirect('/player')

    def next(self):
        global player
        if player._playback_thread is not None:
            player.next()
        return HttpResponseRedirect('/player')

    def stop(self):
        global player
        if player._playback_thread is not None:
            player.button_3_value = BUTTON_3['Next']
            player.stop()
            player.set_image()
        # button_3_value = self.player.button_3_value

        # player.button_3_value = BUTTON_3['Play']
        return HttpResponseRedirect('/player')


def radio_index(request):
    channels = Channel.objects.all()

    ret = '<html>\n'
    ret += '  <body>\n'
    for channel in channels:
        if channel.is_enabled:
            # required to find out if and which channel is playing
            ps = subprocess.Popen(['ps -o cmd -p $(pidof ffplay) | grep -i {0}'.format(channel.url)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = ps.communicate()[0].decode('utf-8').replace('\n', '')
            if output != '':
                pid = subprocess.Popen(['pidof ffplay'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                pid_output = pid.communicate()[0].decode('utf-8').replace('\n', '')
                ret += f'        <button style=\"width:100%; background-color:green; \" onclick=\"window.location.href = \'stop/{pid_output}\';\">{channel.display_name}</button>\n'  # , channel.display_name)
            else:
                ret += f'        <button style=\"width:100%\" onclick=\"window.location.href = \'{channel.display_name_short}/play\';\">{channel.display_name}</button>\n'
    ret += '  </body>\n'
    ret += '</html>\n'
    return HttpResponse(ret)


def radio_play(request, display_name_short):

    pid = subprocess.Popen(['pidof ffplay'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pid_output = pid.communicate()[0].decode('utf-8').replace('\n', '')

    try:
        for c in Channel.objects.filter(last_played=True):
            c.last_played = False
            c.save()
    except radio.models.Channel.DoesNotExist:
        pass

    if pid_output != '':
        os.system(f'kill {pid_output}')
    channel = Channel.objects.get(display_name_short=display_name_short)
    subprocess.Popen(['ffplay', '-hide_banner', '-autoexit', '-nodisp', '-vn', '-loglevel', 'quiet', channel.url])
    channel.last_played = True
    channel.save()

    set_image(image_file=channel.url_logo, media_info=channel.display_name)

    return HttpResponseRedirect('/player/radio')


def radio_stop(request, pid):
    os.system(f'kill {pid}')
    set_image(image_file=SLEEP_IMAGE, media_info='')
    return HttpResponseRedirect('/player/radio')


def set_image(image_file, media_info):
    logging.debug('ignoring setting image task')
    return
#     thread = threading.Thread(target=task_pimoroni_set_image, kwargs={'image_file': image_file, 'media_info': media_info})
#     thread.name = 'Set Image Thread'
#     thread.daemon = False
#     thread.start()
#
#
# def task_pimoroni_set_image(**kwargs):
#     pimoroni = Inky()
#
#     logging.debug('setting image...')
#
#     if kwargs['image_file'] is None:
#         cover = STANDARD_COVER
#     else:
#         cover = kwargs['image_file']
#
#     bg = PlayerLayout.get_layout(labels=['', '', '', ''], cover=cover)
#     """
#     File "/data/django/jukeoroni/player/views.py", line 100, in task_pimoroni_set_image
#       bg = PlayerLayout.get_layout(labels=['', '', '', ''], cover=cover)
#     TypeError: get_layout() missing 1 required positional argument: 'self'
#     """
#
#     pimoroni.set_image(bg, saturation=PIMORONI_SATURATION)
#     pimoroni.show()
