"""国际法院公开案件目录与案件官方文件链接；非浙大订购接口。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.icj-cij.org/'

def _get(path):
    r = requests.get(BASE + path, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'html' not in r.headers.get('Content-Type', '').lower() or len(r.content) > 5000000:
        raise RuntimeError('官方页面跳转、格式异常或过大')
    return BeautifulSoup(r.content, 'html.parser')

def search(keyword):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('请输入 1–200 字英文或法文关键词')
    soup = _get('list-of-all-cases')
    result = []
    seen = set()
    rows = soup.select('tr:has(a[href^="case/"])')
    if len(rows) < 100:
        raise RuntimeError('官方案件目录不完整或结构变化')
    for row in rows:
        a = row.select_one('a[href^="case/"]')
        path = a.get('href', '')
        m = re.fullmatch('case/(\\d+)', path)
        cells = row.find_all('td')
        if not m or len(cells) < 4:
            raise RuntimeError('目录行结构异常')
        title = a.get_text(' ', strip=True)
        case_id = int(m.group(1))
        if case_id in seen:
            continue
        seen.add(case_id)
        if keyword.strip().casefold() in title.casefold():
            result.append({'case_id': case_id, 'title': title, 'introduced': cells[1].get_text(' ', strip=True), 'culminated': cells[2].get_text(' ', strip=True), 'type': cells[3].get_text(' ', strip=True), 'url': urljoin(BASE, path)})
    return {'source': '国际法院公开全部案件目录', 'keyword': keyword.strip(), 'total': len(result), 'items': result, 'notice': '本地对官方目录英文标题作子串匹配；不是全文搜索，目录是否完整及判决效力以国际法院为准。'}

def documents(case_id):
    if isinstance(case_id, bool) or not isinstance(case_id, int) or (not 1 <= case_id <= 9999):
        raise ValueError('案件编号须为 1–9999 整数')
    s = _get(f'case/{case_id}')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        url = urljoin(BASE, a['href'])
        p = urlsplit(url)
        label = a.get_text(' ', strip=True)
        if p.scheme != 'https' or p.hostname not in ('www.icj-cij.org', 'api.icj-cij.org') or (not p.path.startswith(f'/sites/default/files/case-related/{case_id}/')) or (not p.path.lower().endswith('.pdf')) or (url in seen) or (not label):
            continue
        seen.add(url)
        items.append({'label': label, 'url': url})
    if not items:
        raise RuntimeError('案件无可识别公开 PDF 链接，或页面结构变化')
    return {'source': '国际法院案件页面', 'case_id': case_id, 'items': items, 'notice': '返回判决、意见书、新闻稿等链接；标题须逐条核验，不默认所有链接为判决正文。'}
