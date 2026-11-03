"""中国数字方志库校园会话单册书目详情。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from digital_fangzhi_ip_catalog_adapter import BASE
ID = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.I)

def detail(book_id, expected_title):
    if not isinstance(book_id, str) or not ID.fullmatch(book_id):
        raise ValueError('书目编号须为 UUID')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200:
        raise ValueError('须提供完整书目标题')
    with requests.Session() as s:
        r = s.get(BASE, timeout=20)
        r.raise_for_status()
        if '欢迎您：浙江大学' not in BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True):
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.post(BASE + 'BookDetails.ashx', data={'pSet': '0', 'pID': book_id, 'list_pID': '', 'pos': ''}, timeout=20)
        r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    fields = []
    for tr in p.select('tr'):
        t = tr.find_all('td', recursive=False)
        if len(t) == 3:
            key = t[1].get_text(' ', strip=True).rstrip(':：')
            value = t[2].get_text(' ', strip=True)
            if key and value:
                fields.append({'name': key, 'value': value})
    title = next((x['value'] for x in fields if x['name'] == '題名與責任'), None)
    if book_id.lower() not in r.text.lower() or not title or re.sub('\\s+', '', expected_title) not in re.sub('\\s+', '', title):
        raise RuntimeError('详情编号或标题与检索结果不一致')
    return {'source': '中国数字方志库', 'institution': '浙江大学', 'id': book_id, 'title': expected_title, 'fields': fields, 'note': '校园内网 HTTP，字段取自站方书目详情；未读取正文或确认全文权限。'}
