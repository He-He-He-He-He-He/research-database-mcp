"""World Economic Forum Global Gender Gap Report 2025 online sections."""
import release_runtime
import argparse
import json
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://www.weforum.org/publications/global-gender-gap-report-2025/benchmarking-gender-gaps-2025'
REPORT = 'https://www.weforum.org/publications/global-gender-gap-report-2025'
MAX_BYTES = 2000000

def _content():
    with requests.get(URL, timeout=25, stream=True) as r:
        r.raise_for_status()
        raw = bytearray()
        for part in r.iter_content(65536):
            raw.extend(part)
            if len(raw) > MAX_BYTES:
                raise ValueError('page exceeds size limit')
    s = BeautifulSoup(bytes(raw), 'html.parser')
    content = s.select_one('div.tiptap.content-editor')
    if content is None:
        raise ValueError('expected report content not found')
    return content

def headings(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    c = _content()
    out = []
    for h in c.select('h4[id]'):
        title = h.get_text(' ', strip=True)
        ident = h.get('id')
        if keyword.casefold() in (title + ' ' + ident).casefold():
            out.append({'id': ident, 'title': title})
    return {'source': URL, 'report': REPORT, 'publication_date': '2025-06-11', 'headings': out, 'note': 'World Economic Forum research, not government statistics. These are selected online country sections, not all 148 economy profiles.'}

def section(slug):
    if not isinstance(slug, str) or not re.fullmatch('[a-z0-9-]{1,100}', slug):
        raise ValueError('invalid heading slug')
    c = _content()
    h = c.find('h4', id=slug)
    if h is None:
        raise ValueError('section not found; search headings')
    out = []
    for el in h.next_siblings:
        if getattr(el, 'name', None) in ('h2', 'h3', 'h4'):
            break
        if getattr(el, 'name', None) == 'p':
            out.append(el.get_text(' ', strip=True))
    if not out:
        raise ValueError('section content not found; page structure may have changed')
    return {'source': URL + '#' + slug, 'report': REPORT, 'publication_date': '2025-06-11', 'title': h.get_text(' ', strip=True), 'paragraphs': out, 'note': 'World Economic Forum nongovernmental composite index; 0–1 parity score is higher when measured gaps are closer to parity and is not UNDP GII. Underlying data vintages vary; online text may be updated. Full PDF not verified by this adapter.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('headings')
    q.add_argument('--keyword', default='')
    q = s.add_parser('section')
    q.add_argument('slug')
    a = p.parse_args()
    print(json.dumps(headings(a.keyword) if a.cmd == 'headings' else section(a.slug), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
