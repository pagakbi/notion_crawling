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
# driver = webdriver.Chrome() 

url = "https://kaist-cs.notion.site/da7b6b2e21b64bc684c69297de57e52f"
driver.get(url)

time.sleep(5)

elements = driver.find_elements(By.CLASS_NAME, "notion-selectable notion-quote-block")
# elements = driver.find_elements(By.CLASS_NAME, "notion-selectable notion-page-block notion-collection-item")

print(elements)

time.sleep(10)