"""UNdata legacy country profile rows, including footnotes and period headings."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup

def profile(country, keyword='', limit=20):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{2}', country):
        raise ValueError('country must be ISO alpha-2')
    if not isinstance(keyword, str):
        raise ValueError('keyword must be text')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    url = f'https://data.un.org/legacy/en/iso/{country.lower()}.html'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'lxml')
    tables = soup.select('table.pure-table')
    items = []
    for table in tables:
        head = table.select_one('thead tr')
        years = [x.get_text(' ', strip=True) for x in head.find_all(['td', 'th'], recursive=False)] if head else []
        if len(years) != 4:
            continue
        for tr in table.select('tbody > tr'):
            cells = tr.find_all('td', recursive=False)
            if len(cells) != 4:
                continue
            label = cells[0].get_text(' ', strip=True)
            if keyword.casefold() not in label.casefold():
                continue
            values = []
            for cell in cells[1:]:
                vals = [x.get_text(' ', strip=True) for x in cell.find_all('small')]
                marks = [x.get_text(' ', strip=True) for x in cell.find_all('sup') if x.get_text(strip=True)]
                values.append({'value': ' '.join(vals), 'footnotes': marks})
            items.append({'indicator': label, 'column_labels': years[1:], 'values': values})
    notes = {}
    for tr in soup.select('table.pure-table-horizontal tr'):
        cells = tr.find_all('td', recursive=False)
        if len(cells) >= 3:
            key = cells[0].get_text(' ', strip=True)
            if key:
                notes[key] = cells[-1].get_text(' ', strip=True)
    if not tables or not notes:
        raise ValueError('unexpected UNdata profile structure')
    return {'source': 'UNdata country profile', 'url': url, 'country_code': country.upper(), 'matched': len(items), 'limit': limit, 'truncated': len(items) > limit, 'items': items[:limit], 'footnotes': notes, 'note': 'If truncated increase limit (maximum 100) or narrow keyword; column headings are profile periods and footnotes may override actual reference year. Values are original strings.'}
