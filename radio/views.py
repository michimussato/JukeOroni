from django.http import HttpResponse, HttpResponseRedirect
import subprocess
import threading
import requests
import logging
from inky.inky_uc8159 import Inky, CLEAN
import signal
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont

from .models import Channel

import os


PIMORONI_SATURATION = 1.0
FONT_SIZE = 12
SLEEP_IMAGE = '/data/django/jukeoroni/player/static/zzz.jpg'
LOADING_IMAGE = '/data/django/jukeoroni/player/static/loading.jpg'
STANDARD_COVER = '/data/django/jukeoroni/player/static/cover_std.png'
PIMORONI_FONT = '/data/django/jukeoroni/player/static/arial_narrow.ttf'


# Create your views here.
def index(request):
    channels = Channel.objects.all()

    ret = '<body>\n'
    ret += '  <html>\n'
    for channel in channels:
        if channel.is_enabled:
            # required to find out if and which channel is playing
            ps = subprocess.Popen(['ps -o cmd -p $(pidof mplayer) | grep -i {0}'.format(channel.url)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = ps.communicate()[0].decode('utf-8').replace('\n', '')
            if output != '':
                pid = subprocess.Popen(['pidof mplayer'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                pid_output = pid.communicate()[0].decode('utf-8').replace('\n', '')
                ret += '        <button style=\"width:100%; background-color:green; \" onclick=\"window.location.href = \'stop/{0}\';\">{1}</button>\n'.format(pid_output, channel.display_name)  # , channel.display_name)
            else:
                ret += '        <button style=\"width:100%\" onclick=\"window.location.href = \'{0}/play\';\">{1}</button>\n'.format(channel.display_name_short, channel.display_name)
    ret += '  </html>\n'
    ret += '</body>\n'
    return HttpResponse(ret)


def play(request, display_name_short):

    # pimoroni = Inky()

    pid = subprocess.Popen(['pidof mplayer'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pid_output = pid.communicate()[0].decode('utf-8').replace('\n', '')

    if pid_output != '':
        os.system('kill {0}'.format(pid_output))
    # channels = Channel.objects.all()
    channel = Channel.objects.get(display_name_short=display_name_short)
    subprocess.Popen(['mplayer', '-nogui', '-noconfig', 'all', '-novideo', '-nocache', '-playlist', channel.url])

    set_image(image_file=channel.url_logo, media_info=channel.display_name)

    return HttpResponseRedirect('/radio')


def stop(request, pid):
    os.system('kill {0}'.format(pid))
    set_image(image_file=None, media_info='')
    return HttpResponseRedirect('/radio')


def set_image(image_file, media_info):
    logging.debug('starting setting image task')
    thread = threading.Thread(target=task_pimoroni_set_image, kwargs={'image_file': image_file, 'media_info': media_info})
    thread.name = 'Set Image Thread'
    thread.daemon = False
    thread.start()
    # _pimoroni_thread = thread


def task_pimoroni_set_image(**kwargs):
    logging.debug('setting image...')
    # if kwargs['image_file'].startswith('http'):

    pimoroni = Inky()

    if kwargs['image_file'] is None:
        cover = STANDARD_COVER
    else:
        cover = kwargs['image_file']

    # if bool(kwargs['media_info']):
    # if False:
    text = kwargs.get('media_info')
    # else:
    #    text = ''

    # image = Image.open(kwargs['image_file'])
    # image = image.rotate(90, expand=True)
    # image_resized = image.resize(self.PIMORONI_SIZE, Image.ANTIALIAS)
    # self.pimoroni.set_image(image_resized, saturation=self.PIMORONI_SATURATION)
    # self.pimoroni.show()

    bg = Image.new(mode='RGBA', size=(600, 448), color=(0, 0, 0, 255))
    # bg_w, bg_h = bg.size
    if cover.startswith('http'):
        cover = Image.open(requests.get(cover, stream=True).raw)
    else:
        cover = Image.open(cover, 'r')

    w, h = cover.size
    if w == h:
        cover = cover.resize((448, 448), Image.ANTIALIAS)
    elif w > h:
        # TODO
        cover = cover.resize((448, 448), Image.ANTIALIAS)
    elif w < h:
        # TODO
        cover = cover.resize((448, 448), Image.ANTIALIAS)

    # offset = ((bg_w - w) // 2, (bg_h - h) // 2)
    # bg.paste(cover, offset)

    offset = (0, 0)

    # img_font = ImageFont.truetype('FreeMono.ttf', 20)

    # print(bg.size)
    # bg = bg.rotate(90, expand=False)
    # print(bg.size)

    # img_draw.text

    ####### self.buttons_img_overlay(cover)

    # self.LABELS

    # buttons_img = Image.new(mode='RGB', size=(448, 12), color=(0, 0, 0))
    # buttons_draw = ImageDraw.Draw(buttons_img)
    # buttons_draw.text((0, 0), '       Quit               Play               Next               Stop', fill=(255, 255, 255))
    # # buttons_img = buttons_img.rotate(90, expand=False)
    # cover.paste(buttons_img, (0, 0))

    cover = cover.rotate(90, expand=True)
    # bg.paste(cover, offset)

    text_img = Image.new(mode='RGB', size=(448, 448), color=(0, 0, 0))
    img_draw = ImageDraw.Draw(text_img)

    font_path = PIMORONI_FONT
    font = ImageFont.truetype(font_path, FONT_SIZE)
    # print(kwargs['media_info'])
    # img_draw.text((10, 5), self.wrap_text(kwargs['media_info']['filename']), fill=(255, 255, 255, 255))
    # img_draw.text((10, 5), self.get_text(kwargs['media_info']), fill=(255, 255, 255))
    img_draw.text((10, 0), text, fill=(255, 255, 255), font=font)

    text_img = text_img.rotate(90, expand=False)

    bg.paste(text_img, (448, 0))

    bg.paste(cover, offset)

    pimoroni.set_image(bg, saturation=PIMORONI_SATURATION)
    pimoroni.show()
