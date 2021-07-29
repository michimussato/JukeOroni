from PIL import Image, ImageDraw
from .clock import Clock
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


def round_resize(img, corner, scaled_by):
    """
    #Resizes an image and keeps aspect ratio. Set mywidth to the desired with in pixels.

    import PIL
    from PIL import Image

    mywidth = 300

    img = Image.open('someimage.jpg')
    wpercent = (mywidth/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((mywidth,hsize), PIL.Image.ANTIALIAS)
    img.save('resized.jpg')
    """
    if img is None:
        return None
    w, h = img.size
    img = img.resize((round(w * scaled_by), round(h * scaled_by)))
    bg = Image.new(mode='RGB', size=img.size, color=(0, 0, 0))
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], corner, fill=255)
    img = Image.composite(img, bg, mask)
    return img


class Layout:
    # Base class so that all subclasses
    # use the same objects (no multiple
    # threads)
    _clock = Clock()
    _radar = Radar()
    border = 4
    main_size = 420


class Standby(Layout):

    def get_layout(self, labels):

        buttons_overlay = buttons_img_overlay(labels)
        bg = Image.new(mode='RGB', size=(600, 448), color=(0, 0, 0))

        # clock_size = 448 - 2 * self.border
        clock_size = self.main_size
        _clock = self._clock.get_clock(size=clock_size, draw_logo=True, draw_date=True, hours=24, draw_astral=True)

        _clock_center = round(bg.size[1]/2 - clock_size/2)
        # _clock_right = 0
        # _clock_left = bg.size[1] - clock_size
        bg.paste(_clock, (buttons_overlay.size[0] + self.border, _clock_center))

        _radar_image = self._radar.radar_image

        if _radar_image is not None:
            _radar_image = round_resize(img=_radar_image, corner=40, scaled_by=0.45)
            # print(_radar_image.size) yields (151, 205) for now
            w, h = _radar_image.size
            _radar_bottom_right = (int(600-w-self.border), self.border)
            bg.paste(_radar_image, _radar_bottom_right)

        bg.paste(buttons_overlay, (0, 0))

        return bg


class Player(Layout):

    def get_layout(self, labels, cover):

        buttons_overlay = buttons_img_overlay(labels)
        bg = Image.new(mode='RGB', size=(600, 448), color=(0, 0, 0))

        # cover_size = 448 - 2 * self.border
        cover_size = self.main_size
        _cover = Image.open(cover).rotate(90, expand=True)
        _cover = _cover.resize((cover_size, cover_size), Image.ANTIALIAS)
        _cover = round_resize(img=_cover, corner=40, scaled_by=1.0)

        _cover_center = round(bg.size[1] / 2 - cover_size / 2)
        bg.paste(_cover, (buttons_overlay.size[0] + self.border, _cover_center))

        clock_size = 151
        _clock = self._clock.get_clock(size=clock_size, draw_logo=False, draw_date=False, hours=24, draw_astral=True)
        _clock_bottom_left_centered = (int(600 - clock_size - self.border),
                                       int(228 + 228/2 + round(self.border/2) - round(clock_size/2)))
        _clock_bottom_left = (int(600 - clock_size - self.border),
                              int(448 - clock_size - self.border))

        bg.paste(_clock, _clock_bottom_left_centered)

        _radar_image = self._radar.radar_image

        if _radar_image is not None:
            _radar_image = round_resize(img=_radar_image, corner=40, scaled_by=0.45)
            # print(_radar_image.size) yields (151, 205) for now
            w, h = _radar_image.size
            border = 4
            _radar_bottom_right = (int(600 - w - border), border)
            bg.paste(_radar_image, _radar_bottom_right)

        bg.paste(buttons_overlay, (0, 0))

        return bg


# TODO
class Radio(Layout):

    def get_layout(self, labels, cover):
        pass
