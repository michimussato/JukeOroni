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
from player.jukeoroni.settings import RADAR_UPDATE_INTERVAL


class _RadarThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = 'Radar Thread'
        self.daemon = False
        # self.start()


class Radar(object):
    # RADAR_UPDATE_INTERVAL = 5  # in minutes
    URL = r'https://meteo.search.ch/prognosis'

    # https://de.sat24.com/de/freeimages
    # https://de.sat24.com/image?type=visual&region=EU
    # https://de.sat24.com/image?type=rainTMC&region=EU
    # https://api.sat24.com/mostrecent/EU/rainTMC
    # https://de.sat24.com/image?type=visual&region=alps
    # https://de.sat24.com/image?type=rainTMC&region=alps
    # https://api.sat24.com/mostrecent/ALPS/rainTMC

    # https://www.meteoschweiz.admin.ch/product/output/satellite/cloud-cover/version__20210730_1138/VLSN84.LSSW_20210730_1115.jpg
    # https://www.meteoschweiz.admin.ch/product/output/cosmo/wind/10m/forecast/version__20210730_1142/web_c1e_ch_ctrl-web_uv10m_kmh_20210731_2300.png

    # import urllib.request
    # img = io.BytesIO(urllib.request.urlopen(image_file_url).read())
    # cover = Image.open(img)

    # https://zoom.earth/#view=46.51,8.171,7z/date=2021-07-30,10:00,+2  https://zoom.earth/#view=46.51,8.171,7z

    def __init__(self):
        super().__init__()

        self.on = False

        # Non-Picklable objects as Image.Image()
        # must use Thread (shared memory)
        # to use multiprocessing, we could save the resulting
        # radar images to disk and read it in the main thread
        # Thread is okay for now
        self._placeholder = Image.new(mode='RGB', size=(336, 456), color=(128, 128, 128))
        self.radar_image = self._placeholder
        # maybe we need to pass the image here because of multiprocessing not
        # sharing memory...not know yet...indeed. need syncmanager
        self.radar_thread = None

    def start(self):
        self.on = True
        self.radar_thread = _RadarThread(target=self._radar_task)
        self.radar_thread.start()

    def stop(self):
        self.on = False
        self.radar_thread.join()
        self.radar_thread = None

    def _radar_task(self):
        update_interval = RADAR_UPDATE_INTERVAL*60.0
        _waited = None
        while self.on:
            if _waited is None or _waited % update_interval == 0:
                _waited = 0
                print('Updating radar image in background...')
                self.radar_image = self._radar_screenshot()
                print('Radar image updated.')

            print(f'waited {_waited}')
            time.sleep(1.0)
            _waited += 1

    def _radar_screenshot(self):
        try:
            options = selenium.webdriver.firefox.options.Options()
            options.headless = True
            service_log_path = os.path.join(tempfile.gettempdir(), 'geckodriver.log')
            with selenium.webdriver.Firefox(options=options, service_log_path=service_log_path) as driver:
                # print(f'Opening {self.URL}')
                driver.get(self.URL)
                time.sleep(2.0)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"onetrust-accept-btn-handler\"]"))).click()
                driver.refresh()
                time.sleep(5.0)
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
