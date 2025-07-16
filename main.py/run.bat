@echo off
echo IT Complaints Scraper
echo =====================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python not found!
    echo Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo Creating folder structure...
echo Running scraper...
echo.

python scraper.py

echo.
echo =====================
echo     SCRAPING DONE!
echo =====================
echo.
echo Generated files:
echo - complaints.db (database)
echo - sites_data/ (data by site)
echo - problems_found/ (problems by severity)
echo - reports/ (final reports)
echo.
echo To add new sites, edit: sites_config.txt
echo.
pause