"""Kyrgyz statistics committee official NSDP current-value table search."""
import release_runtime
import argparse, json, re, subprocess
from bs4 import BeautifulSoup
URL = 'https://www.stat.gov.kg/nsdp/index1.htm'
MAX = 5000000

def search(query, limit=20):
    if not isinstance(query, str) or not query.strip() or len(query) > 100:
        raise ValueError('query required')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1..100')
    p = release_runtime.run(['/usr/bin/curl', '-q', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX), URL], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('Kyrgyz NSDP request failed: curl ' + str(p.returncode))
    if len(p.stdout) > MAX:
        raise ValueError('response exceeds 5 MB')
    soup = BeautifulSoup(p.stdout, 'html.parser')
    matches = []
    for tr in soup.find_all('tr'):
        cells = [re.sub('\\s+', ' ', x.get_text(' ', strip=True)).strip() for x in tr.find_all(['td', 'th'], recursive=False)]
        if len(cells) >= 4 and all((len(c) <= 600 for c in cells)) and (query.casefold() in ' '.join(cells).casefold()):
            matches.append(cells)
    return {'source': URL, 'query': query, 'matched': len(matches), 'returned': min(limit, len(matches)), 'rows': matches[:limit], 'note': 'Raw published table cells, not a complete historical time series. Check nearby headers, footnotes, frequency, statistical agency and status; comma is decimal where used. Never assume missing means zero.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    try:
        print(json.dumps(search(a.query, a.limit), ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError) as e:
        p.exit(1, str(e) + '\n')
if __name__ == '__main__':
    main()
