import os
import time
import tempfile
from io import BytesIO
from PIL import Image, ImageDraw
import selenium.common
import selenium.webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


URL = 'https://meteo.search.ch/prognosis'


def radar_screenshot(factor=1.0):
    options = selenium.webdriver.firefox.options.Options()
    options.headless = True
    service_log_path = os.path.join(tempfile.gettempdir(), 'geckodriver.log')
    with selenium.webdriver.Firefox(options=options, service_log_path=service_log_path) as driver:
        print(f'Opening {URL}')
        driver.get(URL)
        time.sleep(2.0)
        # WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))).click()
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id=\"onetrust-accept-btn-handler\"]"))).click()
        driver.navigate().refresh()
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

    im = im.resize((int(im.size[0] * factor), int(im.size[1] * factor)))

    bg = Image.new(mode='RGB', size=im.size, color=(0, 0, 0))
    mask = Image.new("L", im.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), im.size], 15, fill=255)
    im = Image.composite(im, bg, mask)

    return im
