import binascii
import logging
import socket

import numpy as np
import scipy
import scipy.cluster
from PIL import Image, ImageDraw, ImageFont, ImageOps
from player.jukeoroni.clock import Clock
from player.jukeoroni.radar import Radar
from player.jukeoroni.settings import Settings
from player.jukeoroni.images import Resource


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


"""
https://stackoverflow.com/questions/5324647/how-to-merge-a-transparent-png-image-with-another-image-using-pil
https://github.com/python-pillow/Pillow/issues/924#issuecomment-61848826


paste
https://pillow.readthedocs.io/en/stable/reference/Image.html?highlight=composite#PIL.Image.Image.paste

>>> bg = Image.new("RGBA", (500, 500), (0,0,0,0))
>>> draw = ImageDraw.Draw(bg)
>>> draw.ellipse([(0,0),(200,200)], (255,0,0,128))
>>> fg = Image.new("RGBA", (500, 500), (0,0,0,0))
>>> draw_fg = ImageDraw.Draw(fg)
>>> draw_fg.ellipse([(100,100),(200,200)], (0,255,0,128))
>>> bg.paste(fg, (0,0), fg)
>>> bg.show()


alpha_composite
https://pillow.readthedocs.io/en/stable/reference/Image.html?highlight=composite#PIL.Image.alpha_composite

>>> bg = Image.new("RGBA", (500, 500), (0,0,0,0))
>>> draw_bg = ImageDraw.Draw(bg)
>>> draw_bg.ellipse([(0,0),(200,200)], (255,0,0,128))
>>> fg = Image.new("RGBA", (500, 500), (0,0,0,0))
>>> draw_fg = ImageDraw.Draw(fg)
>>> draw_fg.ellipse([(100,100),(200,200)], (0,255,0,128))
>>> comp = Image.new('RGBA', bg.size)
>>> comp = Image.alpha_composite(comp, bg)
>>> comp = Image.alpha_composite(comp, fg)
>>> comp.show()

3 layers (bg, layer1, layer2)

>>> bg = Image.new("RGBA", (500, 500), (255,255,255,255))
>>> layer1 = Image.new("RGBA", (500, 500), (255,255,255,0))
>>> draw_layer1 = ImageDraw.Draw(layer1)
>>> draw_layer1.ellipse([(0,0),(200,200)], (255,0,0,128))
>>> layer2 = Image.new("RGBA", (500, 500), (0,0,0,0))
>>> draw_layer2 = ImageDraw.Draw(layer2)
>>> draw_layer2.ellipse([(100,100),(200,200)], (0,255,0,128))
>>> comp = Image.new('RGBA', bg.size)
>>> comp = Image.alpha_composite(comp, bg)
>>> comp = Image.alpha_composite(comp, layer1)
>>> comp = Image.alpha_composite(comp, layer2)
>>> comp.show()
"""


def mean_color(img):
    NUM_CLUSTERS = 5  # the higher the name the more accurate is the dominant color

    im = img
    im = im.resize((50, 50))  # optional, to reduce time
    ar = np.asarray(im)
    shape = ar.shape
    ar = ar.reshape(np.product(shape[:2]), shape[2]).astype(float)

    codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)

    vecs, dist = scipy.cluster.vq.vq(ar, codes)  # assign codes
    counts, bins = np.histogram(vecs, len(codes))  # count occurrences

    LOG.debug(f'Color counts: {counts}')

    # TODO: pick most dominant color but make sure it is not close to black
    index_max = np.argmax(counts)  # find most frequent
    LOG.debug(f'Color max count: {index_max} ({counts[index_max]})')
    peak = codes[index_max]
    colour = binascii.hexlify(bytearray(int(c) for c in peak)).decode('ascii')  # actual colour, (in HEX)
    rgb = tuple(int(colour[i:i+2], 16) for i in (0, 2, 4))
    LOG.info(f'Dominant color out of {NUM_CLUSTERS} is {rgb} ({colour})')
    return rgb


def buttons_img_overlay(labels, gradient_color):

    # gradient_color = gradient_color or (255, 255, 255)

    # widget_buttons = Image.new(mode='RGBA', size=(448, 448), color=(0, 0, 0, 180))
    widget_buttons = Image.new(mode='RGBA', size=(448, 448), color=(0, 0, 0, 0))

    # invert = True
    n = 0
    for _label in labels[::-1]:
        n += 1
        if not bool(Settings.BUTTONS_ICONS[_label]):
            continue
        label = Image.open(Settings.BUTTONS_ICONS[_label])
        if Settings.INVERT_BUTTONS:
            r, g, b, a = label.split()
            rgb_image = Image.merge('RGB', (r, g, b))
            inverted_image = ImageOps.invert(rgb_image)
            r2, g2, b2 = inverted_image.split()
            label = Image.merge('RGBA', (r2, g2, b2, a))

        label = label.resize((Settings.BUTTONS_HEIGHT, Settings.BUTTONS_HEIGHT))
        label_bg = Image.new(mode='RGBA', size=widget_buttons.size, color=(0, 0, 0, 0))

        label_bg.paste(im=label, box=(int(round(n*448/4 - 448/4/2 - Settings.BUTTONS_HEIGHT/2)), Settings.BORDER))

        widget_buttons = Image.alpha_composite(widget_buttons, label_bg)

    comp_buttons = Image.new(mode='RGBA', size=widget_buttons.size)

    if Settings.GRADIENT_BUTTONS:
        # create gradient
        # https://stackoverflow.com/questions/39976028/python-pillow-make-gradient-for-transparency
        # Change the bg color of the gradient background here
        bg_color = gradient_color
        initial_opacity = 0.8

        height = comp_buttons.size[1]
        # gradient = 12.0
        gradient = height / (Settings.BUTTONS_HEIGHT + Settings.BORDER*2)
        alpha_gradient = Image.new('L', (1, height), color=255)
        for x in range(height):
            a = int((initial_opacity * 255.0) * (1.0 - gradient * float(x) / height))
            if a > 0:
                alpha_gradient.putpixel((0, x), a)
            else:
                alpha_gradient.putpixel((0, x), 0)
        alpha = alpha_gradient.resize(comp_buttons.size)
        black_im = Image.new('RGBA', comp_buttons.size, color=bg_color)
        black_im.putalpha(alpha)

        comp_buttons.paste(black_im)

    comp_buttons = Image.alpha_composite(comp_buttons, widget_buttons)
    comp_buttons = comp_buttons.rotate(90, expand=False)
    comp_buttons = comp_buttons.crop((0, 0, Settings.BUTTONS_HEIGHT + Settings.BORDER*2, widget_buttons.size[0]))

    return comp_buttons


def host_info():
    # host info
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = 'N/A'
    finally:
        s.close()

    hostname = socket.gethostname()

    host_info = f'{str(hostname)} ({str(ip)})'

    return host_info


class Layout:
    _clock = Clock()
    radar = Radar()
    border = Settings.BORDER
    main_size = 420 - 2*Settings.BORDER - Settings.BUTTONS_HEIGHT
    bg_color = (0, 0, 0, 255)


class Standby(Layout):
    # bg_color = (255, 0, 0, 255)

    def get_layout(self, labels, buttons=True):

        mc = (255, 255, 255)
        buttons_overlay = buttons_img_overlay(labels=labels, gradient_color=mc)
        bg = Image.new(mode='RGBA', size=(600, 448), color=self.bg_color)

        if Settings.GRADIENT_BG:
            # create gradient
            # https://stackoverflow.com/questions/39976028/python-pillow-make-gradient-for-transparency
            # Change the bg color of the gradient background here
            bg_gradient = Image.new(mode='RGBA', size=bg.size, color=self.bg_color)
            bg_gradient.putalpha(0)
            bg_color = mc

            width = bg_gradient.size[0]
            alpha_gradient = Image.new('L', (width, 1), color=255)
            for x in range(width):  # [0, 1,2,...599]
                if x < Settings.GRADIENT_BG_BLACK_SIZE:
                    a = 0.0
                else:
                    a = (x - Settings.GRADIENT_BG_BLACK_SIZE) / (width - Settings.GRADIENT_BG_BLACK_SIZE) * 255 * Settings.GRADIENT_BG_OPACITY
                alpha_gradient.putpixel((x, 0), int(a))

            alpha = alpha_gradient.resize(bg_gradient.size)
            black_im = Image.new('RGBA', bg_gradient.size, color=bg_color)
            black_im.putalpha(alpha)

            bg_gradient.paste(black_im)

            bg = Image.alpha_composite(bg, bg_gradient)

        widget_clock = Image.new(mode='RGBA', size=(self.main_size, self.main_size), color=(0, 0, 0, 0))
        comp_clock = Image.new(mode='RGBA', size=widget_clock.size)

        clock_size = self.main_size
        _clock = self._clock.get_clock(size=clock_size, draw_logo=True, draw_moon=True, draw_moon_phase=True, draw_date=True, hours=24, draw_sun=True)

        comp_clock = Image.alpha_composite(comp_clock, widget_clock)
        comp_clock = Image.alpha_composite(comp_clock, _clock)

        _clock_center = round(bg.size[1]/2 - clock_size/2)
        # _clock_right = 0_radar_image.size is
        # _clock_left = bg.size[1] - clock_size

        bg.paste(comp_clock, box=(buttons_overlay.size[0] + self.border, _clock_center), mask=comp_clock)

        _radar_image = self.radar.radar_image

        if _radar_image is not None:
            _radar_image = Resource().round_resize(image=_radar_image, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
            LOG.info(f'_radar_image.size is {str(_radar_image.size)}')

            _radar_bottom_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                      int(448 / 2 + round(self.border / 2) - round(Settings.SMALL_WIDGET_SIZE / 2)))

            _radar_bottom_right_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                            int(0 + 224 / 2 + round(self.border / 2) - round(Settings.SMALL_WIDGET_SIZE / 2)))

            # _radar_bottom_right = (int(600-w-self.border), self.border)
            bg.paste(_radar_image, _radar_bottom_centered, mask=_radar_image)

        if buttons:
            bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        if Settings.DRAW_HOST_INFO:
            _host_info = host_info()

            font_size = 16
            font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', size=font_size)
            length = font.getlength(_host_info)

            widget_ip_overlay = Image.new(mode='RGBA', size=bg.size, color=(0, 0, 0, 0))
            draw_ip = ImageDraw.Draw(widget_ip_overlay, mode='RGBA')

            draw_ip.text((round(widget_ip_overlay.size[0] - length - Settings.BORDER), 0), _host_info, fill=(255, 255, 255, 255),
                         font=font)

            bg = Image.alpha_composite(bg, widget_ip_overlay)

        return bg


class Jukebox(Layout):
    # bg_color = (0, 255, 0, 255)

    # TODO!!!
    #  If the default image gets currupted, playback won't work anymore!!

    def get_layout(self, labels, loading=False, cover=None, artist=None, buttons=True):

        if loading:
            # TODO:
            #  cover = Resource().squareify(Resource().JUKEBOX_LOADING_IMAGE)
            cover = Resource().JUKEBOX_LOADING_IMAGE

        else:
            if cover is None:
                # TODO change RADIO_ICON_IMAGE
                cover = Resource().JUKEBOX_ICON_IMAGE
            else:
                assert isinstance(cover, Image.Image), f'album cover type must be PIL.Image.Image() (not rotated): {cover}'
            if artist is None:
                pass
            else:
                assert isinstance(artist, Image.Image), 'artist cover type must be PIL.Image.Image() (not rotated)'

        mc = mean_color(cover)

        buttons_overlay = buttons_img_overlay(labels, gradient_color=mc)
        bg = Image.new(mode='RGBA', size=(600, 448), color=self.bg_color)

        if Settings.GRADIENT_BG:
            # create gradient
            # https://stackoverflow.com/questions/39976028/python-pillow-make-gradient-for-transparency
            # Change the bg color of the gradient background here
            bg_gradient = Image.new(mode='RGBA', size=bg.size, color=self.bg_color)
            bg_gradient.putalpha(0)
            bg_color = mc

            width = bg_gradient.size[0]
            alpha_gradient = Image.new('L', (width, 1), color=255)
            for x in range(width):  # [0, 1,2,...599]
                if x < Settings.GRADIENT_BG_BLACK_SIZE:
                    a = 0.0
                else:
                    a = (x - Settings.GRADIENT_BG_BLACK_SIZE) / (width - Settings.GRADIENT_BG_BLACK_SIZE) * 255 * Settings.GRADIENT_BG_OPACITY
                alpha_gradient.putpixel((x, 0), int(a))

            alpha = alpha_gradient.resize(bg_gradient.size)
            black_im = Image.new('RGBA', bg_gradient.size, color=bg_color)
            black_im.putalpha(alpha)

            bg_gradient.paste(black_im)

            bg = Image.alpha_composite(bg, bg_gradient)

        cover_size = self.main_size

        cover.putalpha(255)
        cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
        # TODO: corrupts PIL.Image

        cover = cover.rotate(90, expand=True)

        cover = Resource().round_resize(image=cover, corner=40, factor=1.0)

        if artist:
            scale_cover_artist = 4
            cover_artist = artist.rotate(90, expand=True)
            # TODO move to rounde_resize
            cover_artist = cover_artist.resize((round(cover_size/scale_cover_artist), round(cover_size/scale_cover_artist)), Image.ANTIALIAS)
            cover_artist = Resource().round_resize(image=cover_artist, corner=20, factor=1.0)

            cover_copy = cover.copy()

            cover.paste(cover_artist, box=(round(cover_size - cover_size/scale_cover_artist)-20, 20), mask=cover_artist)
            cover = Image.alpha_composite(cover_copy, cover)  # this is necessary to prevent alpha AA artifacts (background shining through)

        _cover_center = round(bg.size[1] / 2 - cover_size / 2)
        bg.paste(cover, box=(buttons_overlay.size[0] + self.border, _cover_center), mask=cover)

        # SMALL_WIDGET_SIZE = 151
        _clock = self._clock.get_clock(size=Settings.SMALL_WIDGET_SIZE, draw_logo=False, draw_moon_phase=True, draw_moon=True, draw_date=False, hours=24, draw_sun=True, square=True)
        _clock = Resource().round_resize(image=_clock, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
        _clock_bottom_left_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                       int(224 + 224/2 + round(self.border/2) - round(Settings.SMALL_WIDGET_SIZE/2)))
        _clock_bottom_left = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                              int(448 - Settings.SMALL_WIDGET_SIZE - self.border))

        bg.paste(_clock, box=_clock_bottom_left_centered, mask=_clock)

        _radar_image = self.radar.radar_image

        if _radar_image is not None:
            _radar_image = Resource().round_resize(image=_radar_image, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
            LOG.info(f'_radar_image.size is {str(_radar_image.size)}')
            # _radar_bottom_right = (int(600 - w - self.border), self.border)
            _radar_bottom_right_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                            int(0 + 224 / 2 + round(self.border / 2) - round(Settings.SMALL_WIDGET_SIZE / 2)))
            bg.paste(_radar_image, box=_radar_bottom_right_centered, mask=_radar_image)

        if buttons:
            bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        if Settings.DRAW_HOST_INFO:

            _host_info = host_info()

            font_size = 16
            font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', size=font_size)
            length = font.getlength(_host_info)

            widget_ip_overlay = Image.new(mode='RGBA', size=bg.size, color=(0, 0, 0, 0))
            draw_ip = ImageDraw.Draw(widget_ip_overlay, mode='RGBA')

            draw_ip.text((round(widget_ip_overlay.size[0] - length - Settings.BORDER), 0), _host_info, fill=(255, 255, 255, 255), font=font)

            bg = Image.alpha_composite(bg, widget_ip_overlay)

        return bg


class Radio(Layout):

    def get_layout(self, labels, cover, title, buttons=True):

        assert isinstance(cover, Image.Image), f'Radio Channel cover type must be PIL.Image.Image() (not rotated). Got: {cover}'

        mc = mean_color(cover)

        buttons_overlay = buttons_img_overlay(labels, gradient_color=mc)
        bg = Image.new(mode='RGBA', size=(600, 448), color=self.bg_color)

        if Settings.GRADIENT_BG:
            # create gradient
            # https://stackoverflow.com/questions/39976028/python-pillow-make-gradient-for-transparency
            # Change the bg color of the gradient background here
            bg_gradient = Image.new(mode='RGBA', size=bg.size, color=self.bg_color)
            bg_gradient.putalpha(0)
            bg_color = mc

            width = bg_gradient.size[0]
            alpha_gradient = Image.new('L', (width, 1), color=255)
            for x in range(width):  # [0, 1,2,...599]
                if x < Settings.GRADIENT_BG_BLACK_SIZE:
                    a = 0.0
                else:
                    a = (x - Settings.GRADIENT_BG_BLACK_SIZE) / (width - Settings.GRADIENT_BG_BLACK_SIZE) * 255 * Settings.GRADIENT_BG_OPACITY
                alpha_gradient.putpixel((x, 0), int(a))

            alpha = alpha_gradient.resize(bg_gradient.size)
            black_im = Image.new('RGBA', bg_gradient.size, color=bg_color)
            black_im.putalpha(alpha)

            bg_gradient.paste(black_im)

            bg = Image.alpha_composite(bg, bg_gradient)

        cover_size = self.main_size

        cover.putalpha(255)
        cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)

        if title is not None:
            font_size = 24
            border = 10
            border_bottom = 20

            font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', size=font_size)
            length = font.getlength(title)

            widget_stream_title = Image.new(mode='RGBA', size=cover.size, color=(0, 0, 0, 0))

            draw_stream_title = ImageDraw.Draw(widget_stream_title, mode='RGBA')
            draw_stream_title.rounded_rectangle([(round(cover.size[0]/2 - length/2) - border, round(cover.size[1] - (font_size + border)) - border - border_bottom), (round(cover.size[0]/2 + length/2) + border, round(cover.size[1] - border) + border - border_bottom)], radius=15, fill=(0, 0, 0, 180))

            draw_stream_title.text((int(round(cover.size[0]/2 - length/2)), cover.size[1] - (font_size + border) - border_bottom), title, fill=(255, 255, 255, 255), font=font)

            cover = Image.alpha_composite(cover, widget_stream_title)

        cover = cover.rotate(90, expand=True)

        cover = Resource().round_resize(image=cover, corner=40, factor=1.0)

        _cover_center = round(bg.size[1] / 2 - cover_size / 2)
        bg.paste(cover, box=(buttons_overlay.size[0] + self.border, _cover_center), mask=cover)

        # SMALL_WIDGET_SIZE = 151
        _clock = self._clock.get_clock(size=Settings.SMALL_WIDGET_SIZE, draw_logo=False, draw_moon=True, draw_moon_phase=True, draw_date=False, hours=24, draw_sun=True, square=True)
        _clock = Resource().round_resize(image=_clock, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
        _clock_bottom_left_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                       int(224 + 224/2 + round(self.border/2) - round(Settings.SMALL_WIDGET_SIZE/2)))
        _clock_bottom_left = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                              int(448 - Settings.SMALL_WIDGET_SIZE - self.border))

        bg.paste(_clock, box=_clock_bottom_left_centered, mask=_clock)

        _radar_image = self.radar.radar_image

        if _radar_image is not None:
            _radar_image = Resource().round_resize(image=_radar_image, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
            LOG.info(f'_radar_image.size is {str(_radar_image.size)}')

            _radar_bottom_right_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                            int(0 + 224 / 2 + round(self.border / 2) - round(Settings.SMALL_WIDGET_SIZE / 2)))

            # _radar_bottom_right = (int(600 - w - self.border), self.border)
            bg.paste(_radar_image, box=_radar_bottom_right_centered, mask=_radar_image)

        if buttons:
            bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        if Settings.DRAW_HOST_INFO:
            _host_info = host_info()

            font_size = 16
            font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', size=font_size)
            length = font.getlength(_host_info)

            widget_ip_overlay = Image.new(mode='RGBA', size=bg.size, color=(0, 0, 0, 0))
            draw_ip = ImageDraw.Draw(widget_ip_overlay, mode='RGBA')

            draw_ip.text((round(widget_ip_overlay.size[0] - length - Settings.BORDER), 0), _host_info, fill=(255, 255, 255, 255),
                         font=font)

            bg = Image.alpha_composite(bg, widget_ip_overlay)

        return bg


# class Off(Layout):
#     # bg_color = (0, 0, 0, 255)
#
#     # _clock = None
#     # radar = None
#
#     def get_layout(self, labels, cover):
#
#         assert isinstance(cover, Image.Image), f'Radio Channel cover type must be PIL.Image.Image() (not rotated). Got: {cover}'
#
#         buttons_overlay = buttons_img_overlay(labels)
#         bg = Image.new(mode='RGBA', size=(600, 448), color=self.bg_color)
#
#         # cover_size = 448 - 2 * self.border
#         cover_size = self.main_size
#
#         cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
#
#         cover = cover.rotate(90, expand=True)
#
#         cover = Resource().round_resize(image=cover, corner=40, factor=1.0)
#
#         _cover_center = round(bg.size[1] / 2 - cover_size / 2)
#         bg.paste(cover, box=(buttons_overlay.size[0] + self.border, _cover_center), mask=cover)
#
#         bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)
#
#         return bg


class Meditationbox(Layout):
    # bg_color = (0, 0, 255, 255)

    # def get_layout(self, labels, cover, title):
        # raise NotImplementedError

# class Jukebox(Layout):
    # bg_color = (0, 255, 0, 255)

    # TODO!!!
    #  If the default image gets currupted, playback won't work anymore!!

    def get_layout(self, labels, loading=False, cover=None, artist=None, buttons=True):

        if loading:
            # TODO:
            #  cover = Resource().squareify(Resource().JUKEBOX_LOADING_IMAGE)
            cover = Resource().JUKEBOX_LOADING_IMAGE

        else:
            if cover is None:
                # TODO change RADIO_ICON_IMAGE
                cover = Resource().MEDITATION_ICON_IMAGE
            else:
                assert isinstance(cover,
                                  Image.Image), f'album cover type must be PIL.Image.Image() (not rotated): {cover}'
            if artist is None:
                pass
            else:
                assert isinstance(artist, Image.Image), 'artist cover type must be PIL.Image.Image() (not rotated)'

        mc = mean_color(cover)

        buttons_overlay = buttons_img_overlay(labels, gradient_color=mc)
        bg = Image.new(mode='RGBA', size=(600, 448), color=self.bg_color)

        if Settings.GRADIENT_BG:
            # create gradient
            # https://stackoverflow.com/questions/39976028/python-pillow-make-gradient-for-transparency
            # Change the bg color of the gradient background here
            bg_gradient = Image.new(mode='RGBA', size=bg.size, color=self.bg_color)
            bg_gradient.putalpha(0)
            bg_color = mc

            width = bg_gradient.size[0]
            alpha_gradient = Image.new('L', (width, 1), color=255)
            for x in range(width):  # [0, 1,2,...599]
                if x < Settings.GRADIENT_BG_BLACK_SIZE:
                    a = 0.0
                else:
                    a = (x - Settings.GRADIENT_BG_BLACK_SIZE) / (width - Settings.GRADIENT_BG_BLACK_SIZE) * 255 * Settings.GRADIENT_BG_OPACITY
                alpha_gradient.putpixel((x, 0), int(a))

            alpha = alpha_gradient.resize(bg_gradient.size)
            black_im = Image.new('RGBA', bg_gradient.size, color=bg_color)
            black_im.putalpha(alpha)

            bg_gradient.paste(black_im)

            bg = Image.alpha_composite(bg, bg_gradient)

        cover_size = self.main_size

        cover.putalpha(255)
        cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
        # TODO: corrupts PIL.Image
        """
Environment:


Request Method: GET
Request URL: http://localhost/jukeoroni/jukebox/

Django Version: 3.2.5
Python Version: 3.7.3
Installed Applications:
['player.apps.PlayerConfig',
 'django.contrib.admin',
 'django.contrib.auth',
 'django.contrib.contenttypes',
 'django.contrib.sessions',
 'django.contrib.messages',
 'django.contrib.staticfiles']
Installed Middleware:
['django.middleware.security.SecurityMiddleware',
 'django.contrib.sessions.middleware.SessionMiddleware',
 'django.middleware.common.CommonMiddleware',
 'django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware',
 'django.contrib.messages.middleware.MessageMiddleware',
 'django.middleware.clickjacking.XFrameOptionsMiddleware']



Traceback (most recent call last):
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/exception.py", line 47, in inner
    response = get_response(request)
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/base.py", line 181, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/data/django/jukeoroni/player/views.py", line 148, in jukebox_index
    img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS)
  File "/data/django/jukeoroni/player/jukeoroni/displays.py", line 212, in get_layout
    cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
  File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 1978, in resize
    im = self.convert({"LA": "La", "RGBA": "RGBa"}[self.mode])
  File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 915, in convert
    self.load()
  File "/data/venv/lib/python3.7/site-packages/PIL/ImageFile.py", line 274, in load
    raise_oserror(err_code)
  File "/data/venv/lib/python3.7/site-packages/PIL/ImageFile.py", line 67, in raise_oserror
    raise OSError(message + " when reading image file")

Exception Type: OSError at /jukeoroni/jukebox/
Exception Value: unrecognized data stream contents when reading image file
        """

        """
Traceback (most recent call last):
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/exception.py", line 47, in inner
    response = get_response(request)
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/base.py", line 181, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/data/django/jukeoroni/player/views.py", line 147, in jukebox_index
    img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS)
  File "/data/django/jukeoroni/player/jukeoroni/displays.py", line 212, in get_layout
    cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
  File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 1978, in resize
    im = self.convert({"LA": "La", "RGBA": "RGBa"}[self.mode])
  File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 915, in convert
    self.load()
  File "/data/venv/lib/python3.7/site-packages/PIL/ImageFile.py", line 237, in load
    s = read(self.decodermaxblock)
  File "/data/venv/lib/python3.7/site-packages/PIL/PngImagePlugin.py", line 896, in load_read
    cid, pos, length = self.png.read()
  File "/data/venv/lib/python3.7/site-packages/PIL/PngImagePlugin.py", line 166, in read
    raise SyntaxError(f"broken PNG file (chunk {repr(cid)})")

Exception Type: SyntaxError at /jukeoroni/jukebox/
Exception Value: broken PNG file (chunk b"Em\xd5'")
        """

        cover = cover.rotate(90, expand=True)

        cover = Resource().round_resize(image=cover, corner=40, factor=1.0)

        if artist:
            scale_cover_artist = 4
            cover_artist = artist.rotate(90, expand=True)
            # TODO move to rounde_resize
            cover_artist = cover_artist.resize(
                (round(cover_size / scale_cover_artist), round(cover_size / scale_cover_artist)), Image.ANTIALIAS)
            cover_artist = Resource().round_resize(image=cover_artist, corner=20, factor=1.0)

            cover_copy = cover.copy()

            cover.paste(cover_artist, box=(round(cover_size - cover_size / scale_cover_artist) - 20, 20),
                        mask=cover_artist)
            cover = Image.alpha_composite(cover_copy,
                                          cover)  # this is necessary to prevent alpha AA artifacts (background shining through)

        _cover_center = round(bg.size[1] / 2 - cover_size / 2)
        bg.paste(cover, box=(buttons_overlay.size[0] + self.border, _cover_center), mask=cover)

        # SMALL_WIDGET_SIZE = 151
        _clock = self._clock.get_clock(size=Settings.SMALL_WIDGET_SIZE, draw_logo=False, draw_moon_phase=True,
                                       draw_moon=True, draw_date=False, hours=24, draw_sun=True, square=True)
        _clock = Resource().round_resize(image=_clock, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
        _clock_bottom_left_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                       int(224 + 224 / 2 + round(self.border / 2) - round(Settings.SMALL_WIDGET_SIZE / 2)))
        _clock_bottom_left = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                              int(448 - Settings.SMALL_WIDGET_SIZE - self.border))

        bg.paste(_clock, box=_clock_bottom_left_centered, mask=_clock)

        _radar_image = self.radar.radar_image

        if _radar_image is not None:
            _radar_image = Resource().round_resize(image=_radar_image, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
            LOG.info(f'_radar_image.size is {str(_radar_image.size)}')
            # _radar_bottom_right = (int(600 - w - self.border), self.border)
            _radar_bottom_right_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                            int(0 + 224 / 2 + round(self.border / 2) - round(
                                                Settings.SMALL_WIDGET_SIZE / 2)))
            bg.paste(_radar_image, box=_radar_bottom_right_centered, mask=_radar_image)

        if buttons:
            bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        if Settings.DRAW_HOST_INFO:
            _host_info = host_info()

            font_size = 16
            font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', size=font_size)
            length = font.getlength(_host_info)

            widget_ip_overlay = Image.new(mode='RGBA', size=bg.size, color=(0, 0, 0, 0))
            draw_ip = ImageDraw.Draw(widget_ip_overlay, mode='RGBA')

            draw_ip.text((round(widget_ip_overlay.size[0] - length - Settings.BORDER), 0), _host_info,
                         fill=(255, 255, 255, 255), font=font)

            bg = Image.alpha_composite(bg, widget_ip_overlay)

        return bg


class Audiobookbox(Layout):
    # bg_color = (0, 0, 255, 255)

    # def get_layout(self, labels, cover, title):
        # raise NotImplementedError

# class Jukebox(Layout):
    # bg_color = (0, 255, 0, 255)

    # TODO!!!
    #  If the default image gets currupted, playback won't work anymore!!

    def get_layout(self, labels, loading=False, cover=None, artist=None, buttons=True):

        # if loading:
        #     # TODO:
        #     #  cover = Resource().squareify(Resource().JUKEBOX_LOADING_IMAGE)
        #     cover = Resource().JUKEBOX_LOADING_IMAGE
        #
        # else:
        #     if cover is None:
        #         # TODO change RADIO_ICON_IMAGE
        #         cover = Resource().AUDIOBOOK_ICON_IMAGE
        #     else:
        #         assert isinstance(cover,
        #                           Image.Image), f'album cover type must be PIL.Image.Image() (not rotated): {cover}'
        #     if artist is None:
        #         pass
        #     else:
        #         assert isinstance(artist, Image.Image), 'artist cover type must be PIL.Image.Image() (not rotated)'
        #

        mc = mean_color(cover)

        buttons_overlay = buttons_img_overlay(labels, gradient_color=mc)
        bg = Image.new(mode='RGBA', size=(600, 448), color=self.bg_color)

        if Settings.GRADIENT_BG:
            # create gradient
            # https://stackoverflow.com/questions/39976028/python-pillow-make-gradient-for-transparency
            # Change the bg color of the gradient background here
            bg_gradient = Image.new(mode='RGBA', size=bg.size, color=self.bg_color)
            bg_gradient.putalpha(0)
            bg_color = mc

            width = bg_gradient.size[0]
            alpha_gradient = Image.new('L', (width, 1), color=255)
            for x in range(width):  # [0, 1,2,...599]
                if x < Settings.GRADIENT_BG_BLACK_SIZE:
                    a = 0.0
                else:
                    a = (x - Settings.GRADIENT_BG_BLACK_SIZE) / (width - Settings.GRADIENT_BG_BLACK_SIZE) * 255 * Settings.GRADIENT_BG_OPACITY
                alpha_gradient.putpixel((x, 0), int(a))

            alpha = alpha_gradient.resize(bg_gradient.size)
            black_im = Image.new('RGBA', bg_gradient.size, color=bg_color)
            black_im.putalpha(alpha)

            bg_gradient.paste(black_im)

            bg = Image.alpha_composite(bg, bg_gradient)

        cover_size = self.main_size

        cover.putalpha(255)
        cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
        # TODO: corrupts PIL.Image
        """
Environment:


Request Method: GET
Request URL: http://localhost/jukeoroni/jukebox/

Django Version: 3.2.5
Python Version: 3.7.3
Installed Applications:
['player.apps.PlayerConfig',
 'django.contrib.admin',
 'django.contrib.auth',
 'django.contrib.contenttypes',
 'django.contrib.sessions',
 'django.contrib.messages',
 'django.contrib.staticfiles']
Installed Middleware:
['django.middleware.security.SecurityMiddleware',
 'django.contrib.sessions.middleware.SessionMiddleware',
 'django.middleware.common.CommonMiddleware',
 'django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware',
 'django.contrib.messages.middleware.MessageMiddleware',
 'django.middleware.clickjacking.XFrameOptionsMiddleware']



Traceback (most recent call last):
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/exception.py", line 47, in inner
    response = get_response(request)
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/base.py", line 181, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/data/django/jukeoroni/player/views.py", line 148, in jukebox_index
    img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS)
  File "/data/django/jukeoroni/player/jukeoroni/displays.py", line 212, in get_layout
    cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
  File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 1978, in resize
    im = self.convert({"LA": "La", "RGBA": "RGBa"}[self.mode])
  File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 915, in convert
    self.load()
  File "/data/venv/lib/python3.7/site-packages/PIL/ImageFile.py", line 274, in load
    raise_oserror(err_code)
  File "/data/venv/lib/python3.7/site-packages/PIL/ImageFile.py", line 67, in raise_oserror
    raise OSError(message + " when reading image file")

Exception Type: OSError at /jukeoroni/jukebox/
Exception Value: unrecognized data stream contents when reading image file
        """

        """
Traceback (most recent call last):
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/exception.py", line 47, in inner
    response = get_response(request)
  File "/data/venv/lib/python3.7/site-packages/django/core/handlers/base.py", line 181, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/data/django/jukeoroni/player/views.py", line 147, in jukebox_index
    img = jukeoroni.jukebox.layout.get_layout(labels=jukeoroni.LABELS)
  File "/data/django/jukeoroni/player/jukeoroni/displays.py", line 212, in get_layout
    cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
  File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 1978, in resize
    im = self.convert({"LA": "La", "RGBA": "RGBa"}[self.mode])
  File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 915, in convert
    self.load()
  File "/data/venv/lib/python3.7/site-packages/PIL/ImageFile.py", line 237, in load
    s = read(self.decodermaxblock)
  File "/data/venv/lib/python3.7/site-packages/PIL/PngImagePlugin.py", line 896, in load_read
    cid, pos, length = self.png.read()
  File "/data/venv/lib/python3.7/site-packages/PIL/PngImagePlugin.py", line 166, in read
    raise SyntaxError(f"broken PNG file (chunk {repr(cid)})")

Exception Type: SyntaxError at /jukeoroni/jukebox/
Exception Value: broken PNG file (chunk b"Em\xd5'")
        """

        cover = cover.rotate(90, expand=True)

        cover = Resource().round_resize(image=cover, corner=40, factor=1.0)

        if artist:
            scale_cover_artist = 4
            cover_artist = artist.rotate(90, expand=True)
            # TODO move to rounde_resize
            cover_artist = cover_artist.resize(
                (round(cover_size / scale_cover_artist), round(cover_size / scale_cover_artist)), Image.ANTIALIAS)
            cover_artist = Resource().round_resize(image=cover_artist, corner=20, factor=1.0)

            cover_copy = cover.copy()

            cover.paste(cover_artist, box=(round(cover_size - cover_size / scale_cover_artist) - 20, 20),
                        mask=cover_artist)
            cover = Image.alpha_composite(cover_copy,
                                          cover)  # this is necessary to prevent alpha AA artifacts (background shining through)

        _cover_center = round(bg.size[1] / 2 - cover_size / 2)
        bg.paste(cover, box=(buttons_overlay.size[0] + self.border, _cover_center), mask=cover)

        # SMALL_WIDGET_SIZE = 151
        _clock = self._clock.get_clock(size=Settings.SMALL_WIDGET_SIZE, draw_logo=False, draw_moon_phase=True,
                                       draw_moon=True, draw_date=False, hours=24, draw_sun=True, square=True)
        _clock = Resource().round_resize(image=_clock, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
        _clock_bottom_left_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                       int(224 + 224 / 2 + round(self.border / 2) - round(Settings.SMALL_WIDGET_SIZE / 2)))
        _clock_bottom_left = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                              int(448 - Settings.SMALL_WIDGET_SIZE - self.border))

        bg.paste(_clock, box=_clock_bottom_left_centered, mask=_clock)

        _radar_image = self.radar.radar_image

        if _radar_image is not None:
            _radar_image = Resource().round_resize(image=_radar_image, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
            LOG.info(f'_radar_image.size is {str(_radar_image.size)}')
            # _radar_bottom_right = (int(600 - w - self.border), self.border)
            _radar_bottom_right_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                            int(0 + 224 / 2 + round(self.border / 2) - round(
                                                Settings.SMALL_WIDGET_SIZE / 2)))
            bg.paste(_radar_image, box=_radar_bottom_right_centered, mask=_radar_image)

        if buttons:
            bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        if Settings.DRAW_HOST_INFO:
            _host_info = host_info()

            font_size = 16
            font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', size=font_size)
            length = font.getlength(_host_info)

            widget_ip_overlay = Image.new(mode='RGBA', size=bg.size, color=(0, 0, 0, 0))
            draw_ip = ImageDraw.Draw(widget_ip_overlay, mode='RGBA')

            draw_ip.text((round(widget_ip_overlay.size[0] - length - Settings.BORDER), 0), _host_info,
                         fill=(255, 255, 255, 255), font=font)

            bg = Image.alpha_composite(bg, widget_ip_overlay)

        return bg


class Podcastbox(Layout):
    # bg_color = (0, 0, 255, 255)

    # def get_layout(self, labels, cover, title):
        # raise NotImplementedError

# class Jukebox(Layout):
    # bg_color = (0, 255, 0, 255)

    # TODO!!!
    #  If the default image gets currupted, playback won't work anymore!!

    def get_layout(self, labels, loading=False, cover=None, artist=None, buttons=True):

        if loading:
            # TODO:
            #  cover = Resource().squareify(Resource().JUKEBOX_LOADING_IMAGE)
            cover = Resource().JUKEBOX_LOADING_IMAGE

        else:
            if cover is None:
                # TODO change RADIO_ICON_IMAGE
                cover = Resource().PODCAST_ICON_IMAGE
            else:
                assert isinstance(cover,
                                  Image.Image), f'album cover type must be PIL.Image.Image() (not rotated): {cover}'
            if artist is None:
                pass
            else:
                assert isinstance(artist, Image.Image), 'artist cover type must be PIL.Image.Image() (not rotated)'

        mc = mean_color(cover)

        buttons_overlay = buttons_img_overlay(labels, gradient_color=mc)
        bg = Image.new(mode='RGBA', size=(600, 448), color=self.bg_color)

        if Settings.GRADIENT_BG:
            # create gradient
            # https://stackoverflow.com/questions/39976028/python-pillow-make-gradient-for-transparency
            # Change the bg color of the gradient background here
            bg_gradient = Image.new(mode='RGBA', size=bg.size, color=self.bg_color)
            bg_gradient.putalpha(0)
            bg_color = mc

            width = bg_gradient.size[0]
            alpha_gradient = Image.new('L', (width, 1), color=255)
            for x in range(width):  # [0, 1,2,...599]
                if x < Settings.GRADIENT_BG_BLACK_SIZE:
                    a = 0.0
                else:
                    a = (x - Settings.GRADIENT_BG_BLACK_SIZE) / (width - Settings.GRADIENT_BG_BLACK_SIZE) * 255 * Settings.GRADIENT_BG_OPACITY
                alpha_gradient.putpixel((x, 0), int(a))

            alpha = alpha_gradient.resize(bg_gradient.size)
            black_im = Image.new('RGBA', bg_gradient.size, color=bg_color)
            black_im.putalpha(alpha)

            bg_gradient.paste(black_im)

            bg = Image.alpha_composite(bg, bg_gradient)

        cover_size = self.main_size

        cover.putalpha(255)
        cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
        # TODO: corrupts PIL.Image

        cover = cover.rotate(90, expand=True)

        cover = Resource().round_resize(image=cover, corner=40, factor=1.0)

        # if artist:
        #     scale_cover_artist = 4
        #     cover_artist = artist.rotate(90, expand=True)
        #     # TODO move to rounde_resize
        #     cover_artist = cover_artist.resize(
        #         (round(cover_size / scale_cover_artist), round(cover_size / scale_cover_artist)), Image.ANTIALIAS)
        #     cover_artist = Resource().round_resize(image=cover_artist, corner=20, factor=1.0)
        #
        #     cover_copy = cover.copy()
        #
        #     cover.paste(cover_artist, box=(round(cover_size - cover_size / scale_cover_artist) - 20, 20),
        #                 mask=cover_artist)
        #     cover = Image.alpha_composite(cover_copy,
        #                                   cover)  # this is necessary to prevent alpha AA artifacts (background shining through)

        _cover_center = round(bg.size[1] / 2 - cover_size / 2)
        bg.paste(cover, box=(buttons_overlay.size[0] + self.border, _cover_center), mask=cover)

        # SMALL_WIDGET_SIZE = 151
        _clock = self._clock.get_clock(size=Settings.SMALL_WIDGET_SIZE, draw_logo=False, draw_moon_phase=True,
                                       draw_moon=True, draw_date=False, hours=24, draw_sun=True, square=True)
        _clock = Resource().round_resize(image=_clock, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
        _clock_bottom_left_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                       int(224 + 224 / 2 + round(self.border / 2) - round(Settings.SMALL_WIDGET_SIZE / 2)))
        _clock_bottom_left = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                              int(448 - Settings.SMALL_WIDGET_SIZE - self.border))

        bg.paste(_clock, box=_clock_bottom_left_centered, mask=_clock)

        _radar_image = self.radar.radar_image

        if _radar_image is not None:
            _radar_image = Resource().round_resize(image=_radar_image, corner=40, fixed=Settings.SMALL_WIDGET_SIZE)
            LOG.info(f'_radar_image.size is {str(_radar_image.size)}')
            # _radar_bottom_right = (int(600 - w - self.border), self.border)
            _radar_bottom_right_centered = (int(600 - Settings.SMALL_WIDGET_SIZE - self.border),
                                            int(0 + 224 / 2 + round(self.border / 2) - round(
                                                Settings.SMALL_WIDGET_SIZE / 2)))
            bg.paste(_radar_image, box=_radar_bottom_right_centered, mask=_radar_image)

        if buttons:
            bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        if Settings.DRAW_HOST_INFO:
            _host_info = host_info()

            font_size = 16
            font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', size=font_size)
            length = font.getlength(_host_info)

            widget_ip_overlay = Image.new(mode='RGBA', size=bg.size, color=(0, 0, 0, 0))
            draw_ip = ImageDraw.Draw(widget_ip_overlay, mode='RGBA')

            draw_ip.text((round(widget_ip_overlay.size[0] - length - Settings.BORDER), 0), _host_info,
                         fill=(255, 255, 255, 255), font=font)

            bg = Image.alpha_composite(bg, widget_ip_overlay)

        return bg
