import logging
from PIL import Image, ImageDraw, ImageFont, ImageOps
from player.jukeoroni.clock import Clock
from player.jukeoroni.radar import Radar
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
    # RADIO_ICON_IMAGE,
    SMALL_WIDGET_SIZE,
)
from player.jukeoroni.images import Resource


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


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


BUTTONS_HEIGHT = 32
BORDER = 4
BUTTONS_ICONS = {
    'Radio': '/data/django/jukeoroni/player/static/buttons_overlay/icon_radio.png',
    'Player': '/data/django/jukeoroni/player/static/buttons_overlay/icon_player.png',
    'Random -> Album': '/data/django/jukeoroni/player/static/buttons_overlay/icon_random.png',
    'Album -> Random': '/data/django/jukeoroni/player/static/buttons_overlay/icon_album.png',
    'N//A': '/data/django/jukeoroni/player/static/buttons_overlay/icon_na.png',
    'Stop': '/data/django/jukeoroni/player/static/buttons_overlay/icon_stop.png',
    'Play': '/data/django/jukeoroni/player/static/buttons_overlay/icon_play.png',
    'Next': '/data/django/jukeoroni/player/static/buttons_overlay/icon_next.png',
    'Menu': '/data/django/jukeoroni/player/static/buttons_overlay/icon_menu.png'
}


def buttons_img_overlay(labels):
    widget_buttons = Image.new(mode='RGBA', size=(448, 448), color=(0, 0, 0, 180))

    invert = True
    n = 0
    for _label in labels[::-1]:
        n += 1
        label = Image.open(BUTTONS_ICONS[_label])
        if invert:
            r, g, b, a = label.split()
            rgb_image = Image.merge('RGB', (r, g, b))
            inverted_image = ImageOps.invert(rgb_image)
            r2, g2, b2 = inverted_image.split()
            label = Image.merge('RGBA', (r2, g2, b2, a))

        label = label.resize((BUTTONS_HEIGHT, BUTTONS_HEIGHT))
        label_bg = Image.new(mode='RGBA', size=widget_buttons.size, color=(0, 0, 0, 0))

        label_bg.paste(im=label, box=(int(round(n*448/4 - 448/4/2 - BUTTONS_HEIGHT/2)), BORDER))

        widget_buttons = Image.alpha_composite(widget_buttons, label_bg)

    comp_buttons = Image.new(mode='RGBA', size=widget_buttons.size)
    comp_buttons = Image.alpha_composite(comp_buttons, widget_buttons)
    comp_buttons = comp_buttons.rotate(90, expand=False)
    comp_buttons = comp_buttons.crop((0, 0, BUTTONS_HEIGHT + BORDER*2, widget_buttons.size[0]))

    return comp_buttons


class Layout:
    _clock = Clock()
    radar = Radar()
    border = BORDER
    main_size = 420 - 2*BORDER - BUTTONS_HEIGHT


class Standby(Layout):

    def get_layout(self, labels):

        buttons_overlay = buttons_img_overlay(labels=labels)
        bg = Image.new(mode='RGBA', size=(600, 448), color=(255, 0, 0, 255))
        widget_clock = Image.new(mode='RGBA', size=(self.main_size, self.main_size), color=(0, 0, 0, 0))
        comp_clock = Image.new(mode='RGBA', size=widget_clock.size)

        clock_size = self.main_size
        _clock = self._clock.get_clock(size=clock_size, draw_logo=True, draw_date=True, hours=24, draw_astral=True)

        comp_clock = Image.alpha_composite(comp_clock, widget_clock)
        comp_clock = Image.alpha_composite(comp_clock, _clock)

        _clock_center = round(bg.size[1]/2 - clock_size/2)
        # _clock_right = 0_radar_image.size is
        # _clock_left = bg.size[1] - clock_size

        bg.paste(comp_clock, box=(buttons_overlay.size[0] + self.border, _clock_center), mask=comp_clock)

        _radar_image = self.radar.radar_image

        if _radar_image is not None:
            _radar_image = Resource().round_resize(image=_radar_image, corner=40, fixed=SMALL_WIDGET_SIZE)
            LOG.info(f'_radar_image.size is {str(_radar_image.size)}')

            _radar_bottom_centered = (int(600 - SMALL_WIDGET_SIZE - self.border),
                                      int(448 / 2 + round(self.border / 2) - round(SMALL_WIDGET_SIZE / 2)))

            _radar_bottom_right_centered = (int(600 - SMALL_WIDGET_SIZE - self.border),
                                            int(0 + 224 / 2 + round(self.border / 2) - round(SMALL_WIDGET_SIZE / 2)))

            # _radar_bottom_right = (int(600-w-self.border), self.border)
            bg.paste(_radar_image, _radar_bottom_centered, mask=_radar_image)

        bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        return bg


class Jukebox(Layout):

    def get_layout(self, labels, loading=False, cover=None, artist=None):

        if loading:
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

        buttons_overlay = buttons_img_overlay(labels)
        bg = Image.new(mode='RGBA', size=(600, 448), color=(0, 255, 0, 255))

        cover_size = self.main_size

        cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)

        cover = cover.rotate(90, expand=True)

        cover = Resource().round_resize(image=cover, corner=40, factor=1.0)

        if artist:
            scale_cover_artist = 4
            cover_artist = artist.rotate(90, expand=True)
            # TODO move to rounde_resize
            cover_artist = cover_artist.resize((round(cover_size/scale_cover_artist), round(cover_size/scale_cover_artist)), Image.ANTIALIAS)
            cover_artist = Resource().round_resize(image=cover_artist, corner=20, factor=1.0)

            cover.paste(cover_artist, box=(round(cover_size - cover_size/scale_cover_artist)-20, 20), mask=cover_artist)

        _cover_center = round(bg.size[1] / 2 - cover_size / 2)
        bg.paste(cover, box=(buttons_overlay.size[0] + self.border, _cover_center), mask=cover)

        # SMALL_WIDGET_SIZE = 151
        _clock = self._clock.get_clock(size=SMALL_WIDGET_SIZE, draw_logo=False, draw_date=False, hours=24, draw_astral=True, square=True)
        _clock = Resource().round_resize(image=_clock, corner=40, fixed=SMALL_WIDGET_SIZE)
        _clock_bottom_left_centered = (int(600 - SMALL_WIDGET_SIZE - self.border),
                                       int(224 + 224/2 + round(self.border/2) - round(SMALL_WIDGET_SIZE/2)))
        _clock_bottom_left = (int(600 - SMALL_WIDGET_SIZE - self.border),
                              int(448 - SMALL_WIDGET_SIZE - self.border))

        bg.paste(_clock, box=_clock_bottom_left_centered, mask=_clock)

        _radar_image = self.radar.radar_image

        if _radar_image is not None:
            _radar_image = Resource().round_resize(image=_radar_image, corner=40, fixed=SMALL_WIDGET_SIZE)
            LOG.info(f'_radar_image.size is {str(_radar_image.size)}')
            # _radar_bottom_right = (int(600 - w - self.border), self.border)
            _radar_bottom_right_centered = (int(600 - SMALL_WIDGET_SIZE - self.border),
                                            int(0 + 224 / 2 + round(self.border / 2) - round(SMALL_WIDGET_SIZE / 2)))
            bg.paste(_radar_image, box=_radar_bottom_right_centered, mask=_radar_image)

        bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        return bg


class Radio(Layout):

    def get_layout(self, labels, cover, title):

        assert isinstance(cover, Image.Image), f'Radio Channel cover type must be PIL.Image.Image() (not rotated). Got: {cover}'

        buttons_overlay = buttons_img_overlay(labels)
        bg = Image.new(mode='RGBA', size=(600, 448), color=(0, 0, 255, 255))

        cover_size = self.main_size

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
        _clock = self._clock.get_clock(size=SMALL_WIDGET_SIZE, draw_logo=False, draw_date=False, hours=24, draw_astral=True, square=True)
        _clock = Resource().round_resize(image=_clock, corner=40, fixed=SMALL_WIDGET_SIZE)
        _clock_bottom_left_centered = (int(600 - SMALL_WIDGET_SIZE - self.border),
                                       int(224 + 224/2 + round(self.border/2) - round(SMALL_WIDGET_SIZE/2)))
        _clock_bottom_left = (int(600 - SMALL_WIDGET_SIZE - self.border),
                              int(448 - SMALL_WIDGET_SIZE - self.border))

        bg.paste(_clock, box=_clock_bottom_left_centered, mask=_clock)

        _radar_image = self.radar.radar_image

        if _radar_image is not None:
            _radar_image = Resource().round_resize(image=_radar_image, corner=40, fixed=SMALL_WIDGET_SIZE)
            LOG.info(f'_radar_image.size is {str(_radar_image.size)}')

            _radar_bottom_right_centered = (int(600 - SMALL_WIDGET_SIZE - self.border),
                                            int(0 + 224 / 2 + round(self.border / 2) - round(SMALL_WIDGET_SIZE / 2)))

            # _radar_bottom_right = (int(600 - w - self.border), self.border)
            bg.paste(_radar_image, box=_radar_bottom_right_centered, mask=_radar_image)

        bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        return bg


class Off(Layout):

    # _clock = None
    # radar = None

    def get_layout(self, labels, cover):

        assert isinstance(cover, Image.Image), f'Radio Channel cover type must be PIL.Image.Image() (not rotated). Got: {cover}'

        buttons_overlay = buttons_img_overlay(labels)
        bg = Image.new(mode='RGBA', size=(600, 448), color=(0, 0, 0, 255))

        # cover_size = 448 - 2 * self.border
        cover_size = self.main_size

        cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)

        cover = cover.rotate(90, expand=True)

        cover = Resource().round_resize(image=cover, corner=40, factor=1.0)

        _cover_center = round(bg.size[1] / 2 - cover_size / 2)
        bg.paste(cover, box=(buttons_overlay.size[0] + self.border, _cover_center), mask=cover)

        bg.paste(buttons_overlay, box=(0, 0), mask=buttons_overlay)

        return bg
