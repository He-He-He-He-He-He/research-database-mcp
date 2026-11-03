"""World Bank blog authors' December 2024 regional remittance estimate table."""
import release_runtime
import argparse, hashlib, json
import requests
from bs4 import BeautifulSoup
URL = 'https://blogs.worldbank.org/en/peoplemove/in-2024--remittance-flows-to-low--and-middle-income-countries-ar'

def query(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    with requests.get(URL, stream=True, timeout=30) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(2000001, decode_content=True)
    if len(raw) > 2000000:
        raise ValueError('page exceeds limit')
    s = BeautifulSoup(raw, 'html.parser')
    tables = s.select('table')
    if len(tables) != 1:
        raise ValueError('unexpected table count')
    rows = []
    for tr in tables[0].select('tr'):
        cells = [{'text': c.get_text(' ', strip=True), 'colspan': int(c.get('colspan', '1')), 'rowspan': int(c.get('rowspan', '1'))} for c in tr.find_all(['td', 'th'], recursive=False)]
        if cells:
            rows.append(cells)
    if not rows or not any(('2024e' == c['text'] for c in rows[0])):
        raise ValueError('unexpected table header')
    matched = []
    unit = 'USD billion'
    for index, row in enumerate(rows[1:], start=2):
        label = row[0]['text']
        if label == 'Growth rate (percent)':
            unit = 'percent'
        if label.startswith(('Source :', 'Notes :')) or not label:
            continue
        if keyword.casefold() in label.casefold():
            matched.append({'source_row': index, 'section_unit': unit, 'cells': row})
    return {'source': URL, 'article_date': '2024-12-18', 'http_last_modified': modified, 'page_sha256': hashlib.sha256(raw).hexdigest(), 'table_title': 'Remittance Flows to Low- and Middle-Income Regions, 2017–24', 'header': rows[0], 'matched_count': len(matched), 'rows': matched, 'source_notes': rows[-2:], 'note': 'World Bank blog authors’ estimates; 2024e is an estimate, not observed final data. The first section is USD billions and the second is growth percent; regional groupings and excluding-China row are not independent countries or additive categories. Current page may have changed after its publication; server Last-Modified does not prove historical contents. Reported remittances exclude informal flows. Preserve source attribution and consult reuse terms.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(query(a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
