"""Bounded ArticleFirst search via the library's authorized FirstSearch session."""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ENTRY = 'https://firstsearch.oclc.org/FSIP'

def search(query, database='ArticleFirst', page=1):
    if not 1 <= int(page) <= 5:
        raise ValueError('page 限 1–5')
    if database not in ('ArticleFirst', 'ClasePeriodica', 'Ebooks', 'ECO', 'ERIC', 'GPO', 'MEDLINE', 'OpenAccessContent', 'SCIPIO', 'WorldCat', 'WorldCatDissertations'):
        raise ValueError('未知 FirstSearch 数据库')
    if not query.strip() or len(query) > 200:
        raise ValueError('请输入 1–200 字符的检索词')
    s = requests.Session()
    r = s.get(ENTRY, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    if 'ZHEJIANG UNIV' not in p.get_text(' ', strip=True):
        raise RuntimeError('FirstSearch 未识别浙江大学机构身份，请检查网络认证')
    link = next((a for a in p.find_all('a', href=True) if a.get_text(strip=True) == database), None)
    if not link:
        listing = next((a for a in p.find_all('a', href=True) if a.get_text(strip=True) == 'List All Databases'), None)
        if not listing:
            raise RuntimeError('首页缺少数据库目录')
        rr = s.get(urljoin(r.url, listing['href']), timeout=25)
        rr.raise_for_status()
        p = BeautifulSoup(rr.content, 'html.parser')
        r = rr
        link = next((a for a in p.find_all('a', href=True) if a.get_text(strip=True) == database), None)
    if not link:
        raise RuntimeError('目录缺少所选数据库入口')
    target = urljoin(r.url, link['href'])
    if urlparse(target).hostname != 'firstsearch.oclc.org':
        raise RuntimeError('未知检索入口')
    r = s.get(target, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    form = next((f for f in p.find_all('form') if 'FSQUERY' in f.get('action', '')), None)
    if not form:
        raise RuntimeError('未找到检索表单')
    payload = {'action': 'Search', 'dbname': database, 'term1': query, 'index1': 'kw:', 'term2': '', 'term3': ''}
    r = s.post(urljoin(r.url, form['action']), data=payload, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    title = p.title.get_text(' ', strip=True) if p.title else ''
    if 'List of Records' not in title and '记录列表' not in title:
        raise RuntimeError('检索未返回结果列表，可能没有结果或服务状态改变')
    for _ in range(1, int(page)):
        link = next((a for a in p.find_all('a', href=True) if any(('Next page of results' in (im.get('alt') or '') for im in a.find_all('img')))), None)
        if link is None:
            raise ValueError('结果没有下一页')
        target = urljoin(r.url, link['href'])
        if urlparse(target).hostname != 'firstsearch.oclc.org':
            raise RuntimeError('未知分页入口')
        r = s.get(target, timeout=25)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
    items = []
    for tr in p.find_all('tr'):
        if not tr.find('input', attrs={'name': re.compile('^BookMark_')}):
            continue
        a = next((x for x in tr.find_all('a', href=True) if 'fetchtype=fullrecord' in x['href'] and x.get_text(' ', strip=True)), None)
        if a:
            items.append({'title': a.get_text(' ', strip=True), 'record_text': tr.get_text(' ', strip=True)})
    if not items:
        raise RuntimeError('未提取到题录，页面可能改版')
    return {'source': 'OCLC FirstSearch / ' + database, 'institution': 'ZHEJIANG UNIV', 'query': query, 'page': int(page), 'items': items, 'note': '当前仅返回指定页简略题录，不保留临时会话链接；不证明全文或各题录均为馆藏。'}
