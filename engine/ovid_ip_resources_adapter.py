"""Ovid 学校 IP 会话的 MEDLINE、LWW 期刊及全刊摘要题录。"""
import release_runtime
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from ovid_cab_adapter import ENTRY, _ovid_url, _request
RESOURCES = {'medline': ('medall', 'Ovid MEDLINE(R) ALL 1946 to', 'Ovid MEDLINE ALL，覆盖年份及更新日以资源页为准；并非 PubMed 全部内容。'), 'lww': ('yrovft', 'Zhejiang University Full-Text Journals(LWW Journals)', '源站标为浙江大学 LWW 期刊集合；集合名不保证每篇全文或其他产品权限。'), 'journals': ('ovft', 'Search All Ovid Journals(Abstracts Only)', '全平台期刊摘要目录，不代表浙江大学订购范围或全文权限。')}

def search(query, resource='medline', limit=10, start=1, include_abstract=False):
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 200 or re.search('[\\x00-\\x1f]', query):
        raise ValueError('检索词须为 1–200 字单行文本')
    if type(include_abstract) is not bool:
        raise ValueError('include_abstract 必须是布尔值')
    if resource not in RESOURCES:
        raise ValueError('资源须为 medline、lww 或 journals')
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('limit 须为 1–50')
    if type(start) is not int or not 1 <= start <= 1000000:
        raise ValueError('start 须为 1–1000000')
    db, expected, scope = RESOURCES[resource]
    s = requests.Session()
    r = _request(s, 'get', ENTRY, timeout=25)
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname not in ('ovidsp.dc1.ovid.com', 'ovidsp.dc2.ovid.com'):
        raise RuntimeError('馆藏入口未进入预期 Ovid 服务')
    page = BeautifulSoup(r.content, 'html.parser')
    a = next((x for x in page.select('a.resource-dblink[href]') if x.get('db_full_name') == db), None)
    if not a:
        raise RuntimeError('Ovid 未显示所选资源')
    r = _request(s, 'get', _ovid_url(r.url, a['href']), timeout=25)
    page = BeautifulSoup(r.content, 'html.parser')
    f = page.select_one('form#sfeasy')
    if not f or not f.get('action'):
        raise RuntimeError('Ovid 未显示预期检索表单')
    data = {x['name']: x.get('value', '') for x in f.select('input[type=hidden][name]')}
    data.update({'textBox': query.strip(), 'submit:Perform Search|1': '搜索'})
    r = _request(s, 'post', _ovid_url(r.url, f['action']), data=data, timeout=45)
    page = BeautifulSoup(r.content, 'html.parser')
    info = page.select_one('#searchaid-numbers')
    res = page.select_one('#ovid-resources-link-block')
    match = re.search('([\\d,]+)\\s*个文本结果', info.get_text(' ', strip=True)) if info else None
    if not match or not res or expected not in res.get_text(' ', strip=True):
        raise RuntimeError('Ovid 未确认所选资源或结果总数')
    total = int(match.group(1).replace(',', ''))
    resource_raw = res.get_text(' ', strip=True)
    if start <= total and start > 1:
        nav = page.select_one('form#nav-results')
        btn = nav.select_one('#toolbar-go-option input[type=submit][name]') if nav else None
        if not nav or not nav.get('action') or (not btn):
            raise RuntimeError('Ovid 未显示结果跳转表单')
        data = {x['name']: x.get('value', '') for x in nav.select('input[type=hidden][name]')}
        data.update({'startRecord': str(start), btn['name']: btn.get('value', '')})
        r = _request(s, 'post', _ovid_url(r.url, nav['action']), data=data, timeout=45)
        page = BeautifulSoup(r.content, 'html.parser')
    if start <= total:
        position = page.select_one('#startRecord')
        explain = page.select_one('#searchaid-explain')
        if not position or position.get('value') != str(start) or (not explain) or (query.strip() not in explain.get_text(' ', strip=True)):
            raise RuntimeError('Ovid 未确认检索词或起始记录')
    rows = page.select('td.titles-record') if start <= total else []
    items = []
    for offset, row in enumerate(rows[:limit]):

        def txt(css):
            x = row.select_one(css)
            return x.get_text(' ', strip=True) if x else None
        title = txt('.citation_title')
        tr = row.find_parent('tr')
        n = re.match('^\\s*(\\d+)\\.', tr.get_text(' ', strip=True) if tr else '')
        if not title or not n or int(n.group(1)) != start + offset:
            raise RuntimeError('Ovid 题名或记录序号异常')
        item = {'title': title, 'authors_raw': txt('.article-authors'), 'source_raw': txt('.titles-source'), 'publication_type_raw': txt('.titles-pt')}
        if include_abstract:
            item['abstract_raw'] = txt('.titles-ab p')
        items.append(item)
    if len(items) != min(limit, max(0, total - start + 1)):
        raise RuntimeError('Ovid 返回的题录数量与请求范围不一致')
    return {'source': 'Ovid IP 机构会话', 'resource': resource, 'resource_name_raw': resource_raw, 'library_info': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1005', 'query': query.strip(), 'start': start, 'total': total, 'items': items, 'note': scope + ' 检索含站方扩展词；起始记录和每条序号经页面核验。' + ('摘要为结果页中显示的原文，空值不表示文章没有摘要；' if include_abstract else '默认仅返回题录；') + '不取正文或会话链接；未识别结果页时报错，不猜测无结果。'}
