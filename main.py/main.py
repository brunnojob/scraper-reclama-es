"""
Script principal do scraper de reclamações de TI
"""

import logging
import time
from typing import List, Dict
from datetime import datetime

from config import SITES_CONFIG, SCRAPING_CONFIG, LOGGING_CONFIG
from database import DatabaseManager
from utils import setup_logging
from scrapers.reclame_aqui_scraper import ReclameAquiScraper
from scrapers.trustpilot_scraper import TrustpilotScraper
from scrapers.generic_scraper import GenericScraper

# Configurar logging
setup_logging(LOGGING_CONFIG['level'], LOGGING_CONFIG['file'])
logger = logging.getLogger(__name__)

class ComplaintsScraper:
    """Classe principal do scraper de reclamações"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.scrapers = {}
        self.setup_scrapers()
    
    def setup_scrapers(self):
        """Configura os scrapers para cada site"""
        for site_name, config in SITES_CONFIG.items():
            if not config['enabled']:
                continue
            
            try:
                if site_name == 'reclame_aqui':
                    self.scrapers[site_name] = ReclameAquiScraper()
                elif site_name == 'trustpilot':
                    self.scrapers[site_name] = TrustpilotScraper()
                else:
                    # Usa scraper genérico para outros sites
                    self.scrapers[site_name] = GenericScraper(
                        site_name=site_name,
                        base_url=config['base_url'],
                        search_url=config.get('search_url')
                    )
                
                logger.info(f"Scraper configurado para {site_name}")
                
            except Exception as e:
                logger.error(f"Erro ao configurar scraper para {site_name}: {e}")
    
    def scrape_site(self, site_name: str, max_pages: int = None) -> List[Dict]:
        """Executa scraping de um site específico"""
        if site_name not in self.scrapers:
            logger.error(f"Scraper não encontrado para {site_name}")
            return []
        
        scraper = self.scrapers[site_name]
        max_pages = max_pages or SCRAPING_CONFIG['max_pages_per_site']
        
        try:
            logger.info(f"Iniciando scraping de {site_name}")
            start_time = time.time()
            
            # Executa scraping
            raw_complaints = scraper.scrape_complaints(max_pages)
            
            # Filtra reclamações relacionadas a TI
            ti_complaints = scraper.filter_ti_complaints(raw_complaints)
            
            # Normaliza dados
            normalized_complaints = []
            for complaint in ti_complaints:
                normalized = scraper.normalize_complaint_data(complaint)
                normalized_complaints.append(normalized)
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Scraping de {site_name} concluído em {duration:.2f}s - {len(normalized_complaints)} reclamações de TI")
            
            return normalized_complaints
            
        except Exception as e:
            logger.error(f"Erro no scraping de {site_name}: {e}")
            return []
        
        finally:
            # Limpar recursos
            try:
                scraper.close()
            except:
                pass
    
    def scrape_all_sites(self) -> Dict[str, List[Dict]]:
        """Executa scraping de todos os sites configurados"""
        results = {}
        
        for site_name in self.scrapers.keys():
            try:
                logger.info(f"Iniciando scraping de {site_name}")
                
                complaints = self.scrape_site(site_name)
                results[site_name] = complaints
                
                # Salva no banco de dados
                saved_count = 0
                for complaint in complaints:
                    if self.db_manager.save_complaint(complaint):
                        saved_count += 1
                
                logger.info(f"{site_name}: {saved_count} reclamações salvas no banco")
                
                # Pausa entre sites
                time.sleep(SCRAPING_CONFIG['delay_between_sites'])
                
            except Exception as e:
                logger.error(f"Erro no scraping de {site_name}: {e}")
                results[site_name] = []
        
        return results
    
    def generate_report(self) -> Dict:
        """Gera relatório do scraping"""
        stats = self.db_manager.get_stats()
        
        # Adiciona informações de tempo
        stats['scraping_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Exporta para CSV
        if self.db_manager.export_to_csv():
            stats['csv_exported'] = True
        
        return stats
    
    def cleanup(self):
        """Limpa recursos utilizados"""
        for scraper in self.scrapers.values():
            try:
                scraper.close()
            except:
                pass

def main():
    """Função principal"""
    scraper = ComplaintsScraper()
    
    try:
        logger.info("=== INICIANDO SCRAPER DE RECLAMAÇÕES DE TI ===")
        
        # Verifica contagem inicial
        initial_count = scraper.db_manager.get_complaints_count()
        logger.info(f"Reclamações no banco antes do scraping: {initial_count}")
        
        # Executa scraping
        results = scraper.scrape_all_sites()
        
        # Gera relatório
        report = scraper.generate_report()
        
        # Exibe resultados
        logger.info("=== RELATÓRIO FINAL ===")
        logger.info(f"Total de reclamações coletadas: {report['total_complaints']}")
        logger.info(f"Score médio de relevância: {report['avg_relevance_score']}")
        
        print("\n=== RESUMO POR SITE ===")
        for site, count in report['by_site'].items():
            print(f"{site}: {count} reclamações")
        
        print("\n=== TOP 5 EMPRESAS COM MAIS RECLAMAÇÕES ===")
        for company, count in list(report['top_companies'].items())[:5]:
            print(f"{company}: {count} reclamações")
        
        logger.info("Scraping concluído com sucesso!")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()