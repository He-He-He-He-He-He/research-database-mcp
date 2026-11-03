"""Official Hangzhou government gazette monthly economic tables, 2025."""
import release_runtime
import subprocess
from bs4 import BeautifulSoup
BASE = 'https://zfgb.hangzhou.gov.cn/136/'
PATHS = {2: '105220253/t125220253054/520083.shtml', 3: '105220253/t124220253054/520079.shtml', 4: '106220253/t118220253064/529242.shtml', 5: '106220253/t124220253064/529286.shtml', 6: '107220253/t123220253074/529470.shtml', 7: '108220253/t122220253084/529545.shtml', 8: '109220253/t124220253094/529609.shtml', 9: '110220253/t127220253104/529754.shtml', 10: '111220253/t121220253114/529862.shtml', 11: '112220253/t124220253124/529999.shtml', 12: '101220263/t123220263014/530174.shtml'}

def catalog():
    return [{'month': m, 'title': f'2025年{m}月份杭州市国民经济主要统计资料', 'url': BASE + p} for m, p in PATHS.items()]

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
