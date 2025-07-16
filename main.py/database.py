

import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional
from config import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerencia o banco de dados SQLite para armazenar reclamações"""

    def __init__(self, db_path: str = DATABASE_CONFIG['db_path']):
        self.db_path = db_path
        self.init_database()

    def init_database(self):

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()


            cursor.execute('''
                CREATE TABLE IF NOT EXISTS complaints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_source TEXT NOT NULL,
                    company_name TEXT,
                    complaint_date DATE,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    rating REAL,
                    status TEXT,
                    company_response TEXT,
                    url TEXT,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ti_keywords TEXT,
                    relevance_score REAL
                )
            ''')


            cursor.execute('CREATE INDEX IF NOT EXISTS idx_site_source ON complaints(site_source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_company_name ON complaints(company_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_complaint_date ON complaints(complaint_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_scraped_at ON complaints(scraped_at)')

            conn.commit()
            conn.close()

            logger.info(f"Banco de dados inicializado: {self.db_path}")

        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise

    def save_complaint(self, complaint_data: Dict) -> bool:

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            
            cursor.execute('''
                SELECT id FROM complaints
                WHERE site_source = ? AND title = ? AND company_name = ?
            ''', (complaint_data.get('site_source'),
                  complaint_data.get('title'),
                  complaint_data.get('company_name')))

            if cursor.fetchone():
                logger.debug(f"Reclamação já existe: {complaint_data.get('title')}")
                conn.close()
                return False

            # Insere nova reclamação
            cursor.execute('''
                INSERT INTO complaints (
                    site_source, company_name, complaint_date, title, description,
                    category, rating, status, company_response, url, ti_keywords, relevance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                complaint_data.get('site_source'),
                complaint_data.get('company_name'),
                complaint_data.get('complaint_date'),
                complaint_data.get('title'),
                complaint_data.get('description'),
                complaint_data.get('category'),
                complaint_data.get('rating'),
                complaint_data.get('status'),
                complaint_data.get('company_response'),
                complaint_data.get('url'),
                complaint_data.get('ti_keywords'),
                complaint_data.get('relevance_score')
            ))

            conn.commit()
            conn.close()

            logger.info(f"Reclamação salva: {complaint_data.get('title')}")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar reclamação: {e}")
            return False

    def get_complaints_count(self, site_source: Optional[str] = None) -> int:
        """Retorna o número total de reclamações"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if site_source:
                cursor.execute('SELECT COUNT(*) FROM complaints WHERE site_source = ?', (site_source,))
            else:
                cursor.execute('SELECT COUNT(*) FROM complaints')

            count = cursor.fetchone()[0]
            conn.close()

            return count

        except Exception as e:
            logger.error(f"Erro ao contar reclamações: {e}")
            return 0

    def export_to_csv(self, csv_path: str = DATABASE_CONFIG['csv_path']) -> bool:
        """Exporta todas as reclamações para um arquivo CSV"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query('SELECT * FROM complaints ORDER BY scraped_at DESC', conn)
            conn.close()

            df.to_csv(csv_path, index=False, encoding='utf-8')
            logger.info(f"Dados exportados para CSV: {csv_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao exportar para CSV: {e}")
            return False

    def get_recent_complaints(self, limit: int = 100) -> List[Dict]:
        """Retorna as reclamações mais recentes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM complaints
                ORDER BY scraped_at DESC
                LIMIT ?
            ''', (limit,))

            columns = [description[0] for description in cursor.description]
            complaints = []

            for row in cursor.fetchall():
                complaints.append(dict(zip(columns, row)))

            conn.close()
            return complaints

        except Exception as e:
            logger.error(f"Erro ao buscar reclamações recentes: {e}")
            return []

    def get_stats(self) -> Dict:
        """Retorna estatísticas do banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Contagem total
            cursor.execute('SELECT COUNT(*) FROM complaints')
            total_complaints = cursor.fetchone()[0]

            # Contagem por site
            cursor.execute('''
                SELECT site_source, COUNT(*) as count
                FROM complaints
                GROUP BY site_source
            ''')
            by_site = dict(cursor.fetchall())

            # Contagem por empresa (top 10)
            cursor.execute('''
                SELECT company_name, COUNT(*) as count
                FROM complaints
                GROUP BY company_name
                ORDER BY count DESC
                LIMIT 10
            ''')
            top_companies = dict(cursor.fetchall())

            # Média de relevância
            cursor.execute('SELECT AVG(relevance_score) FROM complaints WHERE relevance_score IS NOT NULL')
            avg_relevance = cursor.fetchone()[0] or 0

            conn.close()

            return {
                'total_complaints': total_complaints,
                'by_site': by_site,
                'top_companies': top_companies,
                'avg_relevance_score': round(avg_relevance, 2)
            }

        except Exception as e:
            logger.error(f"Erro ao gerar estatísticas: {e}")
            return {}
