import os
import time
import threading
import tempfile
from io import BytesIO
from PIL import Image, ImageDraw
import selenium.common
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


URL = 'https://meteo.search.ch/prognosis'


class _RadarThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'Radar Thread'
        self.daemon = False
        self.start()


class Radar(object):
    RADAR_UPDATE_INTERVAL = 5  # in minutes
    URL = r'https://meteo.search.ch/prognosis'
    DEFAULT_IMAGE = r'/data/django/jukeoroni/player/static/no-interent-connection.png'

    def __init__(self, size_factor=1.0):
        super().__init__()

        self.radar_image = Image.open(self.DEFAULT_IMAGE)
        self.size_factor = size_factor
        self.radar_thread = _RadarThread(target=self._radar_task)
        # self.default_image = Image.open(self.DEFAULT_IMAGE)

    def start(self):
        self.radar_thread.start()

    def image(self, scaled_by=1.0):
        ret = self.radar_image.resize(
            int(self.size[0] * scaled_by),
            int(self.size[1] * scaled_by)
        )
        return ret

    @property
    def size(self):
        return self.radar_image.size

    def _radar_task(self):
        while True:
            print('Updating radar image in background...')
            radar = self._radar_screenshot()
            self.radar_image = radar.rotate(90, expand=True)
            print('Radar image updated.')
            time.sleep(self.RADAR_UPDATE_INTERVAL*60.0)

    def _radar_screenshot(self):
        try:
            options = selenium.webdriver.firefox.options.Options()
            options.headless = True
            service_log_path = os.path.join(tempfile.gettempdir(), 'geckodriver.log')
            with selenium.webdriver.Firefox(options=options, service_log_path=service_log_path) as driver:
                print(f'Opening {self.URL}')
                driver.get(self.URL)
                time.sleep(2.0)
                # WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
                WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"onetrust-accept-btn-handler\"]"))).click()
                driver.refresh()
                time.sleep(5.0)
                # root = driver.find_element(By.ID, "mapcontainer")
                root = driver.find_element(By.XPATH, "//*[@id=\"mapcontainer\"]")
                png = root.screenshot_as_png
            im = Image.open(BytesIO(png))
            width, height = im.size
            left = 140
            top = 100
            right = width - left
            botton = height - top
            im = im.crop((left, top, right, botton))

            # TODO: round edges... will come later again
            # bg = Image.new(mode='RGB', size=im.size, color=(0, 0, 0))
            # mask = Image.new("L", im.size, 0)
            # draw = ImageDraw.Draw(mask)
            # draw.rounded_rectangle([(0, 0), im.size], 15, fill=255)
            # im = Image.composite(im, bg, mask)
        except Exception as err:
            print(err)
            im = self.radar_image = Image.open(self.DEFAULT_IMAGE)

        return im
