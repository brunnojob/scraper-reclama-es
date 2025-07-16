"""
Utilitários para o scraper de reclamações
"""

import re
import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime
from fake_useragent import UserAgent
from config import TI_KEYWORDS

logger = logging.getLogger(__name__)

class TextProcessor:
    """Classe para processamento de texto e filtragem de conteúdo"""
    
    def __init__(self):
        self.ti_keywords = [keyword.lower() for keyword in TI_KEYWORDS]
    
    def calculate_ti_relevance(self, text: str) -> Dict:
        """Calcula a relevância do texto para TI baseado nas palavras-chave"""
        if not text:
            return {'score': 0, 'keywords_found': []}
        
        text_lower = text.lower()
        keywords_found = []
        
        for keyword in self.ti_keywords:
            if keyword in text_lower:
                keywords_found.append(keyword)
        
        # Calcula score baseado na quantidade e frequência das palavras-chave
        score = len(keywords_found) * 10
        
        # Bonus para palavras-chave mais específicas
        high_priority_keywords = ['bug', 'falha', 'erro', 'sistema', 'suporte técnico', 'servidor']
        for keyword in keywords_found:
            if keyword in high_priority_keywords:
                score += 5
        
        # Normaliza o score (máximo 100)
        score = min(score, 100)
        
        return {
            'score': score,
            'keywords_found': keywords_found
        }
    
    def is_ti_related(self, text: str, min_score: int = 10) -> bool:
        """Verifica se o texto é relacionado a TI"""
        relevance = self.calculate_ti_relevance(text)
        return relevance['score'] >= min_score
    
    def clean_text(self, text: str) -> str:
        """Limpa e normaliza o texto"""
        if not text:
            return ""
        
        # Remove espaços extras e quebras de linha
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove caracteres especiais problemáticos
        text = re.sub(r'[^\w\s\-.,!?;:()\[\]"\'/@#$%&*+=]', '', text)
        
        return text
    
    def extract_date(self, date_str: str) -> Optional[datetime]:
        """Extrai data de strings em diferentes formatos"""
        if not date_str:
            return None
        
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if pattern == date_patterns[1]:  # YYYY-MM-DD
                        year, month, day = match.groups()
                    else:  # DD/MM/YYYY or DD-MM-YYYY
                        day, month, year = match.groups()
                    
                    return datetime(int(year), int(month), int(day))
                except ValueError:
                    continue
        
        return None
    
    def extract_rating(self, rating_str: str) -> Optional[float]:
        """Extrai rating numérico de strings"""
        if not rating_str:
            return None
        
        # Procura por padrões de rating
        rating_patterns = [
            r'(\d+(?:\.\d+)?)/5',  # X.X/5
            r'(\d+(?:\.\d+)?)/10', # X.X/10
            r'(\d+(?:\.\d+)?)★',   # X.X★
            r'(\d+(?:\.\d+)?)',    # Só número
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, rating_str)
            if match:
                try:
                    rating = float(match.group(1))
                    # Normaliza para escala 0-5
                    if '/10' in rating_str:
                        rating = rating / 2
                    elif rating > 5:
                        rating = rating / 2
                    return min(rating, 5.0)
                except ValueError:
                    continue
        
        return None

class RequestHandler:
    """Classe para gerenciar requisições HTTP com rate limiting e user agents"""
    
    def __init__(self, delay: int = 2, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.ua = UserAgent()
        self.last_request_time = 0
    
    def get_headers(self) -> Dict[str, str]:
        """Retorna headers aleatórios para evitar detecção"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.8,en;q=0.6',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def wait_rate_limit(self):
        """Implementa rate limiting entre requisições"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def random_delay(self, min_delay: int = 1, max_delay: int = 3):
        """Adiciona delay aleatório para parecer mais humano"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

class ScrapingHelper:
    """Classe com métodos auxiliares para scraping"""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Verifica se a URL é válida"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None
    
    @staticmethod
    def get_absolute_url(base_url: str, relative_url: str) -> str:
        """Converte URL relativa para absoluta"""
        if relative_url.startswith('http'):
            return relative_url
        
        if relative_url.startswith('/'):
            return base_url.rstrip('/') + relative_url
        
        return base_url.rstrip('/') + '/' + relative_url
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """Extrai o domínio de uma URL"""
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else url

def setup_logging(level: str = 'INFO', log_file: str = 'scraper.log'):
    """Configura o sistema de logging"""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger.info(f"Sistema de logging configurado - Nível: {level}")