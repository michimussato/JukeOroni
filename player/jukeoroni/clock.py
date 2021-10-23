import datetime
import logging
import math
# import numpy as np

import astral.moon

try:
    from jukeoroni.settings import TIME_ZONE
    tz = TIME_ZONE
    print('using djangos timezone')
except ImportError as err:
    tz = "Europe/Zurich"
from PIL import Image, ImageDraw, ImageFont, ImageOps  # , ImageFilter
from astral.sun import sun
from player.jukeoroni.settings import (
    GLOBAL_LOGGING_LEVEL,
    CITY,
    ANTIALIAS,
    ARIAL,
    CALLIGRAPHIC
)


LOG = logging.getLogger(__name__)
LOG.setLevel(GLOBAL_LOGGING_LEVEL)


class Clock(object):

    @staticmethod
    def get_clock(draw_logo, draw_date, size=448, hours=12, draw_astral=False, draw_moon=False, square=False):

        _size = size * ANTIALIAS

        assert hours in [12, 24], 'hours can only be 12 or 24'

        bg = Image.new(mode='RGBA', size=(_size, _size), color=(0, 0, 0, 0))
        draw_bg = ImageDraw.Draw(bg)
        edge_compensation = 1  # top and left edge to make sure, AA takes place in pixels adjacent to edges
        _edge_comp_2 = 1  # bottom and right edge in addition to edge_compensation
        if square:
            draw_bg.rectangle((0+edge_compensation, 0+edge_compensation, _size-edge_compensation-_edge_comp_2, _size-edge_compensation-_edge_comp_2), fill=(0, 0, 0, 255))
        else:
            draw_bg.ellipse((0+edge_compensation, 0+edge_compensation, _size-edge_compensation-_edge_comp_2, _size-edge_compensation-_edge_comp_2), fill=(0, 0, 0, 255))

        _clock = Image.new(mode='RGBA', size=(_size, _size), color=(0, 0, 0, 0))

        draw = ImageDraw.Draw(_clock)

        if hours == 24:
            arc_twelve = 90.0
        else:
            arc_twelve = 270.0

        white = (255, 255, 255, 255)

        LOG.info(f'Moon phase: {round(float(astral.moon.phase()))} / 28')

        if draw_astral:
            city = CITY
            _sun = sun(city.observer, date=datetime.date.today(), tzinfo=city.timezone)

            decimal_sunrise = float(_sun['sunrise'].strftime('%H')) + float(_sun['sunrise'].strftime('%M')) / 60
            arc_length_sunrise = decimal_sunrise / hours * 360.0
            LOG.info(f'Sunrise: {str(_sun["sunrise"].strftime("%H:%M"))}')

            decimal_sunset = float(_sun['sunset'].strftime('%H')) + float(_sun['sunset'].strftime('%M')) / 60
            arc_length_sunset = decimal_sunset / hours * 360.0
            LOG.info(f'Sunset: {str(_sun["sunset"].strftime("%H:%M"))}')

            color = (255, 128, 0, 255)
            _size_astral = 0.17  # TODO: bigger means smaller circle
            _width = 0.012
            size_astral = [(round(_size * _size_astral), round(_size * _size_astral)), (round(_size - _size * _size_astral), round(_size - _size * _size_astral))]
            width_astral = round(_size * _width)
            draw.arc(size_astral, start=arc_length_sunrise+arc_twelve, end=arc_length_sunset+arc_twelve, fill=color,
                     width=width_astral)

        # center dot
        draw.ellipse([(round(_size * 0.482), round(_size * 0.482)), (round(_size - _size * 0.482), round(_size - _size * 0.482))], fill=white, outline=None, width=round(_size * 0.312))

        color = white
        # TODO: we could do the intervals smarter now
        if hours == 24:
            intervals = [(0.0, 3.0),
                         (14.0, 16.0),
                         (29.0, 31.0),
                         (42.0, 48.0),
                         (59.0, 61.0),
                         (74.0, 76.0),
                         (87.0, 93.0),
                         (104.0, 106.0),
                         (119.0, 121.0),
                         (132.0, 138.0),
                         (149.0, 151.0),
                         (164.0, 166.0),
                         (177.0, 183.0),
                         (194.0, 196.0),
                         (209.0, 211.0),
                         (222.0, 228.0),
                         (239.0, 241.0),
                         (254.0, 256.0),
                         (267.0, 273.0),
                         (284.0, 286.0),
                         (299.0, 301.0),
                         (312.0, 318.0),
                         (329.0, 331.0),
                         (344.0, 346.0),
                         (357.0, 359.99),
                         ]
        else:
            intervals = [(0.0, 3.0),
                         (29.0, 31.0),
                         (59.0, 61.0),
                         (87.0, 93.0),
                         (119.0, 121.0),
                         (149.0, 151.0),
                         (177.0, 183.0),
                         (209.0, 211.0),
                         (239.0, 241.0),
                         (267.0, 273.0),
                         (299.0, 301.0),
                         (329.0, 331.0),
                         (357.0, 359.99),
                         ]

        for start, end in intervals[::-1]:  # reversed
            draw.arc([(round(_size * 0.022), round(_size * 0.022)), (round(_size - _size * 0.022), round(_size - _size * 0.022))], start=start, end=end, fill=color, width=round(_size * 0.060))

        decimal_h = float(datetime.datetime.now().strftime('%H')) + float(datetime.datetime.now().strftime('%M')) / 60
        arc_length_h = decimal_h / hours * 360.0

        # indicator
        color = white
        size_h = [(round(_size * 0.112), round(_size * 0.112)), (round(_size - _size * 0.112), round(_size - _size * 0.112))]
        width = round(_size * 0.134)
        draw.arc(size_h, start=(arc_twelve + arc_length_h - round(_size / ANTIALIAS * 0.007)) % 360, end=(arc_twelve + arc_length_h + round(_size / ANTIALIAS * 0.007)) % 360, fill=color,
                 width=width)

        if draw_logo:
            font = ImageFont.truetype(CALLIGRAPHIC, round(_size * 0.150))
            text = 'JukeOroni'
            length = font.getlength(text)
            draw.text((round(_size / 2) - length / 2, round(_size * 0.536)), text, fill=white, font=font)

        if draw_date:
            font = ImageFont.truetype(ARIAL, round(_size * 0.035))
            text = datetime.datetime.now().strftime('%A, %B %d %Y')
            length = font.getlength(text)
            draw.text((round(_size / 2) - length / 2, round(_size * 0.690)), text, fill=white, font=font)

        comp = Image.new(mode='RGBA', size=(_size, _size))
        comp = Image.alpha_composite(comp, bg)
        comp = Image.alpha_composite(comp, _clock)

        if draw_moon:
            _draw_moon_image = Image.new(mode='RGBA', size=(_size, _size), color=(0, 0, 0, 0))
            _draw_moon = ImageDraw.Draw(_draw_moon_image)
            _draw_moon.ellipse(((edge_compensation, edge_compensation), (_size-edge_compensation-_edge_comp_2, _size-edge_compensation-_edge_comp_2)), fill=white)
            phase = round(float(astral.moon.phase()) / 28.0 * 2, 4)

            spherical = math.cos(phase * math.pi)

            center = _size / 2

            if 0.0 <= phase <= 0.5:  # new to half moon
                _draw_moon.rectangle((0, 0, _size / 2, _size), fill=(0, 0, 0, 0))
                _draw_moon.ellipse((center - (spherical * center) + edge_compensation, 0 + edge_compensation, center + (spherical * center) - edge_compensation, _size - edge_compensation),
                                   fill=(0, 0, 0, 0))

            elif 0.5 <= phase <= 1.0:  # half to full moon
                _draw_moon.rectangle((0, 0, _size / 2, _size), fill=(0, 0, 0, 0))
                _draw_moon.ellipse((center + (spherical * center) + edge_compensation, 0 + edge_compensation, center - (spherical * center) - edge_compensation -_edge_comp_2, _size - edge_compensation - _edge_comp_2),
                                   fill=white)

                # # _temp = Image.new(mode='RGBA', size=(_size*2, _size), color=(0, 0, 0, 0))
                # blur_weight = 5
                # for i in range(75):
                #     kernel = np.array([[0, 0, 0, 0, 0],
                #                        [0, 0, 0, 0, 0],
                #                        [blur_weight, blur_weight, blur_weight, blur_weight, blur_weight],
                #                        [0, 0, 0, 0, 0],
                #                        [0, 0, 0, 0, 0]])
                #     _draw_moon_image = _draw_moon_image.filter(ImageFilter.Kernel(size=(5, 5), kernel=kernel.flatten()))
                #     # _temp = _temp.crop((_size/4, 0, _size/4*3, _size))
                #     # _temp = _temp.resize((_size, _size))
                #     # _draw_moon_image = _draw_mo.paste(_temp)
                #     # _draw_moon.rectangle((0, 0, _size / 2, _size), fill=(0, 0, 0, 0))
                #     # _draw_moon.rectangle((_size / 2, 0, _size, _size), fill=(0, 0, 0, 0))

            elif 1.0 < phase <= 1.5:  # full to half moon
                _draw_moon.rectangle((_size / 2, 0, _size, _size), fill=(0, 0, 0, 0))
                _draw_moon.ellipse((center + (spherical * center) + edge_compensation, 0 + edge_compensation, center - (spherical * center) - edge_compensation-_edge_comp_2, _size - edge_compensation-_edge_comp_2),
                                   fill=white)

            elif 1.5 < phase <= 2.0:  # half to new moon
                _draw_moon.rectangle((_size / 2, 0, _size, _size), fill=(0, 0, 0, 0))
                _draw_moon.ellipse((center - (spherical * center) + edge_compensation, 0 + edge_compensation, center + (spherical * center) - edge_compensation, _size - edge_compensation),
                                   fill=(0, 0, 0, 0))

            _comp_inv = ImageOps.invert(comp.convert('RGB'))

            comp.paste(_comp_inv, mask=_draw_moon_image)

        comp = comp.rotate(90, expand=False)

        comp = comp.resize((round(_size/ANTIALIAS), round(_size/ANTIALIAS)), Image.ANTIALIAS)

        return comp
