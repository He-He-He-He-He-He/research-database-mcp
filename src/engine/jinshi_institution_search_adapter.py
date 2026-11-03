"""历代进士登科数据库学校 IP 姓名检索，保留原始字段。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'https://examination.ancientbooks.cn/docDengke/'

def search(name, page=1, field='name'):
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100 or any((ord(c) < 32 for c in name)):
        raise ValueError('姓名须为1–100字单行文本')
    if type(page) is not int or not 1 <= page <= 1000:
        raise ValueError('页码须为1–1000')
    fields = {'name': 'fullName', 'dynasty': 'dynasty', 'subject': 'subject', 'birth': 'sourceBirth'}
    if field not in fields:
        raise ValueError('field 须为 name、dynasty、subject 或 birth')
    q = name.strip()
    params = {'bookType': '0', 'searchType': '1', 'title': q, 'type': fields[field], 'pageNo': str(page), 'pageSize': '15'}
    with requests.Session() as s:
        r = s.get(BASE + 'dkSearch.jspx', params=params, timeout=20)
        r.raise_for_status()
        text = BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True)
        if '当前机构: 浙江大学' not in text:
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.get(BASE + 'dkSearchTable.jspx', params=params, timeout=25)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError:
            raise RuntimeError('登科检索未返回 JSON') from None
    if not isinstance(j, dict) or j.get('code') != 0 or type(j.get('count')) is not int or (j['count'] < 0) or (not isinstance(j.get('data'), list)) or (len(j['data']) > 15):
        raise RuntimeError('登科检索响应异常')
    if any((not isinstance(x, dict) or not x.get('content_id') or (not isinstance(x.get('fullName'), str)) for x in j['data'])):
        raise RuntimeError('登科题录字段缺失')
    result = {'source': '历代进士登科数据库', 'institution': '浙江大学', 'query': q, 'page': page, 'total': j['count'], 'source_total_pages': j.get('totalPage'), 'items': j['data'], 'note': '学校 IP 会话的姓名检索，保留原始字段与高亮 HTML；响应未回显页码，已按本次请求返回；空页可能为无结果或超过页数，站方零结果仍报告1页。详情使用站方字体编码，未解析；不代表逐条全文权限。'}
    if field != 'name':
        result['field_requested'] = field
        result['note'] = '学校 IP 会话按站方字段检索，保留原始字段及高亮；站方未回显页码或字段，空页可能为无结果或超页，站方零结果仍报告1页；匹配方式需核对。详情字体编码未解析。'
    return result
