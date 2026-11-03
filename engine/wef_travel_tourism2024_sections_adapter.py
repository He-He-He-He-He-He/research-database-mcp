"""World Economic Forum TTDI 2024 report landing-page paragraphs."""
import release_runtime
import argparse, hashlib, json
import requests
from bs4 import BeautifulSoup
URL = 'https://www.weforum.org/publications/travel-tourism-development-index-2024'

def query(keyword='', limit=20):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100):
        raise ValueError('invalid query')
    with requests.get(URL, stream=True, timeout=30) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(2000001, decode_content=True)
    if len(raw) > 2000000:
        raise ValueError('page exceeds size limit')
    s = BeautifulSoup(raw, 'html.parser')
    c = s.select_one('div.tiptap.content-editor')
    if c is None:
        raise ValueError('expected article content unavailable')
    paras = [p.get_text(' ', strip=True) for p in c.find_all('p') if p.get_text(' ', strip=True)]
    hits = [p for p in paras if keyword.casefold() in p.casefold()]
    return {'source': URL, 'report_publication_date': '2024-05-21', 'http_last_modified': modified, 'page_sha256': hashlib.sha256(raw).hexdigest(), 'matched_count': len(hits), 'paragraphs': hits[:limit], 'note': 'World Economic Forum and University of Surrey non-governmental composite index of travel and tourism enabling conditions, not tourist arrivals or government statistics. Landing-page selected narrative only; full 119-economy dataset not included or verified. Historical comparisons can reflect methodology and recalculations; consult methodology. Web content may have changed after publication, and timestamps do not prove historical immutability. Full dataset URL was unavailable in local testing. Preserve source and applicable usage terms.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
