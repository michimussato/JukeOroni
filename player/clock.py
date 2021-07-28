import datetime
from PIL import Image, ImageDraw, ImageFont


def clock(draw_logo, draw_date, size=448, hours=12, draw_astral=False):

    assert hours in [12, 24], 'hours can only be 12 or 24'

    bg = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
    image = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    # draw.ellipse([(0, 0), (448, 448)], fill=None, outline=(255, 255, 0), width=14)  # circle
    # draw.line([(448/2, 448/2), (448/2, 448/3)], fill=(0, 0, 0), width=12, joint=None)  # stundenzeiger x600/y448 ist unten rechts
    # draw.line([(448/2, 448/2), (448/2, 0)], fill=(0, 0, 0), width=7, joint=None)  # minutenzeiger x0/y0 ist oben links

    if hours == 24:
        arc_twelve = 90.0
    else:
        arc_twelve = 270.0

    white = (255, 255, 255)
    black = (0, 0, 0)
    toggle = {white: black, black: white}
    # colors = {(255, 255, 0): (0, 0, 0)}

    draw.ellipse([(round(size*0.482), round(size*0.482)), (round(size-size*0.482), round(size-size*0.482))], fill=white, outline=None, width=round(size*0.312))

    ####
    # variante 1
    # color = black
    # for interval in [0.0, 30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0, 360.0][::-1]:
    #    draw.arc([(70, 70), (378, 378)], start=arc_twelve, end=(arc_twelve + interval) % 360, fill=color, width=60)
    #    color = toggle[color]
    ####

    ####
    # variante 2
    color = white

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
        draw.arc([(round(size*0.022), round(size*0.022)), (round(size-size*0.022), round(size-size*0.022))], start=arc_twelve, end=(arc_twelve + interval) % 360, fill=color, width=round(size*0.060))
        color = toggle[color]
    ####

    decimal_h = float(datetime.datetime.now().strftime('%I')) + float(datetime.datetime.now().strftime('%M')) / 60
    arc_length_h = decimal_h / hours * 360.0

    # decimal_m = float(datetime.datetime.now().strftime('%M')) / 60
    # arc_length_m = decimal_m * 360

    # color = yellow
    ## for bounding_box in [[(20, 20), (428, 428)], [(100, 100), (348, 348)]]:
    # width = 20
    # draw.arc([(40, 40), (428, 428)], start=arc_twelve, end=(arc_twelve+arc_length_m+1.5) % 360, fill=color, width=width)
    # color = toggle[color]
    # draw.arc([(40, 40), (428, 428)], start=arc_twelve, end=(arc_twelve+arc_length_m-1.5) % 360, fill=color, width=width)
    # color = toggle[color]

    color = white
    size_h = [(round(size*0.112), round(size*0.112)), (round(size-size*0.112), round(size-size*0.112))]
    width = round(size*0.134)
    draw.arc(size_h, start=arc_twelve, end=(arc_twelve + arc_length_h + round(size*0.007)) % 360, fill=color,
             width=width)
    color = toggle[color]
    draw.arc(size_h, start=arc_twelve, end=(arc_twelve + arc_length_h - round(size*0.007)) % 360, fill=color,
             width=width)

    if draw_astral:
        from astral import LocationInfo
        from astral.sun import sun

        city = LocationInfo("Bern", "Switzerland", "Europe/Zurich", 46.94809, 7.44744)
        _sun = sun(city.observer, date=datetime.date.today(), tzinfo=city.timezone)

        decimal_sunrise = float(_sun["sunrise"].strftime('%I')) + float(_sun["sunrise"].strftime('%M')) / 60
        arc_length_sunrise = decimal_sunrise / hours * 360.0

        decimal_sunset = float(_sun["sunset"].strftime('%I')) + float(_sun["sunset"].strftime('%M')) / 60
        arc_length_sunset = decimal_sunset / hours * 360.0

        color = white
        _size = 0.09
        _width = 0.05
        size_astral = [(round(size * _size), round(size * _size)), (round(size - size * _size), round(size - size * _size))]
        width_astral = round(size * _width)
        draw.arc(size_astral, start=arc_length_sunrise, end=arc_length_sunset, fill=color,
                 width=width_astral)
        # color = toggle[color]
        # draw.arc(size_h, start=arc_twelve, end=(arc_twelve + arc_length_h - round(size * 0.007)) % 360, fill=color,
        #          width=width)

    # color = toggle[color]
    if draw_logo:
        font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/calligraphia-one.ttf', round(size*0.150))
        text = "JukeOroni"
        length = font.getlength(text)
        # print(length)
        draw.text((round(size/2) - length / 2, round(size*0.536)), text, fill=white, font=font)

    if draw_date:
        font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', round(size*0.035))
        text = datetime.datetime.now().strftime('%A, %B %d %Y')
        length = font.getlength(text)
        draw.text((round(size/2) - length / 2, round(size*0.690)), text, fill=white, font=font)



    bg.paste(image.rotate(90, expand=False))
    bg.paste(image)

    return bg


from astral import LocationInfo
s = sun(city.observer, date=datetime.date.today(), tzinfo=city.timezone)
# >>> print((
#     f"Information for {city.name}/{city.region}\n"
#     f"Timezone: {city.timezone}\n"
#     f"Latitude: {city.latitude:.02f}; Longitude: {city.longitude:.02f}\n"
# ))

# Information for London/England
# Timezone: Europe/London
# Latitude: 51.50; Longitude: -0.12

import datetime
from astral.sun import sun
s = sun(city.observer, date=datetime.date.today())

s["dawn"]
s["sunrise"]
s["noon"]
s["sunset"]
s["dusk"]
