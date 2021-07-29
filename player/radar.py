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

    def __init__(self):
        super().__init__()

        self._placeholder = Image.new(mode='RGB', size=(336, 456), color=(128, 128, 128))
        self.radar_image = self._placeholder
        self.radar_thread = _RadarThread(target=self._radar_task)

    def _radar_task(self):
        while True:
            print('Updating radar image in background...')
            self.radar_image = self._radar_screenshot()
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
            # will result in size (456, 336) for now
            return im.rotate(90, expand=True)

        except Exception as err:
            print(err)
            return self._placeholder
