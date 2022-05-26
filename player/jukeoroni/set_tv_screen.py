import os
import subprocess
import logging
from PIL import Image

from player.jukeoroni.clock import Clock
from player.jukeoroni.settings import Settings


LOG = logging.getLogger(__name__)
LOG.setLevel(Settings.GLOBAL_LOGGING_LEVEL)


def set_tv_screen():

    LOG.info('Setting TV background...')

    fbw = int(subprocess.check_output('fbset | grep \'geometry\' | xargs | cut -d \' \' -f2', shell=True))
    fbh = int(subprocess.check_output('fbset | grep \'geometry\' | xargs | cut -d \' \' -f3', shell=True))
    fbd = int(subprocess.check_output('fbset | grep \'geometry\' | xargs | cut -d \' \' -f6', shell=True))

    bg_screen = Image.new(
        mode='RGBA',
        size=(fbw, fbh),
        color=(0, 0, 0, 0)
    )

    clock_size = int(fbh / 2)
    _clock = Clock().get_clock(
        size=clock_size,
        draw_logo=True,
        draw_moon=True,
        draw_moon_phase=True,
        draw_date=True,
        hours=24,
        draw_sun=True,
        square=True
    )
    _clock = _clock.rotate(270, expand=False)

    _clock_center = round(bg_screen.size[1] / 2 - clock_size / 2)

    bg_screen.paste(
        _clock,
        box=(
            int(bg_screen.size[0] / 2) - int(clock_size / 2),
            int(bg_screen.size[1] / 2) - int(clock_size / 2)
        )
    )

    temp_jpg = r'/data/django/jukeoroni/player/static/temp.jpg'
    bg_screen = bg_screen.convert(mode='RGB')
    bg_screen.save(temp_jpg, format='JPEG')

    # https://stackoverflow.com/questions/64279115/editing-a-file-with-root-privileges-from-python
    command = 'echo \'0\' | sudo tee /sys/class/graphics/fbcon/cursor_blink'
    subprocess.call(command, shell=True)

    os.system('fbw="$(fbset | grep \'geometry\' | xargs | cut -d \' \' -f2)"')

    os.system(
        f'convert {temp_jpg}\["${fbw}"x"${fbh}"^\] +flip -strip -define bmp:subtype=RGB565 bmp2:- | tail -c $(( {fbw} * {fbh} * {fbd} / 8 )) > /dev/fb0')

    LOG.info('TV background set successfully.')

    return 0
