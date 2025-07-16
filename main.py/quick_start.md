# Início Rápido - Scraper de Reclamações de TI

## Problema com pip/Python?

Se você está tendo problemas com `pip install`, use a **versão simplificada** que não precisa de dependências externas!

## Opção 1: Versão Simplificada (Recomendada para iniciantes)

### Passo 1: Verificar Python
Abra o Prompt de Comando (cmd) e digite:
```cmd
python --version
```

Se aparecer a versão do Python, pule para o Passo 3.

### Passo 2: Instalar Python (se necessário)
1. Acesse: https://www.python.org/downloads/
2. Baixe e instale a versão mais recente
3. **IMPORTANTE**: Marque "Add Python to PATH" durante a instalação

### Passo 3: Executar Scraper Simplificado
```cmd
# Navegue até a pasta do projeto
cd C:\Users\onnat\Downloads\scraper\project

# Execute o scraper simplificado
python simple_scraper.py
```

**OU** simplesmente clique duas vezes no arquivo `run_simple.bat`

## Opção 2: Versão Completa (Após instalar Python)

```cmd
# Instalar dependências
pip install requests beautifulsoup4 selenium pandas python-dotenv fake-useragent webdriver-manager lxml

# Executar versão completa
python main.py
```

## O que o Scraper Faz

✅ Acessa sites de reclamações automaticamente  
✅ Filtra reclamações relacionadas a TI  
✅ Salva dados em banco SQLite  
✅ Exporta para arquivo CSV  
✅ Respeita limites dos sites (ético)  

## Arquivos Gerados

- `ti_complaints_simple.db` - Banco de dados com todas as reclamações
- `ti_complaints_simple.csv` - Arquivo CSV para análise no Excel
- Logs no terminal mostrando o progresso

## Dicas

- O scraper pode demorar alguns minutos para completar
- Pressione Ctrl+C para interromper se necessário
- Os dados ficam salvos mesmo se interromper
- Execute novamente para coletar mais dados

## Problemas Comuns

**"python não é reconhecido"**: Instale o Python e marque "Add to PATH"  
**Erro de SSL**: Normal em alguns sites, o scraper continua funcionando  
**Poucos resultados**: Alguns sites podem bloquear acesso automatizado  

## Próximos Passos

Após executar o scraper:
1. Abra o arquivo CSV no Excel para análise
2. Use ferramentas de BI para criar dashboards
3. Analise tendências de reclamações de TI