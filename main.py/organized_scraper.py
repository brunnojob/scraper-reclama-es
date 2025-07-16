"""
Scraper Organizado de Reclamações de TI
Versão com pastas separadas e configuração externa
"""

import os
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

# Configuração SSL
ssl._create_default_https_context = ssl._create_unverified_context

class OrganizedScraper:
    """Scraper organizado com sistema de pastas"""
    
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
            'técnico', 'suporte', 'helpdesk', 'TI', 'informática', 'crash',
            'timeout', 'loading', 'carregamento', 'freeze', 'trava'
        ]
        
        self.setup_directories()
        self.setup_database()
        self.sites_config = self.load_sites_config()
    
    def setup_directories(self):
        """Cria estrutura de pastas organizadas"""
        directories = [
            'sites_data',
            'sites_data/reclame_aqui',
            'sites_data/consumidor_gov',
            'sites_data/ebit',
            'sites_data/trustpilot',
            'sites_data/complaints_board',
            'sites_data/sitejabber',
            'problems_found',
            'problems_found/critical',
            'problems_found/high',
            'problems_found/medium',
            'problems_found/low',
            'reports',
            'logs'
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Pasta criada: {directory}")
    
    def load_sites_config(self):
        """Carrega configuração de sites do arquivo txt"""
        sites = {}
        
        if not os.path.exists('sites_config.txt'):
            print("Arquivo sites_config.txt não encontrado!")
            return sites
        
        try:
            with open('sites_config.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            name = parts[0].strip()
                            sites[name] = {
                                'url_base': parts[1].strip(),
                                'url_busca': parts[2].strip(),
                                'ativo': parts[3].strip().lower() == 'sim',
                                'usa_selenium': parts[4].strip().lower() == 'sim' if len(parts) > 4 else False
                            }
            
            print(f"Configuração carregada: {len(sites)} sites encontrados")
            active_sites = sum(1 for site in sites.values() if site['ativo'])
            print(f"Sites ativos: {active_sites}")
            
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
        
        return sites
    
    def setup_database(self):
        """Configura banco de dados"""
        self.conn = sqlite3.connect('organized_complaints.db')
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_source TEXT NOT NULL,
                company_name TEXT,
                title TEXT,
                description TEXT,
                problem_category TEXT,
                severity_level TEXT,
                url TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                relevance_score INTEGER,
                keywords_found TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site_name TEXT,
                complaints_found INTEGER,
                execution_time REAL,
                success_rate REAL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print("Banco de dados configurado!")
    
    def get_page_content(self, url):
        """Obtém conteúdo de uma página"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
                return content
                
        except Exception as e:
            print(f"Erro ao acessar {url}: {e}")
            return None
    
    def categorize_problem(self, text, keywords_found):
        """Categoriza o problema encontrado"""
        text_lower = text.lower()
        
        # Problemas críticos
        critical_keywords = ['fora do ar', 'indisponível', 'crash', 'perda de dados', 'hack', 'vírus', 'malware']
        if any(keyword in text_lower for keyword in critical_keywords):
            return 'critical'
        
        # Problemas altos
        high_keywords = ['bug', 'falha', 'erro', 'não funciona', 'travando', 'freeze']
        if any(keyword in text_lower for keyword in high_keywords):
            return 'high'
        
        # Problemas médios
        medium_keywords = ['lentidão', 'lento', 'demora', 'timeout', 'loading']
        if any(keyword in text_lower for keyword in medium_keywords):
            return 'medium'
        
        # Problemas baixos
        return 'low'
    
    def calculate_relevance(self, text):
        """Calcula relevância e encontra palavras-chave"""
        if not text:
            return 0, []
        
        text_lower = text.lower()
        score = 0
        keywords_found = []
        
        for keyword in self.ti_keywords:
            if keyword in text_lower:
                score += 10
                keywords_found.append(keyword)
                
                # Bonus para palavras críticas
                if keyword in ['bug', 'falha', 'erro', 'crash', 'fora do ar']:
                    score += 15
        
        return min(score, 100), keywords_found
    
    def extract_text_content(self, html_content):
        """Extrai texto do HTML"""
        if not html_content:
            return []
        
        # Remove scripts e styles
        html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Extrai textos
        text_patterns = [
            r'<h[1-6][^>]*>(.*?)</h[1-6]>',
            r'<p[^>]*>(.*?)</p>',
            r'<div[^>]*class="[^"]*complaint[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*review[^"]*"[^>]*>(.*?)</div>',
            r'<span[^>]*>(.*?)</span>',
        ]
        
        extracted_texts = []
        for pattern in text_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                clean_text = re.sub(r'<[^>]+>', '', match).strip()
                if len(clean_text) > 30:
                    extracted_texts.append(clean_text)
        
        return extracted_texts
    
    def save_site_data(self, site_name, complaints):
        """Salva dados específicos do site em pasta própria"""
        site_folder = f'sites_data/{site_name}'
        
        # Arquivo JSON com dados brutos
        json_file = f'{site_folder}/{site_name}_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(complaints, f, ensure_ascii=False, indent=2)
        
        # Arquivo CSV resumido
        csv_file = f'{site_folder}/{site_name}_summary.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Empresa', 'Título', 'Categoria', 'Severidade', 'Score', 'Palavras-chave'])
            
            for complaint in complaints:
                writer.writerow([
                    complaint.get('company_name', ''),
                    complaint.get('title', '')[:100],
                    complaint.get('problem_category', ''),
                    complaint.get('severity_level', ''),
                    complaint.get('relevance_score', 0),
                    complaint.get('keywords_found', '')
                ])
        
        print(f"Dados do {site_name} salvos em: {site_folder}")
    
    def save_problems_by_severity(self, complaints):
        """Salva problemas organizados por severidade"""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for complaint in complaints:
            severity = complaint.get('severity_level', 'low')
            severity_counts[severity] += 1
            
            # Salva em arquivo específico da severidade
            severity_file = f'problems_found/{severity}/{severity}_problems.txt'
            
            with open(severity_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"SITE: {complaint.get('site_source', '')}\n")
                f.write(f"EMPRESA: {complaint.get('company_name', '')}\n")
                f.write(f"TÍTULO: {complaint.get('title', '')}\n")
                f.write(f"PROBLEMA: {complaint.get('description', '')[:200]}...\n")
                f.write(f"PALAVRAS-CHAVE: {complaint.get('keywords_found', '')}\n")
                f.write(f"SCORE: {complaint.get('relevance_score', 0)}\n")
                f.write(f"DATA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Salva resumo de severidade
        summary_file = 'problems_found/severity_summary.txt'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("RESUMO DE PROBLEMAS POR SEVERIDADE\n")
            f.write("="*40 + "\n\n")
            f.write(f"🔴 CRÍTICOS: {severity_counts['critical']}\n")
            f.write(f"🟠 ALTOS: {severity_counts['high']}\n")
            f.write(f"🟡 MÉDIOS: {severity_counts['medium']}\n")
            f.write(f"🟢 BAIXOS: {severity_counts['low']}\n")
            f.write(f"\nTOTAL: {sum(severity_counts.values())}\n")
            f.write(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"Problemas organizados por severidade: {severity_counts}")
    
    def scrape_site(self, site_name, site_config):
        """Scraping de um site específico"""
        if not site_config['ativo']:
            print(f"Site {site_name} está desabilitado")
            return []
        
        print(f"\n🔍 Iniciando scraping de {site_name}...")
        start_time = time.time()
        complaints = []
        
        try:
            # Testa diferentes termos de busca
            search_terms = self.ti_keywords[:8]  # Primeiros 8 termos
            
            for term in search_terms:
                try:
                    # Constrói URL de busca
                    if '?' in site_config['url_busca']:
                        search_url = f"{site_config['url_busca']}&q={urllib.parse.quote(term)}"
                    else:
                        search_url = f"{site_config['url_busca']}?q={urllib.parse.quote(term)}"
                    
                    print(f"  Buscando: {term}")
                    
                    content = self.get_page_content(search_url)
                    if not content:
                        continue
                    
                    texts = self.extract_text_content(content)
                    
                    for text in texts:
                        relevance_score, keywords_found = self.calculate_relevance(text)
                        
                        if relevance_score >= 20:
                            problem_category = self.categorize_problem(text, keywords_found)
                            
                            complaint = {
                                'site_source': site_name,
                                'company_name': self.extract_company_name(text),
                                'title': text[:150] + '...' if len(text) > 150 else text,
                                'description': text,
                                'problem_category': problem_category,
                                'severity_level': problem_category,
                                'url': search_url,
                                'relevance_score': relevance_score,
                                'keywords_found': ', '.join(keywords_found)
                            }
                            
                            complaints.append(complaint)
                            print(f"    ✅ Problema {problem_category} encontrado (score: {relevance_score})")
                    
                    time.sleep(2)  # Pausa entre buscas
                    
                except Exception as e:
                    print(f"    ❌ Erro ao buscar '{term}': {e}")
                    continue
            
            # Salva dados do site
            if complaints:
                self.save_site_data(site_name, complaints)
            
            # Salva estatísticas
            execution_time = time.time() - start_time
            success_rate = len(complaints) / len(search_terms) if search_terms else 0
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO scraping_stats (site_name, complaints_found, execution_time, success_rate)
                VALUES (?, ?, ?, ?)
            ''', (site_name, len(complaints), execution_time, success_rate))
            self.conn.commit()
            
            print(f"✅ {site_name}: {len(complaints)} problemas encontrados em {execution_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Erro no scraping de {site_name}: {e}")
        
        return complaints
    
    def extract_company_name(self, text):
        """Extrai nome da empresa"""
        patterns = [
            r'empresa\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z]+)\s+não\s+funciona',
            r'problema\s+com\s+([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z]+)\s+tem\s+bug',
            r'sistema\s+da\s+([A-Z][a-zA-Z\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        return "Empresa não identificada"
    
    def save_complaint_to_db(self, complaint):
        """Salva reclamação no banco"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
                SELECT id FROM complaints 
                WHERE site_source = ? AND title = ? AND description = ?
            ''', (complaint['site_source'], complaint['title'], complaint['description']))
            
            if cursor.fetchone():
                return False
            
            cursor.execute('''
                INSERT INTO complaints (
                    site_source, company_name, title, description, 
                    problem_category, severity_level, url, relevance_score, keywords_found
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                complaint['site_source'], complaint['company_name'], complaint['title'],
                complaint['description'], complaint['problem_category'], complaint['severity_level'],
                complaint['url'], complaint['relevance_score'], complaint['keywords_found']
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            print(f"Erro ao salvar no banco: {e}")
            return False
    
    def generate_final_report(self):
        """Gera relatório final"""
        cursor = self.conn.cursor()
        
        # Estatísticas gerais
        cursor.execute('SELECT COUNT(*) FROM complaints')
        total_complaints = cursor.fetchone()[0]
        
        cursor.execute('SELECT site_source, COUNT(*) FROM complaints GROUP BY site_source')
        by_site = cursor.fetchall()
        
        cursor.execute('SELECT severity_level, COUNT(*) FROM complaints GROUP BY severity_level')
        by_severity = cursor.fetchall()
        
        # Gera relatório
        report_file = f'reports/final_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO FINAL - SCRAPER DE RECLAMAÇÕES DE TI\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"📊 TOTAL DE PROBLEMAS ENCONTRADOS: {total_complaints}\n\n")
            
            f.write("📈 PROBLEMAS POR SITE:\n")
            for site, count in by_site:
                f.write(f"  {site}: {count}\n")
            
            f.write("\n🚨 PROBLEMAS POR SEVERIDADE:\n")
            for severity, count in by_severity:
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')
                f.write(f"  {emoji} {severity.upper()}: {count}\n")
            
            f.write(f"\n📅 Relatório gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"📋 Relatório final salvo em: {report_file}")
        return report_file
    
    def run_scraping(self):
        """Executa scraping de todos os sites"""
        print("🚀 INICIANDO SCRAPER ORGANIZADO DE RECLAMAÇÕES DE TI")
        print("="*60)
        
        all_complaints = []
        
        for site_name, site_config in self.sites_config.items():
            complaints = self.scrape_site(site_name, site_config)
            
            # Salva no banco
            saved_count = 0
            for complaint in complaints:
                if self.save_complaint_to_db(complaint):
                    saved_count += 1
            
            all_complaints.extend(complaints)
            print(f"💾 {site_name}: {saved_count} problemas salvos no banco")
            
            time.sleep(3)  # Pausa entre sites
        
        # Organiza problemas por severidade
        if all_complaints:
            self.save_problems_by_severity(all_complaints)
        
        # Gera relatório final
        report_file = self.generate_final_report()
        
        print("\n" + "="*60)
        print("✅ SCRAPING CONCLUÍDO COM SUCESSO!")
        print(f"📊 Total de problemas encontrados: {len(all_complaints)}")
        print(f"📋 Relatório disponível em: {report_file}")
        print("\n📁 Verifique as pastas criadas:")
        print("  - sites_data/ (dados por site)")
        print("  - problems_found/ (problemas por severidade)")
        print("  - reports/ (relatórios finais)")
    
    def close(self):
        """Fecha conexões"""
        if self.conn:
            self.conn.close()

def main():
    """Função principal"""
    scraper = OrganizedScraper()
    
    try:
        scraper.run_scraping()
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
    finally:
        scraper.close()
        print("🔚 Scraper finalizado!")

if __name__ == "__main__":
    main()