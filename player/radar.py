import selenium.webdriver
import selenium.common
from selenium.webdriver.common.by import By
import time
from PIL import Image, ImageDraw
from io import BytesIO
import tempfile
import os


def radar_screenshot(factor=1.0):
    options = selenium.webdriver.firefox.options.Options()
    options.headless = True
    # options.log_path = '/tmp/geckodriver.log'
    # options.service_log_path = '/tmp/geckodriver.log'
    service_log_path = os.path.join(tempfile.gettempdir(), 'geckodriver.log')
    with selenium.webdriver.Firefox(options=options, service_log_path=service_log_path) as driver:
        driver.get('https://meteo.search.ch/prognosis')
        time.sleep(2)
        root = driver.find_element(By.ID, "mapcontainer")
        # root = driver.find_element(By.CLASS, "leaflet-pane leaflet-map-pane")
        # root = driver.find_element_by_class_name("leaflet-pane leaflet-map-pane")
        # root = driver.find_element_by_tag_name('html')
        root.screenshot('/home/pi/test_screenshot.png')
        png = root.screenshot_as_png
    im = Image.open(BytesIO(png))
    width, height = im.size
    left = 140
    top = 100
    right = width - left
    botton = height - top
    im = im.crop((left, top, right, botton))
    print(im.size)
    print(im.size)
    print(im.size)
    print(im.size)
    print(im.size)
    im = im.resize((int(im.size[0] * factor), int(im.size[1] * factor)))
    w, h = im.size
    rect = ImageDraw.Draw(im)
    rect.rounded_rectangle([(0, 0), (w, h)], 20, fill="#000000ff")
    # w, h = im.size
    # rect = Image.new('RGBA', (w, h))
    return im

    # if draw_radar:
    #     radar_bg = Image.new(mode='RGB', size=(448, 152), color=(0, 0, 0))
    #     # new_bg.paste(bg)
    #     # bg = new_bg
    #     # bg_radar = Image.new(mode='RGB', size=(448, 152), color=(0, 0, 0))
    #     factor = 0.25
    #     radar = radar_screenshot()
    #     radar = radar.resize((int(radar.size[0]*factor), int(radar.size[1]*factor)))
    #     radar_size = radar.size
    #     radar_bg.paste(radar, (0, 0))
    #     radar_bg = radar_bg.rotate(90, expand=False)
    #     # radar_bg = radar_bg.rotate(90, expand=False)
    #     bg.paste(radar_bg, (0, 0))
    #     # bg =

# radar_screenshot()
