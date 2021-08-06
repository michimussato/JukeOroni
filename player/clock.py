import datetime
try:
    from jukeoroni.settings import TIME_ZONE
    tz = TIME_ZONE
    print('using djangos timezone')
except ImportError as err:
    tz = "Europe/Zurich"
from PIL import Image, ImageDraw, ImageFont
from astral import LocationInfo
from astral.sun import sun


ANTIALIAS = 16


class Clock:

    @staticmethod
    def get_clock(draw_logo, draw_date, size=448, hours=12, draw_astral=False):

        _size = size * ANTIALIAS

        assert hours in [12, 24], 'hours can only be 12 or 24'

        # bg = Image.new(mode='RGB', size=(_size, _size), color=(0, 0, 0, 0))
        bg = Image.new(mode='RGBA', size=(_size, _size), color=(255, 0, 0, 0))
        # _bg = Image.new(mode='RGBA', size=(_size, _size))
        # draw = ImageDraw.Draw(bg)
        # draw.ellipse([(0, 0), (300, 300)], fill=(255,0,0))
        # bg = Image.alpha_composite(bg, _bg)
        # draw = Image.Imag
        # alpha_mask = Image.new('L', _bg.size, 0)
        # alpha_mask_draw = ImageDraw.Draw(alpha_mask)
        # alpha_mask_draw.ellipse([(0, 0), (300, 300)], fill=255)
        # mask_bg_draw = ImageDraw.Draw(_bg, 'RGBA')
        # mask_bg_draw.ellipse([(0,0),(300,300)], fill=(255,0,0,255))
        # bg = Image.composite(_bg, mask=mask_bg_draw)
        # image = Image.new(mode='RGB', size=(_size, _size), color=(0, 0, 0))
        # draw = ImageDraw.Draw(image)

        if hours == 24:
            arc_twelve = 90.0
        else:
            arc_twelve = 270.0

        white = (255, 255, 255)
        black = (0, 0, 0)
        toggle = {white: black, black: white}

        if draw_astral:
            city = LocationInfo("Bern", "Switzerland", tz, 46.94809, 7.44744)
            _sun = sun(city.observer, date=datetime.date.today(), tzinfo=city.timezone)

            decimal_sunrise = float(_sun["sunrise"].strftime('%H')) + float(_sun["sunrise"].strftime('%M')) / 60
            arc_length_sunrise = decimal_sunrise / hours * 360.0
            print('sunrise: {0}'.format(_sun["sunrise"].strftime('%H:%M')))

            decimal_sunset = float(_sun["sunset"].strftime('%H')) + float(_sun["sunset"].strftime('%M')) / 60
            arc_length_sunset = decimal_sunset / hours * 360.0
            print('sunset: {0}'.format(_sun["sunset"].strftime('%H:%M')))

            color = (255, 128, 0)
            _size_astral = 0.17  # TODO: bigger means smaller circle
            _width = 0.012
            size_astral = [(round(_size * _size_astral), round(_size * _size_astral)), (round(_size - _size * _size_astral), round(_size - _size * _size_astral))]
            width_astral = round(_size * _width)
            # draw.arc(size_astral, start=arc_length_sunrise+arc_twelve, end=arc_length_sunset+arc_twelve, fill=color,
            #          width=width_astral)

        # draw.ellipse([(round(_size * 0.482), round(_size * 0.482)), (round(_size - _size * 0.482), round(_size - _size * 0.482))], fill=white, outline=None, width=round(_size * 0.312))

        color = white
        # TODO: we could do the intervals smarter now
        if hours == 24:
            intervals = [0.0, 3.0,
                         14.0, 16.0,
                         29.0, 31.0,
                         42.0, 48.0,
                         59.0, 61.0,
                         74.0, 76.0,
                         87.0, 93.0,
                         104.0, 106.0,
                         119.0, 121.0,
                         132.0, 138.0,
                         149.0, 151.0,
                         164.0, 166.0,
                         177.0, 183.0,
                         194.0, 196.0,
                         209.0, 211.0,
                         222.0, 228.0,
                         239.0, 241.0,
                         254.0, 256.0,
                         267.0, 273.0,
                         284.0, 286.0,
                         299.0, 301.0,
                         312.0, 318.0,
                         329.0, 331.0,
                         344.0, 346.0,
                         357.0]
        else:
            intervals = [0.0, 3.0,
                         29.0, 31.0,
                         59.0, 61.0,
                         87.0, 93.0,
                         119.0, 121.0,
                         149.0, 151.0,
                         177.0, 183.0,
                         209.0, 211.0,
                         239.0, 241.0,
                         267.0, 273.0,
                         299.0, 301.0,
                         329.0, 331.0,
                         357.0]

        for interval in intervals[::-1]:
            # draw.arc([(round(_size * 0.022), round(_size * 0.022)), (round(_size - _size * 0.022), round(_size - _size * 0.022))], start=arc_twelve, end=(arc_twelve + interval) % 360, fill=color, width=round(_size * 0.060))
            color = toggle[color]

        decimal_h = float(datetime.datetime.now().strftime('%H')) + float(datetime.datetime.now().strftime('%M')) / 60
        arc_length_h = decimal_h / hours * 360.0

        color = white
        size_h = [(round(_size * 0.112), round(_size * 0.112)), (round(_size - _size * 0.112), round(_size - _size * 0.112))]
        width = round(_size * 0.134)
        # draw.arc(size_h, start=(arc_twelve + arc_length_h - round(_size / ANTIALIAS * 0.007)) % 360, end=(arc_twelve + arc_length_h + round(_size / ANTIALIAS * 0.007)) % 360, fill=color,
        #          width=width)

        if draw_logo:
            font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/calligraphia-one.ttf', round(_size * 0.150))
            text = "JukeOroni"
            length = font.getlength(text)
            # draw.text((round(_size / 2) - length / 2, round(_size * 0.536)), text, fill=white, font=font)

        if draw_date:
            font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', round(_size * 0.035))
            text = datetime.datetime.now().strftime('%A, %B %d %Y')
            length = font.getlength(text)
            # draw.text((round(_size / 2) - length / 2, round(_size * 0.690)), text, fill=white, font=font)

        # bg.paste(image.rotate(90, expand=False))
        # bg.paste(image)

        bg = bg.rotate(90, expand=False)
        bg = bg.resize((round(_size/ANTIALIAS), round(_size/ANTIALIAS)), Image.ANTIALIAS)

        return bg
