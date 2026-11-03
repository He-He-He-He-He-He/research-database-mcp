"""IEA Gender and Energy Explorer: energy employment shares (OECD analysis of EU-LFS)."""
import release_runtime
import json
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.iea.org/gender-diversity'
PAGE = 'https://www.iea.org/data-and-statistics/data-tools/gender-and-energy-data-explorer'
LIMIT = 8000000

def _get(path='', params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(LIMIT), url], capture_output=True, timeout=40)
    if r.returncode:
        raise RuntimeError('IEA request failed: ' + r.stderr.decode('utf-8', 'replace')[:500])
    if len(r.stdout) > LIMIT:
        raise ValueError('IEA response too large')
    rows = json.loads(r.stdout)
    if not isinstance(rows, list):
        raise ValueError('unexpected response')
    return (url, rows)

def share(country, start, end):
    if not isinstance(country, str) or not country.strip() or len(country) > 120:
        raise ValueError('invalid country')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1900 <= x <= 2100) for x in (start, end))) or start > end:
        raise ValueError('invalid years')
    params = {'topic': 'Employment', 'indicator': 'Share of employment', 'country': country}
    url, rows = _get('', params)
    if any((not isinstance(r, dict) or any((r.get(k) != v for k, v in params.items())) or (not isinstance(r.get('year'), int)) for r in rows)):
        raise ValueError('unexpected/out-of-filter response')
    return {'source': url, 'page': PAGE, 'page_updated': '2026-10-30', 'year_filter': 'local', 'rows': [r for r in rows if start <= r['year'] <= end], 'note': 'OECD ELS analysis of EU Labour Force Survey, reproduced by IEA; 13 energy clusters based on O*NET occupations, not all national employment. Values are estimated percentages by gender/cluster; samples, category definitions and observation counts matter. Breakdowns and totals may overlap. See explorer metadata and original sources.'}
