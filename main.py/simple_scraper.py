"""
Versão Simplificada do Scraper de Reclamações de TI
Usa apenas bibliotecas padrão do Python (sem dependências externas)
"""

import urllib.request
import urllib.parse
import json
import csv
import time
import re
import sqlite3
from datetime import datetime
from html.parser import HTMLParser
import ssl

# Configuração para ignorar certificados SSL (apenas para testes)
ssl._create_default_https_context = ssl._create_unverified_context

class SimpleHTMLParser(HTMLParser):
    """Parser HTML simples para extrair dados"""
    
    def __init__(self):
        super().__init__()
        self.data = []
        self.current_tag = None
        self.current_attrs = {}
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        self.current_attrs = dict(attrs)
        
    def handle_data(self, data):
        if self.current_tag and data.strip():
            self.data.append({
                'tag': self.current_tag,
                'attrs': self.current_attrs,
                'text': data.strip()
            })
    
    def get_text_by_tag(self, tag):
        """Retorna texto de tags específicas"""
        return [item['text'] for item in self.data if item['tag'] == tag]
    
    def get_text_by_class(self, class_name):
        """Retorna texto de elementos com classe específica"""
        return [item['text'] for item in self.data 
                if 'class' in item['attrs'] and class_name in item['attrs']['class']]

class SimpleScraper:
    """Scraper simplificado usando apenas bibliotecas padrão"""
    
    def __init__(self):
        self.ti_keywords = [
            'sistema', 'bug', 'falha', 'erro', 'lentidão', 'suporte técnico',
            'internet', 'servidor', 'segurança', 'atendimento online', 'plataforma',
            'aplicativo', 'app', 'site', 'website', 'login', 'senha', 'acesso',
            'conexão', 'rede', 'tecnologia', 'digital', 'online', 'software',
            'hardware', 'dados', 'backup', 'vírus', 'malware', 'firewall',
            'database', 'banco de dados', 'API', 'integração', 'sincronização',
            'atualização', 'versão', 'instalação', 'configuração', 'performance',
            'lento', 'travando', 'fora do ar', 'indisponível', 'manutenção',
            'técnico', 'suporte', 'helpdesk', 'TI', 'informática'
        ]
        self.setup_database()
    
    def setup_database(self):
        """Configura o banco de dados SQLite"""
        self.conn = sqlite3.connect('ti_complaints_simple.db')
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_source TEXT NOT NULL,
                company_name TEXT,
                title TEXT,
                description TEXT,
                url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                relevance_score INTEGER
            )
        ''')
        
        self.conn.commit()
        print("Banco de dados configurado com sucesso!")
    
    def get_page_content(self, url):
        """Obtém conteúdo de uma página web"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
                return content
                
        except Exception as e:
            print(f"Erro ao acessar {url}: {e}")
            return None
    
    def calculate_relevance(self, text):
        """Calcula relevância do texto para TI"""
        if not text:
            return 0
        
        text_lower = text.lower()
        score = 0
        keywords_found = []
        
        for keyword in self.ti_keywords:
            if keyword in text_lower:
                score += 10
                keywords_found.append(keyword)
        
        return min(score, 100), keywords_found
    
    def extract_text_content(self, html_content):
        """Extrai texto relevante do HTML"""
        if not html_content:
            return []
        
        # Remove scripts e styles
        html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Extrai texto de tags comuns
        text_patterns = [
            r'<h[1-6][^>]*>(.*?)</h[1-6]>',  # Títulos
            r'<p[^>]*>(.*?)</p>',            # Parágrafos
            r'<div[^>]*>(.*?)</div>',        # Divs
            r'<span[^>]*>(.*?)</span>',      # Spans
        ]
        
        extracted_texts = []
        for pattern in text_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                # Remove tags HTML restantes
                clean_text = re.sub(r'<[^>]+>', '', match).strip()
                if len(clean_text) > 20:  # Apenas textos substanciais
                    extracted_texts.append(clean_text)
        
        return extracted_texts
    
    def scrape_generic_site(self, base_url, site_name, search_terms=None):
        """Scraping genérico para qualquer site"""
        complaints = []
        
        if not search_terms:
            search_terms = self.ti_keywords[:5]  # Usa primeiras 5 palavras-chave
        
        print(f"\nIniciando scraping de {site_name}...")
        
        for term in search_terms:
            try:
                # Tenta diferentes formatos de URL de busca
                search_urls = [
                    f"{base_url}/busca?q={urllib.parse.quote(term)}",
                    f"{base_url}/search?q={urllib.parse.quote(term)}",
                    f"{base_url}/pesquisa?termo={urllib.parse.quote(term)}",
                    f"{base_url}/?s={urllib.parse.quote(term)}",
                ]
                
                for search_url in search_urls:
                    print(f"Tentando: {search_url}")
                    
                    content = self.get_page_content(search_url)
                    if not content:
                        continue
                    
                    # Extrai textos da página
                    texts = self.extract_text_content(content)
                    
                    for text in texts:
                        relevance_score, keywords = self.calculate_relevance(text)
                        
                        if relevance_score >= 20:  # Apenas textos relevantes
                            complaint = {
                                'site_source': site_name,
                                'company_name': self.extract_company_name(text),
                                'title': text[:100] + '...' if len(text) > 100 else text,
                                'description': text,
                                'url': search_url,
                                'relevance_score': relevance_score
                            }
                            
                            complaints.append(complaint)
                            print(f"Encontrada reclamação relevante (score: {relevance_score})")
                    
                    time.sleep(2)  # Pausa entre requisições
                    break  # Se conseguiu acessar, não tenta outras URLs
                
            except Exception as e:
                print(f"Erro ao buscar '{term}' em {site_name}: {e}")
                continue
        
        return complaints
    
    def extract_company_name(self, text):
        """Tenta extrair nome da empresa do texto"""
        # Padrões simples para identificar nomes de empresas
        patterns = [
            r'empresa\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z]+)\s+não\s+resolve',
            r'problema\s+com\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z]+)\s+tem\s+falha',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return "Não identificado"
    
    def save_complaint(self, complaint):
        """Salva reclamação no banco de dados"""
        try:
            cursor = self.conn.cursor()
            
            # Verifica se já existe
            cursor.execute('''
                SELECT id FROM complaints 
                WHERE site_source = ? AND title = ? AND description = ?
            ''', (complaint['site_source'], complaint['title'], complaint['description']))
            
            if cursor.fetchone():
                return False  # Já existe
            
            # Insere nova reclamação
            cursor.execute('''
                INSERT INTO complaints (
                    site_source, company_name, title, description, url, relevance_score
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                complaint['site_source'],
                complaint['company_name'],
                complaint['title'],
                complaint['description'],
                complaint['url'],
                complaint['relevance_score']
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao salvar reclamação: {e}")
            return False
    
    def export_to_csv(self, filename='ti_complaints_simple.csv'):
        """Exporta dados para CSV"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM complaints ORDER BY scraped_at DESC')
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Cabeçalho
                writer.writerow([
                    'ID', 'Site', 'Empresa', 'Título', 'Descrição', 
                    'URL', 'Data Coleta', 'Score Relevância'
                ])
                
                # Dados
                for row in cursor.fetchall():
                    writer.writerow(row)
            
            print(f"Dados exportados para {filename}")
            return True
            
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            return False
    
    def run_scraping(self):
        """Executa o scraping de todos os sites"""
        sites = [
            ('https://www.reclameaqui.com.br', 'Reclame Aqui'),
            ('https://www.consumidor.gov.br', 'Consumidor.gov.br'),
            ('https://www.ebit.com.br', 'Ebit'),
            ('https://www.trustpilot.com', 'Trustpilot'),
            ('https://www.complaintsboard.com', 'ComplaintsBoard'),
            ('https://www.sitejabber.com', 'SiteJabber'),
        ]
        
        total_complaints = 0
        
        for base_url, site_name in sites:
            try:
                complaints = self.scrape_generic_site(base_url, site_name)
                
                saved_count = 0
                for complaint in complaints:
                    if self.save_complaint(complaint):
                        saved_count += 1
                
                print(f"{site_name}: {saved_count} reclamações salvas")
                total_complaints += saved_count
                
                time.sleep(5)  # Pausa entre sites
                
            except Exception as e:
                print(f"Erro no scraping de {site_name}: {e}")
        
        print(f"\n=== SCRAPING CONCLUÍDO ===")
        print(f"Total de reclamações coletadas: {total_complaints}")
        
        # Exporta para CSV
        self.export_to_csv()
        
        # Mostra estatísticas
        self.show_stats()
    
    def show_stats(self):
        """Mostra estatísticas dos dados coletados"""
        cursor = self.conn.cursor()
        
        # Total por site
        cursor.execute('''
            SELECT site_source, COUNT(*) as count 
            FROM complaints 
            GROUP BY site_source
        ''')
        
        print("\n=== ESTATÍSTICAS POR SITE ===")
        for site, count in cursor.fetchall():
            print(f"{site}: {count} reclamações")
        
        # Score médio
        cursor.execute('SELECT AVG(relevance_score) FROM complaints')
        avg_score = cursor.fetchone()[0] or 0
        print(f"\nScore médio de relevância: {avg_score:.2f}")
    
    def close(self):
        """Fecha conexão com banco de dados"""
        if self.conn:
            self.conn.close()

def main():
    """Função principal"""
    print("=== SCRAPER SIMPLIFICADO DE RECLAMAÇÕES DE TI ===")
    print("Versão que usa apenas bibliotecas padrão do Python")
    print("Pressione Ctrl+C para interromper a qualquer momento\n")
    
    scraper = SimpleScraper()
    
    try:
        scraper.run_scraping()
        
    except KeyboardInterrupt:
        print("\nScraping interrompido pelo usuário")
    except Exception as e:
        print(f"Erro durante execução: {e}")
    finally:
        scraper.close()
        print("Scraper finalizado!")

if __name__ == "__main__":
    main()