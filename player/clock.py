import datetime
from PIL import Image, ImageDraw, ImageFont


def clock(draw_logo, draw_date, size=448):



    bg = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
    image = Image.new(mode='RGB', size=(size, size), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    # draw.ellipse([(0, 0), (448, 448)], fill=None, outline=(255, 255, 0), width=14)  # circle
    # draw.line([(448/2, 448/2), (448/2, 448/3)], fill=(0, 0, 0), width=12, joint=None)  # stundenzeiger x600/y448 ist unten rechts
    # draw.line([(448/2, 448/2), (448/2, 0)], fill=(0, 0, 0), width=7, joint=None)  # minutenzeiger x0/y0 ist oben links

    arc_twelve = 270.0

    white = (255, 255, 255)
    black = (0, 0, 0)
    toggle = {white: black, black: white}
    # colors = {(255, 255, 0): (0, 0, 0)}

    draw.ellipse([(int(size*0.482), int(size*0.482)), (int(size-size*0.482), int(size-size*0.482))], fill=white, outline=None, width=int(size*0.312))

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
    for interval in [0.0, 3.0, 29.0, 31.0, 59.0, 61.0, 87.0, 93.0, 119.0, 121.0, 149.0, 151.0, 177.0, 183.0, 209.0,
                     211.0, 239.0, 241.0, 267.0, 273.0, 299.0, 301.0, 329.0, 331.0, 357.0][::-1]:
        draw.arc([(int(size*0.022), int(size*0.022)), (int(size-size*0.022), int(size-size*0.022))], start=arc_twelve, end=(arc_twelve + interval) % 360, fill=color, width=int(size*0.067))
        color = toggle[color]
    ####

    decimal_h = float(datetime.datetime.now().strftime('%I')) + float(datetime.datetime.now().strftime('%M')) / 60
    arc_length_h = decimal_h / 12.0 * 360.0

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
    size_h = [(int(size*0.112), int(size*0.112)), (int(size-size*0.112), int(size-size*0.112))]
    width = int(size*0.134)
    draw.arc(size_h, start=arc_twelve, end=(arc_twelve + arc_length_h + int(size*0.007)) % 360, fill=color,
             width=width)
    color = toggle[color]
    draw.arc(size_h, start=arc_twelve, end=(arc_twelve + arc_length_h - int(size*0.007)) % 360, fill=color,
             width=width)
    # color = toggle[color]
    if draw_logo:
        font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/calligraphia-one.ttf', int(size*0.140))
        text = "JukeOroni"
        length = font.getlength(text)
        # print(length)
        draw.text((int(size/2) - length / 2, int(size*0.536)), text, fill=white, font=font)

    if draw_date:
        font = ImageFont.truetype(r'/data/django/jukeoroni/player/static/arial_narrow.ttf', int(size*0.045))
        text = datetime.datetime.now().strftime('%A, %B %d %Y')
        length = font.getlength(text)
        draw.text((int(size/2) - length / 2, int(size*0.670)), text, fill=white, font=font)

    bg.paste(image.rotate(90, expand=False))
    bg.paste(image)

    # bg = bg.resize((448, 448), Image.ANTIALIAS)
    # bg = bg.resize((int(bg.size[0] * factor), int(bg.size[1] * factor)))

    return bg

    # inky.set_image(bg, saturation=1.0)
    # inky.show()

    # time.sleep(sleep_time)
