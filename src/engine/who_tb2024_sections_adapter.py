"""Search selected WHO Global Tuberculosis Report 2024 web sections."""
import release_runtime
import argparse, hashlib, json
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.who.int/teams/global-programme-on-tuberculosis-and-lung-health/tb-reports/global-tuberculosis-report-2024/'
SECTIONS = {'incidence': 'tb-disease-burden/1-1-tb-incidence', 'mortality': 'tb-disease-burden/1-2-tb-mortality', 'notifications': 'tb-diagnosis-and-treatment/2-1-case-notifications'}

def query(section, keyword='', limit=20):
    if section not in SECTIONS:
        raise ValueError('invalid section')
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('invalid query')
    url = BASE + SECTIONS[section]
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(2000001, decode_content=True)
    if len(raw) > 2000000:
        raise ValueError('page exceeds size limit')
    soup = BeautifulSoup(raw, 'html.parser')
    container = soup.select_one('#PageContent_C037_Col01')
    if container is None:
        raise ValueError('expected content not found')
    paras = [p.get_text(' ', strip=True) for p in container.select('p') if p.get_text(' ', strip=True)]
    hits = [p for p in paras if keyword.casefold() in p.casefold()]
    return {'source': url, 'report_page': BASE, 'report_publication_date': '2024-10-29', 'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'section': section, 'paragraphs_found': len(hits), 'paragraphs': hits[:limit], 'note': 'WHO Global Tuberculosis Report 2024 historical web section only; not complete database or figures. WHO warns these burden estimates are outdated and direct comparisons across report editions are inappropriate. Model-based incidence and mortality estimates are distinct from reported notifications. Current webpage may have changed since publication; HTTP timestamp is not independent archive proof. Check year, denominator, uncertainty intervals and reuse conditions.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('section', choices=list(SECTIONS))
    p.add_argument('--keyword', default='')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(query(a.section, a.keyword, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
