import os
import tempfile
from io import BytesIO
from PIL import Image, ImageDraw
import selenium.common
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def radar_screenshot(factor=1.0):
    options = selenium.webdriver.firefox.options.Options()
    options.headless = True
    service_log_path = os.path.join(tempfile.gettempdir(), 'geckodriver.log')
    with selenium.webdriver.Firefox(options=options, service_log_path=service_log_path) as driver:
        driver.get('https://meteo.search.ch/prognosis')
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
        root = driver.find_element(By.ID, "mapcontainer")
        png = root.screenshot_as_png
    im = Image.open(BytesIO(png))
    width, height = im.size
    left = 140
    top = 100
    right = width - left
    botton = height - top
    im = im.crop((left, top, right, botton))

    im = im.resize((int(im.size[0] * factor), int(im.size[1] * factor)))

    bg = Image.new(mode='RGB', size=im.size, color=(0, 0, 0))
    mask = Image.new("L", im.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), im.size], 15, fill=255)
    im = Image.composite(im, bg, mask)

    return im
