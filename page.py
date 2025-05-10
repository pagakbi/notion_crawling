# 단일 페이지 크롤링

url = "https://kaist-cs.notion.site/2025-1eda15b64af280758dafd820810aab06"

# selenium의 webdriver를 사용하기 위한 import
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# from selenium.webdriver.common.keys import Keys

import time

options = Options()
options.add_argument("--start-maximized")  # 전체화면

driver = webdriver.Chrome(options=options)

driver.get(url)
time.sleep(5)

data = {}

title_element = driver.find_elements(By.TAG_NAME, "h1")[0]
title = title_element.text
data["title"] = title

date_element = driver.find_elements(By.CSS_SELECTOR, "#notion-app > div > div:nth-child(1) > div > div:nth-child(1) > main > div > div > div.whenContentEditable > div > div.layout-content.layout-content-with-divider > div > div")[0]
date = date_element.text
date = date.split("\n")
start = date[1]
finish = date[3]
data["start"] = start
data["finish"] = finish

contents_element = driver.find_elements(By.CLASS_NAME, "notion-page-content")[0]
contents = contents_element.text

images = contents_element.find_elements(By.TAG_NAME, "img")
images_uri = []
for image in images:
    uri = image.get_attribute("src")
    if "https://kaist-cs.notion.site/image/" in uri:
        images_uri.append(uri)

data["contents"] = contents
data["images"] = images_uri

print("Title:", title)
print("Start Date:", start)
print("Finish Date:", finish)
print("Contents:", contents)
print("Images:", images_uri)
print(data)

# time.sleep(10)

