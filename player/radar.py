import selenium.webdriver
import selenium.common
from selenium.webdriver.common.by import By
import time
from PIL import Image
from io import BytesIO
import tempfile
import os


def radar_screenshot():
    options = selenium.webdriver.firefox.options.Options()
    options.headless = True
    # options.log_path = '/tmp/geckodriver.log'
    # options.service_log_path = '/tmp/geckodriver.log'
    service_log_path = os.path.join(tempfile.gettempdir(), 'geckodriver.log')
    with selenium.webdriver.Firefox(options=options, service_log_path='/tmp/geckodriver.log') as driver:
        driver.get('https://meteo.search.ch/prognosis')
        time.sleep(2)
        root = driver.find_element(By.ID, "mapcontainer")
        # root = driver.find_element(By.CLASS, "leaflet-pane leaflet-map-pane")
        # root = driver.find_element_by_class_name("leaflet-pane leaflet-map-pane")
        # root = driver.find_element_by_tag_name('html')
        # root.screenshot('screenshot.png')
        png = root.screenshot_as_png
    im = Image.open(BytesIO(png))
    print(im.size)
    return im

# radar_screenshot()
