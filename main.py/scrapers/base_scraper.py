

import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import requests
from bs4 import BeautifulSoup

from utils import TextProcessor, RequestHandler, ScrapingHelper
from config import SCRAPING_CONFIG

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Classe base para todos os scrapers de sites"""

    def __init__(self, site_name: str, base_url: str, use_selenium: bool = False):
        self.site_name = site_name
        self.base_url = base_url
        self.use_selenium = use_selenium
        self.text_processor = TextProcessor()
        self.request_handler = RequestHandler(
            delay=SCRAPING_CONFIG['delay_between_requests'],
            max_retries=SCRAPING_CONFIG['max_retries']
        )
        self.driver = None
        self.session = requests.Session()

        if use_selenium:
            self.setup_selenium()

    def setup_selenium(self):

        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info(f"Driver Selenium configurado para {self.site_name}")

        except Exception as e:
            logger.error(f"Erro ao configurar Selenium para {self.site_name}: {e}")
            raise

    def get_page_content(self, url: str, use_selenium: bool = None) -> Optional[BeautifulSoup]:

        if use_selenium is None:
            use_selenium = self.use_selenium

        try:
            self.request_handler.wait_rate_limit()

            if use_selenium and self.driver:
                self.driver.get(url)
                time.sleep(2)


                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except:
                    pass

                html_content = self.driver.page_source
                return BeautifulSoup(html_content, 'html.parser')

            else:
                headers = self.request_handler.get_headers()
                response = self.session.get(url, headers=headers, timeout=SCRAPING_CONFIG['timeout'])
                response.raise_for_status()

                return BeautifulSoup(response.content, 'html.parser')

        except Exception as e:
            logger.error(f"Erro ao obter conteúdo de {url}: {e}")
            return None

    def close(self):
        """Fecha recursos utilizados"""
        if self.driver:
            self.driver.quit()
        self.session.close()

    @abstractmethod
    def extract_complaint_data(self, complaint_element) -> Dict:

        pass

    @abstractmethod
    def get_complaint_urls(self, search_terms: List[str]) -> List[str]:

        pass

    @abstractmethod
    def scrape_complaints(self, max_pages: int = 5) -> List[Dict]:

        pass

    def filter_ti_complaints(self, complaints: List[Dict]) -> List[Dict]:

        filtered_complaints = []

        for complaint in complaints:

            text_to_analyze = f"{complaint.get('title', '')} {complaint.get('description', '')}"

            if self.text_processor.is_ti_related(text_to_analyze):
                relevance = self.text_processor.calculate_ti_relevance(text_to_analyze)
                complaint['ti_keywords'] = ','.join(relevance['keywords_found'])
                complaint['relevance_score'] = relevance['score']
                complaint['site_source'] = self.site_name

                filtered_complaints.append(complaint)

        logger.info(f"{self.site_name}: {len(filtered_complaints)} reclamações de TI encontradas de {len(complaints)} total")
        return filtered_complaints

    def normalize_complaint_data(self, complaint: Dict) -> Dict:
       
        return {
            'site_source': self.site_name,
            'company_name': self.text_processor.clean_text(complaint.get('company_name', '')),
            'complaint_date': self.text_processor.extract_date(complaint.get('complaint_date', '')),
            'title': self.text_processor.clean_text(complaint.get('title', '')),
            'description': self.text_processor.clean_text(complaint.get('description', '')),
            'category': self.text_processor.clean_text(complaint.get('category', '')),
            'rating': self.text_processor.extract_rating(complaint.get('rating', '')),
            'status': self.text_processor.clean_text(complaint.get('status', '')),
            'company_response': self.text_processor.clean_text(complaint.get('company_response', '')),
            'url': complaint.get('url', ''),
            'ti_keywords': complaint.get('ti_keywords', ''),
            'relevance_score': complaint.get('relevance_score', 0)
        }
