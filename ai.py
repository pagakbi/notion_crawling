import time
import json
import os
from datetime import datetime
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class NotionCrawler:
    def __init__(self, base_url, output_folder="notion_data"):
        """
        노션 크롤러 초기화
        
        Args:
            base_url (str): 크롤링할 노션 페이지의 기본 URL
            output_folder (str): 크롤링한 데이터를 저장할 폴더 경로
        """
        self.base_url = base_url
        self.output_folder = output_folder
        
        # 출력 폴더가 없으면 생성
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 헤드리스 모드
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # WebDriver 초기화
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
    
    def __del__(self):
        """크롤러 종료 시 WebDriver 종료"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def get_page_content(self, url):
        """
        URL에서 페이지 내용 가져오기
        
        Args:
            url (str): 가져올 페이지의 URL
            
        Returns:
            BeautifulSoup: 페이지 내용의 BeautifulSoup 객체
        """
        try:
            self.driver.get(url)
            
            # 페이지 로딩 대기
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".notion-page-content"))
            )
            
            # 페이지가 완전히 로드될 때까지 추가 대기
            time.sleep(3)
            
            # 페이지 스크롤
            self.scroll_to_bottom()
            
            # HTML 파싱
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            return soup
        
        except Exception as e:
            print(f"Error loading page {url}: {e}")
            return None
    
    def scroll_to_bottom(self):
        """페이지를 끝까지 스크롤하여 모든 콘텐츠 로드"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # 페이지 끝으로 스크롤
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # 새 콘텐츠 로드 대기
            time.sleep(2)
            
            # 새 스크롤 높이 계산
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # 더 이상 스크롤할 내용이 없으면 종료
            if new_height == last_height:
                break
                
            last_height = new_height
    
    def extract_notice_links(self, soup):
        """
        메인 페이지에서 공지사항 링크 추출
        
        Args:
            soup (BeautifulSoup): 메인 페이지의 BeautifulSoup 객체
            
        Returns:
            list: 공지사항 링크 및 제목 목록
        """
        notice_links = []
        
        # 노션 페이지의 링크 찾기
        # 노션 테이블의 행 찾기 (클래스명은 실제 페이지 구조에 따라 달라질 수 있음)
        rows = soup.select(".notion-collection-item")
        
        if not rows:
            # 다른 선택자 시도
            rows = soup.select(".notion-selectable.notion-page-block")
        
        if not rows:
            # 또 다른 선택자 시도
            rows = soup.select("a[href*='/']")
        
        for row in rows:
            # 링크 요소 찾기
            link_elem = row.find("a") or row
            
            if hasattr(link_elem, 'get') and link_elem.get("href"):
                link = link_elem.get("href")
                
                # 상대 URL을 절대 URL로 변환
                if link.startswith("/"):
                    link = urljoin(self.base_url, link)
                
                # 제목 추출
                title_elem = row.select_one(".notion-page-block-title") or row
                title = title_elem.get_text(strip=True) if hasattr(title_elem, 'get_text') else "No Title"
                
                notice_links.append({
                    "url": link,
                    "title": title
                })
        
        return notice_links
    
    def extract_notice_content(self, soup, title):
        """
        공지사항 페이지에서 내용 추출
        
        Args:
            soup (BeautifulSoup): 공지사항 페이지의 BeautifulSoup 객체
            title (str): 공지사항 제목
            
        Returns:
            dict: 공지사항 내용
        """
        try:
            # 공지 내용 컨테이너 찾기
            content_container = soup.select_one(".notion-page-content")
            
            if not content_container:
                content_container = soup.select_one(".notion-scroller")
            
            if not content_container:
                content_container = soup
            
            # 텍스트 블록 추출
            text_blocks = content_container.select(".notion-text-block")
            content_text = "\n\n".join([block.get_text(strip=True) for block in text_blocks if block.get_text(strip=True)])
            
            # 이미지 추출
            images = content_container.select("img.notion-image-block")
            image_urls = [img.get("src") for img in images if img.get("src")]
            
            # 날짜 정보 찾기 (노션 페이지의 구조에 따라 다양한 선택자 시도)
            date_elem = soup.select_one(".notion-property-date")
            date_str = date_elem.get_text(strip=True) if date_elem else "No date"
            
            notice_data = {
                "title": title,
                "date": date_str,
                "content": content_text,
                "image_urls": image_urls,
                "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            return notice_data
            
        except Exception as e:
            print(f"Error extracting content: {e}")
            return {
                "title": title,
                "content": "Error extracting content",
                "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def crawl_notices(self):
        """모든 공지사항 크롤링"""
        try:
            # 메인 페이지에서 공지사항 링크 추출
            main_soup = self.get_page_content(self.base_url)
            if not main_soup:
                print("Failed to load main page")
                return
            
            notice_links = self.extract_notice_links(main_soup)
            
            if not notice_links:
                print("No notice links found")
                return
            
            print(f"Found {len(notice_links)} notices")
            
            all_notices = []
            
            # 각 공지사항 페이지 크롤링
            for i, notice in enumerate(notice_links):
                print(f"Crawling notice {i+1}/{len(notice_links)}: {notice['title']}")
                
                notice_soup = self.get_page_content(notice['url'])
                if not notice_soup:
                    print(f"Failed to load notice page: {notice['url']}")
                    continue
                
                notice_data = self.extract_notice_content(notice_soup, notice['title'])
                notice_data["url"] = notice['url']
                
                all_notices.append(notice_data)
                
                # JSON 파일로 저장
                filename = f"{self.output_folder}/notice_{i+1}_{notice_data['title'].replace(' ', '_')[:30]}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(notice_data, f, ensure_ascii=False, indent=2)
                
                print(f"Saved to {filename}")
                
                # 서버 부하 방지를 위해 대기
                time.sleep(2)
            
            # 모든 공지사항을 하나의 JSON 파일로 저장
            with open(f"{self.output_folder}/all_notices.json", "w", encoding="utf-8") as f:
                json.dump(all_notices, f, ensure_ascii=False, indent=2)
            
            print(f"All notices saved to {self.output_folder}/all_notices.json")
            
            return all_notices
            
        except Exception as e:
            print(f"Error during crawling: {e}")
            return None


if __name__ == "__main__":
    # KAIST-CS 노션 페이지 URL
    base_url = "https://kaist-cs.notion.site/da7b6b2e21b64bc684c69297de57e52f"
    
    # 크롤러 생성 및 실행
    crawler = NotionCrawler(base_url)
    notices = crawler.crawl_notices()
    
    print(f"Crawled {len(notices) if notices else 0} notices in total")