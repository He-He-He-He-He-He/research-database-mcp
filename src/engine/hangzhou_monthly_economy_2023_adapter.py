"""Official Hangzhou government gazette monthly economic tables, 2023."""
import release_runtime
import subprocess
from bs4 import BeautifulSoup
BASE = 'https://zfgb.hangzhou.gov.cn/136/'
PATHS = {m: f'106220253/t103220253064/{525292 + m}.shtml' for m in range(2, 13)}

def catalog():
    return [{'month': m, 'title': f'2023年{m}月份杭州市国民经济主要统计指标', 'url': BASE + p} for m, p in PATHS.items()]

def table(month):
    if isinstance(month, bool) or not isinstance(month, int) or month not in PATHS:
        raise ValueError('available months: February through December')
    item = next((x for x in catalog() if x['month'] == month))
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', item['url']], capture_output=True, check=True, timeout=30)
    soup = BeautifulSoup(r.stdout, 'html.parser')
    title = soup.find('meta', attrs={'name': 'ArticleTitle'})
    source = soup.find('meta', attrs={'name': 'ContentSource'})
    if not title or title.get('content') != item['title'] or (not source) or (source.get('content') not in ('杭州市统计局', '市统计局')):
        raise ValueError('source or title mismatch')
    body = soup.select_one('.html_content')
    if not body:
        raise ValueError('article body missing')
    tables = []
    for tab in body.find_all('table'):
        rows = []
        for tr in tab.find_all('tr'):
            cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if not tables:
        raise ValueError('table missing')
    return {'source': '杭州市统计局，经杭州市人民政府公报发布', 'source_url': item['url'], 'month': month, 'tables': tables, 'text': body.get_text('\n', strip=True)}
