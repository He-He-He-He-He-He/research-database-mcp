"""国家知识产权局专利年报 A1 官方原表（2015—2024）。"""
import release_runtime
import subprocess
from bs4 import BeautifulSoup

def annual(year):
    year = int(year)
    if not 2015 <= year <= 2024:
        raise ValueError('本接口仅支持经核验的 2015—2024 年')
    url = f'https://www.cnipa.gov.cn/tjxx/jianbao/year{year}/a/a1.html'
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--compressed', '--max-time', '25', url], capture_output=True, timeout=30)
    if p.returncode:
        raise RuntimeError('知识产权局查询失败: ' + p.stderr.decode('utf-8', 'replace').strip())
    soup = BeautifulSoup(p.stdout, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        raise RuntimeError('未识别原表，网站可能变化或访问受限')
    table = max(tables, key=lambda t: len(t.find_all('tr')))
    rows = []
    for tr in table.find_all('tr'):
        cells = [{'text': c.get_text(' ', strip=True), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
        if cells:
            rows.append(cells)
    text = soup.get_text(' ', strip=True)
    if str(year) not in text or len(rows) < 8:
        raise RuntimeError('年份或表格结构未通过核验')
    return {'year': year, 'url': url, 'source': '国家知识产权局', 'scope': '截至年末累计申请及授权量、有效量' if year in (2015, 2016) else '当年申请与授权、年末有效量；以原表为准', 'unit': '件；另有构成百分比', 'rows': rows, 'page_text': text}
