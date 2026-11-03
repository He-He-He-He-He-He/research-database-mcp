"""Public eCFR API: title metadata, search and date-specific section XML."""
import release_runtime
import datetime
import re
import xml.etree.ElementTree as ET
import requests
BASE = 'https://www.ecfr.gov/api'

def _get(path, params=None):
    response = requests.get(BASE + path, params=params, timeout=45, headers={'User-Agent': 'ResearchDatabaseToolkit/1.0 (personal research)'})
    response.raise_for_status()
    return response

def titles():
    return _get('/versioner/v1/titles.json').json()

def search(query, page=1, per_page=10):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be nonempty')
    if not isinstance(page, int) or page < 1 or (not isinstance(per_page, int)) or (not 1 <= per_page <= 100):
        raise ValueError('page must be positive and per_page must be between 1 and 100')
    return _get('/search/v1/results', {'query': query, 'page': page, 'per_page': per_page}).json()

def section(title, section_number, date):
    if not isinstance(title, int) or not 1 <= title <= 50:
        raise ValueError('title must be an integer from 1 to 50')
    if not isinstance(section_number, str) or not re.fullmatch('[A-Za-z0-9.-]+', section_number):
        raise ValueError('invalid section number')
    try:
        datetime.date.fromisoformat(date)
    except (TypeError, ValueError):
        raise ValueError('date must be YYYY-MM-DD') from None
    if not re.fullmatch('\\d{4}-\\d{2}-\\d{2}', date):
        raise ValueError('date must be YYYY-MM-DD')
    response = _get(f'/versioner/v1/full/{date}/title-{title}.xml', {'section': section_number})
    root = ET.fromstring(response.content)
    return {'title': title, 'section': section_number, 'date': date, 'source_url': response.url, 'xml': response.content.decode('utf-8'), 'text': ' '.join(' '.join(root.itertext()).split())}
