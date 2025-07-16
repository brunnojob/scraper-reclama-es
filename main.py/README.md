# IT Complaints Scraper

Python scraper that collects IT-related complaints from multiple public review and complaint sites.

## Sites Monitored

- Reclame Aqui
- Consumidor.gov.br
- Ebit
- Trustpilot
- ComplaintsBoard
- SiteJabber

## Features

- Filters complaints related to IT issues using keyword matching
- Categorizes problems by severity (critical, high, medium, low)
- Organizes data into separate folders by site and severity
- Saves data in SQLite database and CSV files
- Respects site rate limits and ethical scraping practices

## Installation

Requires Python 3.6 or higher.

## Usage

### Quick Start
```bash
# Double-click the file:
run.bat

# Or run directly:
python scraper.py
```

### Configuration

Edit `sites_config.txt` to:
- Add new sites
- Enable/disable specific sites
- Configure search URLs

Format: `site_name|base_url|search_url|active(sim/nao)|uses_selenium(sim/nao)`

## Output Structure

```
sites_data/          # Raw data by site
problems_found/      # Problems organized by severity
  ├── critical/      # Critical issues
  ├── high/         # High priority issues
  ├── medium/       # Medium priority issues
  └── low/          # Low priority issues
reports/            # Final summary reports
complaints.db       # SQLite database
```

## Data Collected

For each complaint:
- Company name
- Problem title and description
- Severity level
- Relevance score
- Keywords found
- Source URL
- Timestamp

## Keywords Monitored

System, bug, error, failure, slow performance, technical support, server, security, platform, application, website, login, access, network, technology, software, hardware, database, API, configuration, crash, timeout, maintenance, and more.

## Ethical Usage

This scraper:
- Implements delays between requests
- Respects robots.txt
- Only accesses public data
- Uses appropriate user agents
- Includes rate limiting

Use responsibly and in accordance with site terms of service.

## License

For educational and research purposes.