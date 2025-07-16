

import time
import logging
from typing import List, Dict
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from config import TI_KEYWORDS

logger = logging.getLogger(__name__)

class GenericScraper(BaseScraper):


    def __init__(self, site_name: str, base_url: str, search_url: str = None):
        super().__init__(
            site_name=site_name,
            base_url=base_url,
            use_selenium=False
        )
        self.search_url = search_url or base_url

    def get_complaint_urls(self, search_terms: List[str]) -> List[str]:

        complaint_urls = []

        try:

            if 'consumidor.gov.br' in self.base_url:
                complaint_urls = self._get_consumidor_gov_urls()
            elif 'ebit.com.br' in self.base_url:
                complaint_urls = self._get_ebit_urls()
            elif 'complaintsboard.com' in self.base_url:
                complaint_urls = self._get_complaintsboard_urls()
            elif 'sitejabber.com' in self.base_url:
                complaint_urls = self._get_sitejabber_urls()
            else:
                complaint_urls = self._get_generic_urls()

        except Exception as e:
            logger.error(f"Erro ao obter URLs de {self.site_name}: {e}")

        return complaint_urls

    def _get_consumidor_gov_urls(self) -> List[str]:

        urls = []

        try:

            recent_url = f"{self.base_url}/pages/indicador/relatorio"
            soup = self.get_page_content(recent_url)

            if soup:

                complaint_links = soup.find_all('a', href=lambda x: x and 'reclamacao' in x)

                for link in complaint_links[:15]:
                    href = link.get('href')
                    if href:
                        urls.append(urljoin(self.base_url, href))

        except Exception as e:
            logger.error(f"Erro ao buscar URLs do Consumidor.gov: {e}")

        return urls

    def _get_ebit_urls(self) -> List[str]:

        urls = []

        try:

            reclamations_url = f"{self.base_url}/reclamacoes"
            soup = self.get_page_content(reclamations_url)

            if soup:

                complaint_links = soup.find_all('a', href=lambda x: x and 'reclamacao' in x)

                for link in complaint_links[:15]:
                    href = link.get('href')
                    if href:
                        urls.append(urljoin(self.base_url, href))

        except Exception as e:
            logger.error(f"Erro ao buscar URLs do Ebit: {e}")

        return urls

    def _get_complaintsboard_urls(self) -> List[str]:

        urls = []

        try:

            tech_url = f"{self.base_url}/categories/technology"
            soup = self.get_page_content(tech_url)

            if soup:

                complaint_links = soup.find_all('a', href=lambda x: x and 'complaints' in x)

                for link in complaint_links[:15]:
                    href = link.get('href')
                    if href:
                        urls.append(urljoin(self.base_url, href))

        except Exception as e:
            logger.error(f"Erro ao buscar URLs do ComplaintsBoard: {e}")

        return urls

    def _get_sitejabber_urls(self) -> List[str]:

        urls = []

        try:

            tech_url = f"{self.base_url}/categories/technology"
            soup = self.get_page_content(tech_url)

            if soup:

                review_links = soup.find_all('a', href=lambda x: x and 'reviews' in x)

                for link in review_links[:15]:
                    href = link.get('href')
                    if href:
                        urls.append(urljoin(self.base_url, href))

        except Exception as e:
            logger.error(f"Erro ao buscar URLs do SiteJabber: {e}")

        return urls

    def _get_generic_urls(self) -> List[str]:

        urls = []

        try:
            soup = self.get_page_content(self.search_url)
            if not soup:
                return urls


            potential_links = soup.find_all('a', href=lambda x: x and any(
                keyword in x.lower() for keyword in ['reclamacao', 'complaint', 'review', 'avaliacao']
            ))

            for link in potential_links[:20]:
                href = link.get('href')
                if href:
                    urls.append(urljoin(self.base_url, href))

        except Exception as e:
            logger.error(f"Erro na busca genérica de URLs: {e}")

        return urls

    def extract_complaint_data(self, soup) -> Dict:
        """Extrai dados de forma genérica"""
        complaint_data = {}

        try:

            title_selectors = ['h1', 'h2', '.title', '.complaint-title', '.review-title']
            title_element = None

            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element and len(title_element.get_text(strip=True)) > 5:
                    break

            complaint_data['title'] = title_element.get_text(strip=True) if title_element else ''


            company_selectors = ['.company-name', '.company', '.business-name', 'h1', 'h2']
            company_element = None

            for selector in company_selectors:
                company_element = soup.select_one(selector)
                if company_element and len(company_element.get_text(strip=True)) > 2:
                    break

            complaint_data['company_name'] = company_element.get_text(strip=True) if company_element else ''


            date_element = soup.find('time') or \
                          soup.find(string=lambda text: text and any(sep in text for sep in ['/', '-', '.']) and len(text) < 20)

            if date_element:
                if hasattr(date_element, 'get'):
                    complaint_data['complaint_date'] = date_element.get('datetime') or date_element.get_text(strip=True)
                else:
                    complaint_data['complaint_date'] = str(date_element).strip()
            else:
                complaint_data['complaint_date'] = ''


            description_selectors = ['.description', '.complaint-text', '.review-text', '.content', 'p']
            description_text = ''

            for selector in description_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if len(text) > 50:
                        description_text += text + ' '

            complaint_data['description'] = description_text.strip()


            rating_selectors = ['.rating', '.stars', '.score']
            rating_element = None

            for selector in rating_selectors:
                rating_element = soup.select_one(selector)
                if rating_element:
                    break

            complaint_data['rating'] = rating_element.get_text(strip=True) if rating_element else ''

          
            status_indicators = soup.find_all(string=lambda text: text and any(
                word in text.lower() for word in ['resolvido', 'resolved', 'pendente', 'pending', 'closed', 'open']
            ))

            complaint_data['status'] = status_indicators[0].strip() if status_indicators else 'Não informado'

            # Categoria - tentativa de inferir
            complaint_data['category'] = 'Tecnologia'

            # Resposta da empresa - busca por padrões
            response_selectors = ['.company-response', '.business-response', '.response']
            response_element = None

            for selector in response_selectors:
                response_element = soup.select_one(selector)
                if response_element:
                    break

            complaint_data['company_response'] = response_element.get_text(strip=True) if response_element else ''

        except Exception as e:
            logger.error(f"Erro ao extrair dados genéricos: {e}")

        return complaint_data

    def scrape_complaints(self, max_pages: int = 5) -> List[Dict]:
        """Scraping principal genérico"""
        complaints = []

        try:
            # Obtém URLs de reclamações
            complaint_urls = self.get_complaint_urls(TI_KEYWORDS[:5])

            logger.info(f"Encontradas {len(complaint_urls)} URLs em {self.site_name}")

            for i, url in enumerate(complaint_urls[:max_pages * 5]):
                try:
                    logger.info(f"Processando {i+1}/{len(complaint_urls)}: {url}")

                    soup = self.get_page_content(url)
                    if not soup:
                        continue

                    complaint_data = self.extract_complaint_data(soup)
                    if complaint_data.get('title') or complaint_data.get('description'):
                        complaint_data['url'] = url
                        complaints.append(complaint_data)

                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Erro ao processar {url}: {e}")
                    continue

            logger.info(f"{self.site_name}: {len(complaints)} reclamações coletadas")

        except Exception as e:
            logger.error(f"Erro no scraping de {self.site_name}: {e}")

        return complaints
