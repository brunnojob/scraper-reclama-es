

import time
import logging
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

from scrapers.base_scraper import BaseScraper
from config import TI_KEYWORDS

logger = logging.getLogger(__name__)

class ReclameAquiScraper(BaseScraper):
    """Scraper para o site Reclame Aqui"""

    def __init__(self):
        super().__init__(
            site_name='reclame_aqui',
            base_url='https://www.reclameaqui.com.br',
            use_selenium=True
        )

    def get_complaint_urls(self, search_terms: List[str]) -> List[str]:
        """Obtém URLs de reclamações do Reclame Aqui"""
        complaint_urls = []

        for term in search_terms[:5]:  # Limita termos de busca
            try:
                search_url = f"{self.base_url}/busca?q={term}"
                logger.info(f"Buscando no Reclame Aqui: {term}")

                soup = self.get_page_content(search_url)
                if not soup:
                    continue


                complaint_links = soup.find_all('a', {'class': 'complaint-card-link'})
                if not complaint_links:
                    # Tenta seletores alternativos
                    complaint_links = soup.find_all('a', href=lambda x: x and '/reclamacao/' in x)

                for link in complaint_links[:10]:  # Limita por termo
                    href = link.get('href')
                    if href:
                        if not href.startswith('http'):
                            href = self.base_url + href
                        complaint_urls.append(href)

                time.sleep(2)

            except Exception as e:
                logger.error(f"Erro ao buscar '{term}' no Reclame Aqui: {e}")
                continue

        return list(set(complaint_urls))  # Remove duplicatas

    def extract_complaint_data(self, soup) -> Dict:

        complaint_data = {}

        try:

            title_element = soup.find('h1', {'class': 'complaint-title'}) or \
                           soup.find('h1', {'data-testid': 'complaint-title'}) or \
                           soup.find('h1')

            complaint_data['title'] = title_element.get_text(strip=True) if title_element else ''


            company_element = soup.find('span', {'class': 'company-name'}) or \
                             soup.find('a', {'class': 'company-link'}) or \
                             soup.find('span', {'data-testid': 'company-name'})

            complaint_data['company_name'] = company_element.get_text(strip=True) if company_element else ''


            date_element = soup.find('time') or \
                          soup.find('span', {'class': 'complaint-date'}) or \
                          soup.find('span', string=lambda text: text and '/' in text)

            complaint_data['complaint_date'] = date_element.get_text(strip=True) if date_element else ''


            description_element = soup.find('div', {'class': 'complaint-text'}) or \
                                soup.find('div', {'data-testid': 'complaint-description'}) or \
                                soup.find('div', {'class': 'complaint-description'})

            complaint_data['description'] = description_element.get_text(strip=True) if description_element else ''

            
            status_element = soup.find('span', {'class': 'status'}) or \
                           soup.find('div', {'class': 'complaint-status'}) or \
                           soup.find('span', string=lambda text: text and any(word in text.lower() for word in ['resolvido', 'não resolvido', 'em análise']))

            complaint_data['status'] = status_element.get_text(strip=True) if status_element else ''

            # Categoria
            category_element = soup.find('span', {'class': 'category'}) or \
                             soup.find('div', {'class': 'complaint-category'})

            complaint_data['category'] = category_element.get_text(strip=True) if category_element else ''

            # Avaliação/Rating
            rating_element = soup.find('span', {'class': 'rating'}) or \
                           soup.find('div', {'class': 'stars'}) or \
                           soup.find('span', string=lambda text: text and ('★' in text or '/5' in text))

            complaint_data['rating'] = rating_element.get_text(strip=True) if rating_element else ''

            # Resposta da empresa
            response_element = soup.find('div', {'class': 'company-response'}) or \
                             soup.find('div', {'data-testid': 'company-response'}) or \
                             soup.find('div', string=lambda text: text and 'resposta da empresa' in text.lower())

            if response_element:
                # Busca o texto da resposta
                response_text = response_element.find_next('div', {'class': 'response-text'})
                complaint_data['company_response'] = response_text.get_text(strip=True) if response_text else response_element.get_text(strip=True)
            else:
                complaint_data['company_response'] = ''

        except Exception as e:
            logger.error(f"Erro ao extrair dados da reclamação: {e}")

        return complaint_data

    def scrape_complaints(self, max_pages: int = 5) -> List[Dict]:
        """Scraping principal do Reclame Aqui"""
        complaints = []

        try:
            # Obtém URLs de reclamações usando palavras-chave de TI
            complaint_urls = self.get_complaint_urls(TI_KEYWORDS[:10])

            logger.info(f"Encontradas {len(complaint_urls)} URLs de reclamações no Reclame Aqui")

            for i, url in enumerate(complaint_urls[:max_pages * 10]):  # Limita total de páginas
                try:
                    logger.info(f"Processando reclamação {i+1}/{len(complaint_urls)}: {url}")

                    soup = self.get_page_content(url)
                    if not soup:
                        continue

                    complaint_data = self.extract_complaint_data(soup)
                    if complaint_data.get('title'):
                        complaint_data['url'] = url
                        complaints.append(complaint_data)

                    # Pausa entre requisições
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Erro ao processar reclamação {url}: {e}")
                    continue

            logger.info(f"Reclame Aqui: {len(complaints)} reclamações coletadas")

        except Exception as e:
            logger.error(f"Erro no scraping do Reclame Aqui: {e}")

        return complaints

    def search_by_category(self, category: str = 'tecnologia') -> List[Dict]:
        """Busca reclamações por categoria específica"""
        complaints = []

        try:
            # URL de categoria de tecnologia
            category_url = f"{self.base_url}/categoria/{category}"

            soup = self.get_page_content(category_url)
            if not soup:
                return complaints

            # Encontra reclamações na página de categoria
            complaint_cards = soup.find_all('div', {'class': 'complaint-card'})

            for card in complaint_cards:
                try:
                    link_element = card.find('a')
                    if link_element and link_element.get('href'):
                        complaint_url = link_element.get('href')
                        if not complaint_url.startswith('http'):
                            complaint_url = self.base_url + complaint_url

                        # Extrai dados da reclamação
                        complaint_soup = self.get_page_content(complaint_url)
                        if complaint_soup:
                            complaint_data = self.extract_complaint_data(complaint_soup)
                            if complaint_data.get('title'):
                                complaint_data['url'] = complaint_url
                                complaints.append(complaint_data)

                        time.sleep(1)

                except Exception as e:
                    logger.error(f"Erro ao processar card de reclamação: {e}")
                    continue

        except Exception as e:
            logger.error(f"Erro ao buscar por categoria {category}: {e}")

        return complaints
