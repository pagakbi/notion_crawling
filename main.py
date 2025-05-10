import requests
from bs4 import BeautifulSoup

url = "https://kaist-cs.notion.site/da7b6b2e21b64bc684c69297de57e52f"

response = requests.get(url)

if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    # print(soup)

    title = soup.find_all('h1')[0].text
    print(title)

else : 
    print(response.status_code)

