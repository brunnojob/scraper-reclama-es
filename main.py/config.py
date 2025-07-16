

import os
from dotenv import load_dotenv

load_dotenv()

#
TI_KEYWORDS = [
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


SCRAPING_CONFIG = {
    'delay_between_requests': 2,  # segundos
    'delay_between_sites': 5,     # segundos
    'max_retries': 3,
    'timeout': 30,
    'user_agent_rotation': True,
    'respect_robots_txt': True,
    'max_pages_per_site': 10,     # limite de páginas por site
}


DATABASE_CONFIG = {
    'db_path': 'ti_complaints.db',
    'backup_csv': True,
    'csv_path': 'ti_complaints_backup.csv'
}


SITES_CONFIG = {
    'reclame_aqui': {
        'base_url': 'https://www.reclameaqui.com.br',
        'search_url': 'https://www.reclameaqui.com.br/busca',
        'enabled': True,
        'use_selenium': True,  # Site carrega conteúdo dinamicamente
    },
    'consumidor_gov': {
        'base_url': 'https://www.consumidor.gov.br',
        'search_url': 'https://www.consumidor.gov.br/pages/indicador/pesquisar',
        'enabled': True,
        'use_selenium': False,
    },
    'ebit': {
        'base_url': 'https://www.ebit.com.br',
        'search_url': 'https://www.ebit.com.br/reclamacoes',
        'enabled': True,
        'use_selenium': False,
    },
    'trustpilot': {
        'base_url': 'https://www.trustpilot.com',
        'search_url': 'https://www.trustpilot.com/categories/technology',
        'enabled': True,
        'use_selenium': True,
    },
    'complaints_board': {
        'base_url': 'https://www.complaintsboard.com',
        'search_url': 'https://www.complaintsboard.com/categories/technology',
        'enabled': True,
        'use_selenium': False,
    },
    'sitejabber': {
        'base_url': 'https://www.sitejabber.com',
        'search_url': 'https://www.sitejabber.com/categories/technology',
        'enabled': True,
        'use_selenium': False,
    }
}


LOGGING_CONFIG = {
    'level': 'INFO',
    'file': 'scraper.log',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}
