from PIL import Image, ImageDraw
from .clock import clock
from .radar import Radar


def buttons_img_overlay(labels):
    buttons_img = Image.new(mode='RGB', size=(448, 16), color=(80, 80, 80))
    buttons_draw = ImageDraw.Draw(buttons_img)
    buttons_draw.text((0, 0), '       {0}               {1}               {2}           {3}'.format(
        labels[3],
        labels[2],
        labels[1],
        labels[0],
    ), fill=(255, 255, 255))

    return buttons_img.rotate(90, expand=True)


def standby(labels):
    _clock = clock(size=400, draw_logo=True, draw_date=True, hours=24, draw_astral=True)
    _radar = Radar()
    _radar_image = _radar.image(scaled_by=0.45)

    buttons_overlay = buttons_img_overlay(labels)
    bg = Image.new(mode='RGB', size=(600, 448), color=(0, 0, 0))

    w, h = _clock.size
    _clock_center = round(bg.size[1]/2 - h/2)
    _clock_right = 0
    _clock_left = bg.size[1] - h
    bg.paste(_clock, (buttons_overlay.size[0], _clock_center))

    w, h = _radar_image.size
    border = 4
    _radar_bottom_right = (int(600-w-border), border)
    bg.paste(_radar_image, _radar_bottom_right)

    bg.paste(buttons_overlay, (0, 0))

    return bg
