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

ssl._create_default_https_context = ssl._create_unverified_context

class ITComplaintsScraper:
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
                print(f"Created directory: {directory}")
    
    def load_sites_config(self):
        sites = {}
        
        if not os.path.exists('sites_config.txt'):
            print("sites_config.txt not found!")
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
            
            print(f"Configuration loaded: {len(sites)} sites found")
            active_sites = sum(1 for site in sites.values() if site['ativo'])
            print(f"Active sites: {active_sites}")
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
        
        return sites
    
    def setup_database(self):
        self.conn = sqlite3.connect('complaints.db')
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
        print("Database configured successfully")
    
    def get_page_content(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
                return content
                
        except Exception as e:
            print(f"Error accessing {url}: {e}")
            return None
    
    def categorize_problem(self, text, keywords_found):
        text_lower = text.lower()
        
        critical_keywords = ['fora do ar', 'indisponível', 'crash', 'perda de dados', 'hack', 'vírus', 'malware']
        if any(keyword in text_lower for keyword in critical_keywords):
            return 'critical'
        
        high_keywords = ['bug', 'falha', 'erro', 'não funciona', 'travando', 'freeze']
        if any(keyword in text_lower for keyword in high_keywords):
            return 'high'
        
        medium_keywords = ['lentidão', 'lento', 'demora', 'timeout', 'loading']
        if any(keyword in text_lower for keyword in medium_keywords):
            return 'medium'
        
        return 'low'
    
    def calculate_relevance(self, text):
        if not text:
            return 0, []
        
        text_lower = text.lower()
        score = 0
        keywords_found = []
        
        for keyword in self.ti_keywords:
            if keyword in text_lower:
                score += 10
                keywords_found.append(keyword)
                
                if keyword in ['bug', 'falha', 'erro', 'crash', 'fora do ar']:
                    score += 15
        
        return min(score, 100), keywords_found
    
    def extract_text_content(self, html_content):
        if not html_content:
            return []
        
        html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL)
        
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
        site_folder = f'sites_data/{site_name}'
        
        json_file = f'{site_folder}/{site_name}_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(complaints, f, ensure_ascii=False, indent=2)
        
        csv_file = f'{site_folder}/{site_name}_summary.csv'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Company', 'Title', 'Category', 'Severity', 'Score', 'Keywords'])
            
            for complaint in complaints:
                writer.writerow([
                    complaint.get('company_name', ''),
                    complaint.get('title', '')[:100],
                    complaint.get('problem_category', ''),
                    complaint.get('severity_level', ''),
                    complaint.get('relevance_score', 0),
                    complaint.get('keywords_found', '')
                ])
        
        print(f"Data for {site_name} saved in: {site_folder}")
    
    def save_problems_by_severity(self, complaints):
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for complaint in complaints:
            severity = complaint.get('severity_level', 'low')
            severity_counts[severity] += 1
            
            severity_file = f'problems_found/{severity}/{severity}_problems.txt'
            
            with open(severity_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"SITE: {complaint.get('site_source', '')}\n")
                f.write(f"COMPANY: {complaint.get('company_name', '')}\n")
                f.write(f"TITLE: {complaint.get('title', '')}\n")
                f.write(f"PROBLEM: {complaint.get('description', '')[:200]}...\n")
                f.write(f"KEYWORDS: {complaint.get('keywords_found', '')}\n")
                f.write(f"SCORE: {complaint.get('relevance_score', 0)}\n")
                f.write(f"DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        summary_file = 'problems_found/severity_summary.txt'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("PROBLEM SEVERITY SUMMARY\n")
            f.write("="*40 + "\n\n")
            f.write(f"CRITICAL: {severity_counts['critical']}\n")
            f.write(f"HIGH: {severity_counts['high']}\n")
            f.write(f"MEDIUM: {severity_counts['medium']}\n")
            f.write(f"LOW: {severity_counts['low']}\n")
            f.write(f"\nTOTAL: {sum(severity_counts.values())}\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"Problems organized by severity: {severity_counts}")
    
    def scrape_site(self, site_name, site_config):
        if not site_config['ativo']:
            print(f"Site {site_name} is disabled")
            return []
        
        print(f"\nStarting scraping of {site_name}...")
        start_time = time.time()
        complaints = []
        
        try:
            search_terms = self.ti_keywords[:8]
            
            for term in search_terms:
                try:
                    if '?' in site_config['url_busca']:
                        search_url = f"{site_config['url_busca']}&q={urllib.parse.quote(term)}"
                    else:
                        search_url = f"{site_config['url_busca']}?q={urllib.parse.quote(term)}"
                    
                    print(f"  Searching: {term}")
                    
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
                            print(f"    Found {problem_category} problem (score: {relevance_score})")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"    Error searching '{term}': {e}")
                    continue
            
            if complaints:
                self.save_site_data(site_name, complaints)
            
            execution_time = time.time() - start_time
            success_rate = len(complaints) / len(search_terms) if search_terms else 0
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO scraping_stats (site_name, complaints_found, execution_time, success_rate)
                VALUES (?, ?, ?, ?)
            ''', (site_name, len(complaints), execution_time, success_rate))
            self.conn.commit()
            
            print(f"{site_name}: {len(complaints)} problems found in {execution_time:.2f}s")
            
        except Exception as e:
            print(f"Error scraping {site_name}: {e}")
        
        return complaints
    
    def extract_company_name(self, text):
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
        
        return "Company not identified"
    
    def save_complaint_to_db(self, complaint):
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
            print(f"Error saving to database: {e}")
            return False
    
    def generate_final_report(self):
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM complaints')
        total_complaints = cursor.fetchone()[0]
        
        cursor.execute('SELECT site_source, COUNT(*) FROM complaints GROUP BY site_source')
        by_site = cursor.fetchall()
        
        cursor.execute('SELECT severity_level, COUNT(*) FROM complaints GROUP BY severity_level')
        by_severity = cursor.fetchall()
        
        report_file = f'reports/final_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("FINAL REPORT - IT COMPLAINTS SCRAPER\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"TOTAL PROBLEMS FOUND: {total_complaints}\n\n")
            
            f.write("PROBLEMS BY SITE:\n")
            for site, count in by_site:
                f.write(f"  {site}: {count}\n")
            
            f.write("\nPROBLEMS BY SEVERITY:\n")
            for severity, count in by_severity:
                f.write(f"  {severity.upper()}: {count}\n")
            
            f.write(f"\nReport generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"Final report saved at: {report_file}")
        return report_file
    
    def run_scraping(self):
        print("STARTING IT COMPLAINTS SCRAPER")
        print("="*60)
        
        all_complaints = []
        
        for site_name, site_config in self.sites_config.items():
            complaints = self.scrape_site(site_name, site_config)
            
            saved_count = 0
            for complaint in complaints:
                if self.save_complaint_to_db(complaint):
                    saved_count += 1
            
            all_complaints.extend(complaints)
            print(f"{site_name}: {saved_count} problems saved to database")
            
            time.sleep(3)
        
        if all_complaints:
            self.save_problems_by_severity(all_complaints)
        
        report_file = self.generate_final_report()
        
        print("\n" + "="*60)
        print("SCRAPING COMPLETED SUCCESSFULLY!")
        print(f"Total problems found: {len(all_complaints)}")
        print(f"Report available at: {report_file}")
        print("\nCheck the created folders:")
        print("  - sites_data/ (data by site)")
        print("  - problems_found/ (problems by severity)")
        print("  - reports/ (final reports)")
    
    def close(self):
        if self.conn:
            self.conn.close()

def main():
    scraper = ITComplaintsScraper()
    
    try:
        scraper.run_scraping()
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        scraper.close()
        print("Scraper finished!")

if __name__ == "__main__":
    main()