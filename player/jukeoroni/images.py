from player.jukeoroni.settings import (_RADIO_ICON_IMAGE,
                                       _RADIO_ON_AIR_DEFAULT_IMAGE,
                                       _JUKEBOX_ON_AIR_DEFAULT_IMAGE,
                                       _OFF_IMAGE,
                                       _JUKEBOX_ICON_IMAGE,
                                       GLOBAL_LOGGING_LEVEL,
                                       )
from player.jukeoroni.is_string_url import is_string_url
from PIL import Image, ImageDraw
import urllib.request
import io
import logging


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


class Resource(object):
    """
    from player.jukeoroni.images import Resource
    """
    OFF_IMAGE = Image.open(_OFF_IMAGE)
    RADIO_ICON_IMAGE = Image.open(_RADIO_ICON_IMAGE)
    RADIO_ON_AIR_DEFAULT_IMAGE = Image.open(_RADIO_ON_AIR_DEFAULT_IMAGE)

    JUKEBOX_ICON_IMAGE = Image.open(_JUKEBOX_ICON_IMAGE)
    JUKEBOX_ON_AIR_DEFAULT_IMAGE = Image.open(_JUKEBOX_ON_AIR_DEFAULT_IMAGE)

    @property
    def PLACEHOLDER_SQUARE(self):
        """
        Resource().PLACEHOLDER_SQUARE
        """
        return Image.new(mode='RGB', size=(448, 448), color=(128, 128, 128))

    @property
    def OFF_IMAGE_SQUARE(self):
        return self.squareify(self.OFF_IMAGE).resize((448, 448))

    @property
    def RADIO_ICON_IMAGE_SQUARE(self):
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

        bg = Image.new('RGBA', image.size, color=(0, 0, 0, 0))

        mask = Image.new('RGBA', image.size, color=(0, 0, 0, 0))
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), image.size], corner, fill=(0, 0, 0, 255))

        comp = Image.composite(image, bg, mask)

        return comp

    def from_url(self, url):
        assert is_string_url(url), 'given string is not a URL'

        try:
            hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}
            req = urllib.request.Request(url, headers=hdr)
            response = urllib.request.urlopen(req)

            assert response.status == 200, f'status code is {str(response.status)} instead of 200'

            image = io.BytesIO(response.read())
            image = Image.open(image)
        except Exception as err:
            LOG.exception(f'Could not get online cover:')
            image = self.RADIO_ON_AIR_DEFAULT_IMAGE

        return image
