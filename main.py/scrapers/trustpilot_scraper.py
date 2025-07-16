

import time
import logging
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from scrapers.base_scraper import BaseScraper
from config import TI_KEYWORDS

logger = logging.getLogger(__name__)

class TrustpilotScraper(BaseScraper):
    """Scraper para o site Trustpilot"""

    def __init__(self):
        super().__init__(
            site_name='trustpilot',
            base_url='https://www.trustpilot.com',
            use_selenium=True
        )

    def get_complaint_urls(self, search_terms: List[str]) -> List[str]:
        """Obtém URLs de reviews do Trustpilot"""
        review_urls = []

        try:

            tech_category_url = f"{self.base_url}/categories/technology"

            soup = self.get_page_content(tech_category_url)
            if not soup:
                return review_urls


            company_links = soup.find_all('a', {'class': 'company-link'}) or \
                           soup.find_all('a', href=lambda x: x and '/review/' in x)

            for link in company_links[:20]:  # Limita empresas
                href = link.get('href')
                if href:
                    if not href.startswith('http'):
                        href = self.base_url + href
                    review_urls.append(href)

        except Exception as e:
            logger.error(f"Erro ao obter URLs do Trustpilot: {e}")

        return list(set(review_urls))

    def extract_complaint_data(self, soup) -> Dict:
        """Extrai dados de uma review do Trustpilot"""
        complaint_data = {}

        try:

            title_element = soup.find('h2', {'class': 'review-title'}) or \
                           soup.find('h2', {'data-service-review-title-typography': 'true'}) or \
                           soup.find('h2', string=lambda text: text and len(text) > 10)

            complaint_data['title'] = title_element.get_text(strip=True) if title_element else ''


            company_element = soup.find('span', {'class': 'company-name'}) or \
                             soup.find('a', {'class': 'company-link'}) or \
                             soup.find('h1')

            complaint_data['company_name'] = company_element.get_text(strip=True) if company_element else ''

            # Data da review
            date_element = soup.find('time') or \
                          soup.find('span', {'class': 'review-date'}) or \
                          soup.find('div', {'class': 'review-date'})

            complaint_data['complaint_date'] = date_element.get('datetime') or \
                                             date_element.get_text(strip=True) if date_element else ''


            description_element = soup.find('div', {'class': 'review-content'}) or \
                                soup.find('p', {'data-service-review-text-typography': 'true'}) or \
                                soup.find('div', {'class': 'review-text'})

            complaint_data['description'] = description_element.get_text(strip=True) if description_element else ''


            rating_element = soup.find('div', {'class': 'star-rating'}) or \
                           soup.find('div', {'class': 'stars'}) or \
                           soup.find('span', {'class': 'rating'})

            if rating_element:

                rating_text = rating_element.get_text(strip=True)
                if 'star' in rating_text.lower():
                    complaint_data['rating'] = rating_text
                else:
                    # Conta estrelas preenchidas
                    filled_stars = len(rating_element.find_all('span', {'class': 'star-filled'}))
                    if filled_stars > 0:
                        complaint_data['rating'] = f"{filled_stars}/5"


            complaint_data['status'] = 'Publicada'


            complaint_data['category'] = 'Tecnologia'

           
            response_element = soup.find('div', {'class': 'company-response'}) or \
                             soup.find('div', {'class': 'business-response'})

            complaint_data['company_response'] = response_element.get_text(strip=True) if response_element else ''

        except Exception as e:
            logger.error(f"Erro ao extrair dados da review: {e}")

        return complaint_data

    def scrape_company_reviews(self, company_url: str, max_reviews: int = 10) -> List[Dict]:
        """Scraping de reviews de uma empresa específica"""
        reviews = []

        try:
            soup = self.get_page_content(company_url)
            if not soup:
                return reviews

            # Encontra reviews na página
            review_cards = soup.find_all('div', {'class': 'review-card'}) or \
                          soup.find_all('article', {'class': 'review'}) or \
                          soup.find_all('div', {'data-service-review-card-paper': 'true'})

            for i, card in enumerate(review_cards[:max_reviews]):
                try:
                    complaint_data = self.extract_complaint_data(card)
                    if complaint_data.get('title') or complaint_data.get('description'):
                        complaint_data['url'] = company_url
                        reviews.append(complaint_data)

                except Exception as e:
                    logger.error(f"Erro ao processar review {i+1}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Erro ao scraping reviews de {company_url}: {e}")

        return reviews

    def scrape_complaints(self, max_pages: int = 5) -> List[Dict]:
        """Scraping principal do Trustpilot"""
        complaints = []

        try:
            # Obtém URLs de empresas
            company_urls = self.get_complaint_urls(TI_KEYWORDS[:5])

            logger.info(f"Encontradas {len(company_urls)} empresas no Trustpilot")

            for i, url in enumerate(company_urls[:max_pages]):
                try:
                    logger.info(f"Processando empresa {i+1}/{len(company_urls)}: {url}")

                    # Coleta reviews da empresa
                    company_reviews = self.scrape_company_reviews(url, max_reviews=5)
                    complaints.extend(company_reviews)

                    # Pausa entre empresas
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"Erro ao processar empresa {url}: {e}")
                    continue

            logger.info(f"Trustpilot: {len(complaints)} reviews coletadas")

        except Exception as e:
            logger.error(f"Erro no scraping do Trustpilot: {e}")

        return complaints

    def search_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """Busca reviews por palavras-chave específicas"""
        complaints = []

        for keyword in keywords[:3]:  # Limita palavras-chave
            try:
                search_url = f"{self.base_url}/search?query={keyword}"

                soup = self.get_page_content(search_url)
                if not soup:
                    continue

                # Encontra empresas nos resultados da busca
                search_results = soup.find_all('div', {'class': 'search-result'}) or \
                               soup.find_all('a', href=lambda x: x and '/review/' in x)

                for result in search_results[:5]:  # Limita resultados por palavra-chave
                    try:
                        if result.name == 'a':
                            company_url = result.get('href')
                        else:
                            link_element = result.find('a')
                            company_url = link_element.get('href') if link_element else None

                        if company_url:
                            if not company_url.startswith('http'):
                                company_url = self.base_url + company_url

                            # Coleta algumas reviews da empresa
                            company_reviews = self.scrape_company_reviews(company_url, max_reviews=3)
                            complaints.extend(company_reviews)

                    except Exception as e:
                        logger.error(f"Erro ao processar resultado de busca: {e}")
                        continue

                time.sleep(2)

            except Exception as e:
                logger.error(f"Erro ao buscar '{keyword}' no Trustpilot: {e}")
                continue

        return complaints
