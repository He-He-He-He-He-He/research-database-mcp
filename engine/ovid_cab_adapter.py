"""Ovid 平台 CAB Abstracts 首屏检索；每次使用新的临时机构会话。"""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ENTRY = 'https://libdb.zju.edu.cn/s/lib/libtb/turning/1005'

def _ovid_url(base, href):
    u = urljoin(base, href)
    p = urlparse(u)
    if p.scheme != 'https' or p.hostname not in ('ovidsp.dc1.ovid.com', 'ovidsp.dc2.ovid.com'):
        raise RuntimeError('Ovid 返回了非预期地址')
    return u

def _request(session, method, url, **kwargs):
    try:
        response = getattr(session, method)(url, **kwargs)
        response.raise_for_status()
        return response
    except requests.RequestException as exc:
        raise RuntimeError('Ovid 网络或服务请求失败：' + type(exc).__name__) from None

def search_cab(query: str, limit: int=10, start: int=1) -> dict:
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('检索词须为 1 至 200 字')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit 须为 1 至 50')
    if type(start) is not int or not 1 <= start <= 1000000:
        raise ValueError('start 须为 1 至 1000000')
    session = requests.Session()
    r = _request(session, 'get', ENTRY, timeout=25)
    if urlparse(r.url).hostname not in ('ovidsp.dc1.ovid.com', 'ovidsp.dc2.ovid.com') or urlparse(r.url).scheme != 'https':
        raise RuntimeError('馆藏入口未进入预期 Ovid 服务，可能需要机构登录')
    page = BeautifulSoup(r.content, 'html.parser')
    link = next((a for a in page.select('a.resource-dblink[href]') if 'CAB Abstracts + Full Text' in a.get_text(' ', strip=True)), None)
    if not link:
        raise RuntimeError('Ovid 未提供 CAB Abstracts 资源，可能需要机构授权')
    r = _request(session, 'get', _ovid_url(r.url, link['href']), timeout=25)
    page = BeautifulSoup(r.content, 'html.parser')
    form = page.select_one('form#sfeasy')
    if not form or not form.get('action'):
        raise RuntimeError('Ovid 未显示预期搜索表单')
    data = {i['name']: i.get('value', '') for i in form.select('input[type=hidden][name]')}
    data.update({'textBox': query.strip(), 'submit:Perform Search|1': '搜索'})
    r = _request(session, 'post', _ovid_url(r.url, form['action']), data=data, timeout=45)
    page = BeautifulSoup(r.content, 'html.parser')
    info = page.select_one('#searchaid-numbers')
    if not info:
        raise RuntimeError('Ovid 未返回可识别的结果页面')
    match = re.search('([\\d,]+)\\s*个文本结果', info.get_text(' ', strip=True))
    if not match:
        raise RuntimeError('Ovid 结果数格式发生变化')
    total = int(match.group(1).replace(',', ''))
    resource = page.select_one('#ovid-resources-link-block')
    if not resource or 'CAB Abstracts + Full Text' not in resource.get_text(' ', strip=True):
        raise RuntimeError('Ovid 未确认 CAB 资源')
    if start <= total and start > 1:
        nav = page.select_one('form#nav-results')
        button = nav.select_one('#toolbar-go-option input[type=submit][name]') if nav else None
        if not nav or not nav.get('action') or (not button):
            raise RuntimeError('Ovid 未显示结果跳转表单')
        data = {i['name']: i.get('value', '') for i in nav.select('input[type=hidden][name]')}
        data.update({'startRecord': str(start), button['name']: button.get('value', '')})
        r = _request(session, 'post', _ovid_url(r.url, nav['action']), data=data, timeout=45)
        page = BeautifulSoup(r.content, 'html.parser')
    if start <= total:
        position = page.select_one('#startRecord')
        explain = page.select_one('#searchaid-explain')
        if not position or position.get('value') != str(start) or (not explain) or (query.strip() not in explain.get_text(' ', strip=True)):
            raise RuntimeError('Ovid 未确认资源、检索词或起始记录')
    items = []
    rows = page.select('td.titles-record') if start <= total else []
    for offset, row in enumerate(rows[:limit]):

        def get(selector):
            el = row.select_one(selector)
            return el.get_text(' ', strip=True) if el else None
        title = get('.citation_title')
        if not title:
            raise RuntimeError('Ovid 返回的记录缺少题名')
        tr = row.find_parent('tr')
        number = re.match('^\\s*(\\d+)\\.', tr.get_text(' ', strip=True) if tr else '')
        if not number or int(number.group(1)) != start + offset:
            raise RuntimeError('Ovid 返回的记录序号不连续')
        items.append({'title': title, 'authors': get('.article-authors'), 'source': get('.titles-source'), 'publication_type': get('.titles-pt'), 'abstract': get('.titles-ab p')})
    if len(items) != min(limit, max(0, total - start + 1)):
        raise RuntimeError('Ovid 返回的题录数量与请求范围不一致')
    return {'source': 'Ovid CAB Abstracts + Full Text', 'query': query.strip(), 'total': total, 'start': start, 'items': items, 'scope': '从指定序号连续返回至多 limit 条；不表示 CABI 电子书全部内容或全文可用', 'library_entry': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1005'}
