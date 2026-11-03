"""Hangzhou government plans and execution tables in official gazette."""
import release_runtime
import subprocess
from bs4 import BeautifulSoup
URLS = {2015: 'https://zfgb.hangzhou.gov.cn/7/106220253/t113220253064/529176.shtml', 2020: 'https://zfgb.hangzhou.gov.cn/7/106220253/t109220253064/528953.shtml', 2023: 'https://zfgb.hangzhou.gov.cn/7/106220253/t104220253064/528829.shtml'}

def report(execution_year):
    if execution_year not in URLS:
        raise ValueError('available execution years: 2015, 2020, 2023')
    url = URLS[execution_year]
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '35', url], capture_output=True, timeout=40)
    if p.returncode:
        raise RuntimeError('gazette request failed: curl status ' + str(p.returncode))
    soup = BeautifulSoup(p.stdout, 'html.parser')
    body = soup.select_one('.html_content')
    if not body:
        raise ValueError('article body missing')
    tables = []
    for t in body.find_all('table'):
        rows = []
        for tr in t.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('no HTML tables found')
    return {'execution_year': execution_year, 'source': '杭州市人民政府公报', 'source_url': url, 'text': body.get_text('\n', strip=True), 'tables': tables}
