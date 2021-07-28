from PIL import Image, ImageDraw
from .clock import clock
from .radar import radar_screenshot


def buttons_img_overlay(labels):
    buttons_img = Image.new(mode='RGB', size=(448, 12), color=(0, 0, 0))
    buttons_draw = ImageDraw.Draw(buttons_img)
    buttons_draw.text((0, 0), '       {0}               {1}               {2}           {3}'.format(
        labels[4],
        labels[3],
        labels[2],
        labels[1],
    ), fill=(255, 255, 255))

    return buttons_img


def standby(labels):
    _clock = clock(draw_logo=True, draw_date=True, hours=24, draw_astral=True)
    _radar_screenshot = radar_screenshot(factor=0.45).rotate(90, expand=True)

    buttons_overlay = buttons_img_overlay(labels)
    bg = Image.new(mode='RGB', size=(600, 448), color=(0, 0, 0))

    bg.paste(buttons_overlay, (0, 0))

    return bg
