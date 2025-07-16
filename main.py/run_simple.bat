@echo off
echo === SCRAPER SIMPLIFICADO DE RECLAMACOES DE TI ===
echo.
echo Verificando se Python esta instalado...
python --version
if %errorlevel% neq 0 (
    echo.
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python de https://www.python.org/downloads/
    echo Certifique-se de marcar "Add Python to PATH" durante a instalacao
    pause
    exit /b 1
)

echo.
echo Executando scraper simplificado...
python simple_scraper.py

echo.
echo Scraping concluido! Verifique os arquivos:
echo - ti_complaints_simple.db (banco de dados)
echo - ti_complaints_simple.csv (dados em CSV)
echo.
pause