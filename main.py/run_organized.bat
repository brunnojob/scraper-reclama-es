@echo off
echo ========================================
echo   SCRAPER ORGANIZADO DE RECLAMACOES TI
echo ========================================
echo.

echo Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Python nao encontrado!
    echo Instale de: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo Criando estrutura de pastas...
echo Executando scraper organizado...
echo.

python organized_scraper.py

echo.
echo ========================================
echo           SCRAPING CONCLUIDO!
echo ========================================
echo.
echo Arquivos gerados:
echo - organized_complaints.db (banco de dados)
echo - sites_data/ (dados por site)
echo - problems_found/ (problemas por severidade)
echo - reports/ (relatorios finais)
echo.
echo Para adicionar novos sites, edite: sites_config.txt
echo.
pause