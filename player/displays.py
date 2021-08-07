from PIL import Image, ImageDraw
from .clock import Clock
from .radar import Radar


def buttons_img_overlay(labels, stby=False):
    bg = Image.new(mode='RGBA', size=(600, 448), color=(0, 0, 0, 0))
    widget_buttons = Image.new(mode='RGBA', size=(448, 16), color=(255, 255, 255, 128))
    comp_buttons = Image.new(mode='RGBA', size=widget_buttons.size)

    comp_buttons = Image.alpha_composite(comp_buttons, widget_buttons)

    bg.paste(comp_buttons)

    # # bg = Image.new(mode='RGBA', size=(448, 16), color=(80, 80, 80, 0))
    # # buttons_img = Image.new(mode='RGBA', size=(448, 16), color=(80, 80, 80, 64))
    # buttons_draw = ImageDraw.Draw(buttons_img)
    # buttons_draw.text((0, 0), '       {0}               {1}               {2}           {3}'.format(
    #     '    ',  # self.button_4_value,  # Just hide the label for now as the button has no effect
    #     labels[2],
    #     '    ' if stby else labels[1],
    #     '    ' if stby else labels[0],
    # ), fill=(0, 255, 0, 255))

    bg = bg.rotate(90, expand=True)
    # comp_buttons = comp_buttons.rotate(90, expand=False)
    # comp_buttons = comp_buttons.crop((left, top, right, botton))
    # comp_buttons = comp_buttons.crop((0, 0, 0, widget_buttons.size[0]-widget_buttons.size[1]))
    # comp_buttons = comp_buttons.crop((0, 0, 0, widget_buttons.size[0]-widget_buttons.size[1]))

    return bg


def round_resize(img, corner, scaled_by):
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
    _clock = Clock()
    _radar = Radar()
    border = 4
    main_size = 420


class Standby(Layout):

    def get_layout(self, labels):

        buttons_overlay = buttons_img_overlay(labels=labels, stby=True)
        bg = Image.new(mode='RGBA', size=(600, 448), color=(255, 0, 0, 255))
        widget_clock = Image.new(mode='RGBA', size=(self.main_size, self.main_size), color=(0, 0, 0, 0))
        comp_clock = Image.new(mode='RGBA', size=widget_clock.size)

        # clock_size = 448 - 2 * self.border
        clock_size = self.main_size
        _clock = self._clock.get_clock(size=clock_size, draw_logo=True, draw_date=True, hours=24, draw_astral=True)

        comp_clock = Image.alpha_composite(comp_clock, widget_clock)
        comp_clock = Image.alpha_composite(comp_clock, _clock)

        _clock_center = round(bg.size[1]/2 - clock_size/2)
        # _clock_right = 0
        # _clock_left = bg.size[1] - clock_size

        bg.paste(comp_clock, box=(buttons_overlay.size[0] + self.border, _clock_center), mask=comp_clock)

        # _radar_image = self._radar.radar_image
        #
        # if _radar_image is not None:
        #     _radar_image = round_resize(img=_radar_image, corner=40, scaled_by=0.45)
        #     # print(_radar_image.size) yields (151, 205) for now
        #     w, h = _radar_image.size
        #     _radar_bottom_right = (int(600-w-self.border), self.border)
        #     bg.paste(_radar_image, _radar_bottom_right)

        # bg.paste(buttons_overlay, (0, 0))
        # comp_buttons_overlay = Image.new(mode='RGBA', size=(448, 16))
        # comp_buttons_overlay = Image.alpha_composite(comp_buttons_overlay)
        bg.paste(buttons_overlay, (0, 0))

        return bg


class Player(Layout):

    def get_layout(self, labels, cover, artist=None):

        assert isinstance(cover, Image.Image), 'album cover type must be PIL.Image.Image() (not rotated)'
        if artist is None:
            pass
        else:
            print(artist)
            assert isinstance(artist, Image.Image), 'artist cover type must be PIL.Image.Image() (not rotated)'

        buttons_overlay = buttons_img_overlay(labels)
        bg = Image.new(mode='RGB', size=(600, 448), color=(255, 255, 255))

        # cover_size = 448 - 2 * self.border
        cover_size = self.main_size

        cover = cover.rotate(90, expand=True)
        cover = cover.resize((cover_size, cover_size), Image.ANTIALIAS)
        cover = round_resize(img=cover, corner=40, scaled_by=1.0)

        if artist:
            scale_cover_artist = 4
            cover_artist = artist.rotate(90, expand=True)
            cover_artist = cover_artist.resize((round(cover_size/scale_cover_artist), round(cover_size/scale_cover_artist)), Image.ANTIALIAS)
            cover_artist = round_resize(img=cover_artist, corner=20, scaled_by=1.0)

            cover.paste(cover_artist, (round(cover_size - cover_size/scale_cover_artist)-20, 20))

        _cover_center = round(bg.size[1] / 2 - cover_size / 2)
        bg.paste(cover, (buttons_overlay.size[0] + self.border, _cover_center))

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
