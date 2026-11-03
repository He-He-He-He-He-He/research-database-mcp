"""WOAH official 2024 Terrestrial Animal Health Code archived chapter index."""
import release_runtime
from urllib.parse import urljoin, urlparse
import re
import requests
from bs4 import BeautifulSoup
ROOT = 'https://www.woah.org/fileadmin/Home/eng/Health_standards/tahc/2024/'
PAGE = ROOT + 'en_sommaire.htm'
NOTES = ['The source is the 2024 edition of the WOAH Terrestrial Animal Health Code, not necessarily the current edition. Verify historical availability separately when an exact cutoff matters.', 'International standards and recommendations do not themselves establish the current domestic law or import requirements of any particular country.', 'The directory supplies chapter titles and original links, not disease occurrence statistics. Changes after 2024 are not reflected.']

def search(keyword='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid search parameters')
    r = requests.get(PAGE, timeout=45)
    r.raise_for_status()
    s = BeautifulSoup(r.text, 'html.parser')
    if 'Terrestrial Animal Health Code' not in s.get_text(' ', strip=True):
        raise ValueError('Unexpected WOAH page')
    rows = []
    for a in s.find_all('a', href=True):
        number = ' '.join(a.get_text(' ', strip=True).split())
        if not re.fullmatch('Chapter \\d+\\.\\d+\\.', number):
            continue
        tr = a.find_parent('tr')
        td = tr.find_all('td', recursive=False) if tr else []
        if len(td) < 2:
            raise ValueError('Unexpected WOAH chapter row')
        title = ' '.join(td[1].get_text(' ', strip=True).split())
        url = urljoin(PAGE, a['href'])
        p = urlparse(url)
        if not title or p.scheme != 'https' or p.hostname != 'www.woah.org' or (not p.path.startswith('/fileadmin/Home/eng/Health_standards/tahc/2024/')):
            raise ValueError('Unexpected WOAH chapter or link')
        rows.append({'chapter': number, 'title': title, 'url': url})
    if not rows or len({x['chapter'] for x in rows}) != len(rows):
        raise ValueError('Empty or duplicate WOAH chapters')
    matches = [r for r in rows if keyword.casefold() in (r['chapter'] + ' ' + r['title']).casefold()]
    return {'source': PAGE, 'edition': 2024, 'source_chapter_count': len(rows), 'total_matching': len(matches), 'offset': offset, 'notes': NOTES, 'records': matches[offset:offset + limit]}
