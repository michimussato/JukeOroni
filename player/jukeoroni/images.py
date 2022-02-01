from player.jukeoroni.settings import Settings  # (
#     _RADIO_ICON_IMAGE,
#     _RADIO_ON_AIR_DEFAULT_IMAGE,
#     _JUKEBOX_ON_AIR_DEFAULT_IMAGE,
#     _OFF_IMAGE,
#     _JUKEBOX_ICON_IMAGE,
#     _JUKEBOX_LOADING_IMAGE,
#     _MEDITATION_ICON_IMAGE,
#     _AUDIOBOOK_ICON_IMAGE,
#     _MOON_TEXUTRE,
#     GLOBAL_LOGGING_LEVEL,
# )
from player.jukeoroni.is_string_url import is_string_url
from PIL import Image, ImageDraw
import urllib.request
import io
import logging


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


class Resource(object):
    """
    from player.jukeoroni.images import Resource
    """

    @property
    def OFF_IMAGE(self):
        return Image.open(Settings._OFF_IMAGE)

    @property
    def DEFAULT_ALBUM_COVER(self):
        # TODO: add default album cover image
        return Image.open(Settings._OFF_IMAGE)

    @property
    def RADIO_ICON_IMAGE(self):
        return Image.open(Settings._RADIO_ICON_IMAGE)

    @property
    def RADIO_ON_AIR_DEFAULT_IMAGE(self):
        return Image.open(Settings._RADIO_ON_AIR_DEFAULT_IMAGE)

    @property
    def JUKEBOX_ICON_IMAGE(self):
        return Image.open(Settings._JUKEBOX_ICON_IMAGE)

    @property
    def JUKEBOX_LOADING_IMAGE(self):
        return Image.open(Settings._JUKEBOX_LOADING_IMAGE)

    @property
    def JUKEBOX_ON_AIR_DEFAULT_IMAGE(self):
        return Image.open(Settings._JUKEBOX_ON_AIR_DEFAULT_IMAGE)

    @property
    def MEDITATION_ICON_IMAGE(self):
        return Image.open(Settings._MEDITATION_ICON_IMAGE)

    @property
    def AUDIOBOOK_ICON_IMAGE(self):
        return Image.open(Settings._AUDIOBOOK_ICON_IMAGE)

    @property
    def MOON_TEXUTRE(self):
        return Image.open(Settings._MOON_TEXUTRE)

    @property
    def PLACEHOLDER_SQUARE(self):
        """
        Resource().PLACEHOLDER_SQUARE
        """
        return Image.new(mode='RGB', size=(448, 448), color=(0, 0, 0))

    @property
    def OFF_IMAGE_SQUARE(self):
        return self.squareify(self.OFF_IMAGE).resize((448, 448))

    @property
    def MOON_TEXTURE_SQUARE(self):
        return self.squareify(self.MOON_TEXUTRE).resize((448, 448))

    @property
    def RADIO_ICON_IMAGE_SQUARE(self):
        """
        Oct 13 00:23:23 jukeoroni gunicorn[20629]: Exception in thread State Watcher Thread:
Oct 13 00:23:23 jukeoroni gunicorn[20629]: Traceback (most recent call last):
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/usr/lib/python3.7/threading.py", line 917, in _bootstrap_inner
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     self.run()
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/usr/lib/python3.7/threading.py", line 865, in run
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     self._target(*self._args, **self._kwargs)
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 325, in state_watcher_task
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     self.set_display_radio()
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/django/jukeoroni/player/jukeoroni/jukeoroni.py", line 252, in set_display_radio
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     bg = self.layout_radio.get_layout(labels=self.LABELS, cover=self.radio.cover, title=self.radio.stream_title)
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/django/jukeoroni/player/jukeoroni/juke_radio.py", line 102, in cover
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     cover = Resource().RADIO_ICON_IMAGE_SQUARE
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/django/jukeoroni/player/jukeoroni/images.py", line 45, in RADIO_ICON_IMAGE_SQUARE
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     return self.squareify(self.RADIO_ICON_IMAGE).resize((448, 448))
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 1978, in resize
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     im = self.convert({"LA": "La", "RGBA": "RGBa"}[self.mode])
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 915, in convert
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     self.load()
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/PIL/ImageFile.py", line 237, in load
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     s = read(self.decodermaxblock)
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/PIL/PngImagePlugin.py", line 896, in load_read
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     cid, pos, length = self.png.read()
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/PIL/PngImagePlugin.py", line 166, in read
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     raise SyntaxError(f"broken PNG file (chunk {repr(cid)})")
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "<string>", line None
Oct 13 00:23:23 jukeoroni gunicorn[20629]: SyntaxError: broken PNG file (chunk b'\xfa}\x96\xd7')
Oct 13 00:23:23 jukeoroni gunicorn[20629]: [10-13-2021 00:23:23] [ERROR] [MainThread|3069569744] [django.request]: Internal Server Error: /jukeoroni/radio/
Oct 13 00:23:23 jukeoroni gunicorn[20629]: Traceback (most recent call last):
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/django/core/handlers/exception.py", line 47, in inner
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     response = get_response(request)
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/django/core/handlers/base.py", line 181, in _get_response
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     response = wrapped_callback(request, *callback_args, **callback_kwargs)
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/django/jukeoroni/player/views.py", line 337, in radio_index
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     img = jukeoroni.layout_radio.get_layout(labels=jukeoroni.LABELS, cover=jukeoroni.radio.cover, title=jukeoroni.radio.stream_title)
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/django/jukeoroni/player/jukeoroni/juke_radio.py", line 102, in cover
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     cover = Resource().RADIO_ICON_IMAGE_SQUARE
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/django/jukeoroni/player/jukeoroni/images.py", line 45, in RADIO_ICON_IMAGE_SQUARE
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     return self.squareify(self.RADIO_ICON_IMAGE).resize((448, 448))
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 1978, in resize
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     im = self.convert({"LA": "La", "RGBA": "RGBa"}[self.mode])
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/PIL/Image.py", line 915, in convert
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     self.load()
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/PIL/ImageFile.py", line 274, in load
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     raise_oserror(err_code)
Oct 13 00:23:23 jukeoroni gunicorn[20629]:   File "/data/venv/lib/python3.7/site-packages/PIL/ImageFile.py", line 67, in raise_oserror
Oct 13 00:23:23 jukeoroni gunicorn[20629]:     raise OSError(message + " when reading image file")
Oct 13 00:23:23 jukeoroni gunicorn[20629]: OSError: unrecognized data stream contents when reading image file

        """
        return self.squareify(self.RADIO_ICON_IMAGE).resize((448, 448))

    @property
    def ON_AIR_DEFAULT_IMAGE_SQUARE(self):
        return self.squareify(self.RADIO_ON_AIR_DEFAULT_IMAGE).resize((448, 448))

    @staticmethod
    def squareify(image):
        assert isinstance(image, Image.Image), 'need PIL Image to squareify'

        size = image.size

        small_side = min(size)
        large_side = max(size)

        if small_side == large_side:
            return image

        orientation = 'portrait' if size[0] < size[0] else 'landscape'

        crop_total = large_side - small_side
        crop_one_side = round(int(crop_total / 2))
        crop_other_side = crop_total - crop_one_side

        if orientation == 'landscape':
            top = 0
            bottom = small_side
            left = 0 + crop_one_side
            right = large_side - crop_other_side

        elif orientation == 'portrait':
            left = 0
            right = small_side
            top = 0 + crop_one_side
            bottom = large_side - crop_other_side

        image = image.crop((left, top, right, bottom))

        return image

    @staticmethod
    def round_resize(image, corner, factor=None, fixed=None):
        """
        # Resizes an image and keeps aspect ratio. Set mywidth to the desired with in pixels.

        import PIL
        from PIL import Image

        mywidth = 300

        img = Image.open('someimage.jpg')
        wpercent = (mywidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((mywidth,hsize), PIL.Image.ANTIALIAS)
        img.save('resized.jpg')
        """
        assert isinstance(image, Image.Image), 'need PIL Image to squareify'
        assert (factor is not None and fixed is None) or (fixed is not None and factor is None)

        w, h = image.size

        if factor:
            image = image.resize((round(w * factor), round(h * factor)))
        if fixed:
            if isinstance(fixed, int):
                image = image.resize((round(fixed), round(fixed)))
            elif isinstance(fixed, tuple):
                image = image.resize((round(fixed[0]), round(fixed[1])))

        bg = image.copy()  # use copy of image as background to prevent AA artifacts
        bg.putalpha(0)

        aa = 8

        mask = Image.new('RGBA', (image.size[0]*aa, image.size[1]*aa), color=(0, 0, 0, 0))

        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), mask.size], corner*aa, fill=(0, 0, 0, 255))

        mask = mask.resize(image.size, Image.ANTIALIAS)

        comp = Image.composite(image, bg, mask)

        return comp

    def from_url(self, url):
        if not is_string_url(url):
            return None

        try:
            hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
            req = urllib.request.Request(url, headers=hdr)
            response = urllib.request.urlopen(req)

            assert response.status == 200, f'status code is {str(response.status)} instead of 200'

            image = io.BytesIO(response.read())
            image = Image.open(image)
        except Exception:
            LOG.exception(f'Could not get online cover:')
            return None
            # image = self.RADIO_ON_AIR_DEFAULT_IMAGE

        return image
