#  Scraper Organizado de Reclamações de TI

Sistema avançado de scraping com organização em pastas e configuração externa.

## Como Executar

### Método Mais Fácil
```bash
# Clique duas vezes no arquivo:
run_organized.bat
```

### Pelo Terminal
```bash
python organized_scraper.py
```

## Estrutura de Pastas Criadas

```
project/
├── sites_data/           # Dados específicos de cada site
│   ├── reclame_aqui/
│   ├── consumidor_gov/
│   ├── ebit/
│   ├── trustpilot/
│   ├── complaints_board/
│   └── sitejabber/
├── problems_found/       # Problemas organizados por severidade
│   ├── critical/         # 🔴 Problemas críticos
│   ├── high/            # 🟠 Problemas altos
│   ├── medium/          # 🟡 Problemas médios
│   └── low/             # 🟢 Problemas baixos
├── reports/             # Relatórios finais
└── logs/               # Logs de execução
```

## Configuração de Sites

### Arquivo `sites_config.txt`

Edite este arquivo para:
- Adicionar novos sites
- Desabilitar sites específicos
- Configurar URLs de busca

**Formato:**
```
nome_site|url_base|url_busca|ativo(sim/nao)|usa_selenium(sim/nao)
```

**Exemplo:**
```
reclame_aqui|https://www.reclameaqui.com.br|https://www.reclameaqui.com.br/busca|sim|sim
novo_site|https://exemplo.com|https://exemplo.com/search|nao|nao
```

## Categorização de Problemas

### Por Severidade:
- 🔴 **CRÍTICOS**: Sistema fora do ar, perda de dados, hacks
- 🟠 **ALTOS**: Bugs, falhas, erros que impedem uso
- 🟡 **MÉDIOS**: Lentidão, timeouts, carregamento
- 🟢 **BAIXOS**: Problemas menores de usabilidade

### Por Palavras-chave:
- Sistema, bug, falha, erro, crash
- Suporte técnico, servidor, segurança
- Aplicativo, site, login, acesso
- E mais 25+ termos técnicos

## Arquivos Gerados

### Por Site:
- `{site}_data_YYYYMMDD_HHMMSS.json` - Dados brutos
- `{site}_summary.csv` - Resumo para Excel

### Por Severidade:
- `critical_problems.txt` - Problemas críticos
- `high_problems.txt` - Problemas altos
- `medium_problems.txt` - Problemas médios
- `low_problems.txt` - Problemas baixos
- `severity_summary.txt` - Resumo geral

### Relatórios:
- `final_report_YYYYMMDD_HHMMSS.txt` - Relatório completo
- `organized_complaints.db` - Banco de dados SQLite

## Funcionalidades Avançadas

### Sistema de Pontuação
- Cada problema recebe score de 0-100
- Bonus para palavras críticas
- Filtragem automática por relevância

### Detecção Inteligente
- Identifica tipo de problema
- Extrai nome da empresa
- Categoriza automaticamente

### Organização Automática
- Separa por site de origem
- Agrupa por severidade
- Gera estatísticas detalhadas

## Personalização

### Adicionar Novo Site:
1. Abra `sites_config.txt`
2. Adicione linha: `nome|url_base|url_busca|sim|nao`
3. Execute o scraper

### Modificar Palavras-chave:
1. Edite `organized_scraper.py`
2. Modifique lista `self.ti_keywords`
3. Adicione termos específicos

### Ajustar Severidade:
1. Modifique função `categorize_problem()`
2. Adicione novos critérios
3. Personalize classificação

## Exemplo de Uso

```python
# Executar scraping completo
scraper = OrganizedScraper()
scraper.run_scraping()

# Verificar resultados
# - Pasta sites_data/ terá dados de cada site
# - Pasta problems_found/ terá problemas por severidade
# - Pasta reports/ terá relatório final
```

## Problemas Comuns

**"Python não reconhecido"**
- Instale Python de python.org
- Marque "Add to PATH"

**"Poucos resultados"**
- Sites podem bloquear scraping
- Ajuste delays no código
- Verifique sites_config.txt

**"Erro de SSL"**
- Normal em alguns sites
- Scraper continua funcionando

## Suporte

1. Verifique pasta `logs/` para erros
2. Consulte `reports/` para estatísticas
3. Edite `sites_config.txt` para ajustes

---

**Sistema criado para análise ética de reclamações públicas de TI**
