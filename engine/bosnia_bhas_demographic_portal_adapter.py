"""BiH BHAS Demographic Resilience portal public metadata and CSV."""
import release_runtime
import argparse, csv, io, json, re
import requests
from bs4 import BeautifulSoup
PORTAL = 'https://pdo.bhas.gov.ba'
DATA = 'https://demootpbh.github.io/populationData-data/en'
TOPICS = {1: 'Population', 2: 'Census', 3: 'Health', 4: 'Social protection', 5: 'Education', 6: 'Economy', 7: 'Labour force and living standard', 8: 'Violence'}

def get(url):
    s = requests.Session()
    s.trust_env = False
    with s.get(url, timeout=35, stream=True) as r:
        r.raise_for_status()
        b = bytearray()
        for chunk in r.iter_content(65536):
            b.extend(chunk)
            if len(b) > 5000000:
                raise ValueError('Response exceeds 5 MB')
        return (bytes(b).decode('utf-8-sig'), r.url)

def catalog(topic):
    if topic not in TOPICS:
        raise ValueError('Topic must be 1–8')
    html, url = get(PORTAL + '/' + str(topic) + '/')
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for a in soup.select('.goal-indicator a[href]'):
        match = re.fullmatch('/(\\d+-\\d+-\\d+)/?', a.get('href', ''))
        if match:
            items.append({'id': match.group(1), 'title': a.get_text(' ', strip=True)})
    return {'source': url, 'topic': TOPICS[topic], 'items': items, 'note': 'Portal uses Open SDG template numbering for national demographic indicators; these are not automatically global SDG series.'}

def check(id):
    if not re.fullmatch('[1-8]-\\d{1,3}-\\d{1,3}', id):
        raise ValueError('Invalid indicator id')
    return id

def metadata(id):
    check(id)
    raw, url = get(DATA + '/meta/' + id + '.json')
    return {'source': url, 'portal_page': PORTAL + '/' + id + '/', 'metadata': json.loads(raw)}

def data(id, year=None, limit=100):
    check(id)
    if not 1 <= limit <= 1000:
        raise ValueError('limit 1–1000')
    m = metadata(id)
    raw, url = get(DATA + '/data/' + id + '.csv')
    reader = csv.DictReader(io.StringIO(raw))
    rows = [row for row in reader if year is None or row.get('Year') == str(year)]
    return {'source': url, 'metadata_source': m['source'], 'metadata': m['metadata'], 'matches': len(rows), 'returned': min(len(rows), limit), 'truncated': len(rows) > limit, 'rows': rows[:limit], 'note': 'Official portal links GitHub-hosted data. Source and definitions vary by indicator; Page template includes a development-site notice; current publication status requires independent confirmation.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    c = s.add_parser('catalog')
    c.add_argument('topic', type=int)
    m = s.add_parser('metadata')
    m.add_argument('id')
    d = s.add_parser('data')
    d.add_argument('id')
    d.add_argument('--year', type=int)
    d.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    res = catalog(a.topic) if a.command == 'catalog' else metadata(a.id) if a.command == 'metadata' else data(a.id, a.year, a.limit)
    print(json.dumps(res, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
