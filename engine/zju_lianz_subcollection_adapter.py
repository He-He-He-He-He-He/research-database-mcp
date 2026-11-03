"""Bounded title search in a single ZJU integrity literature subcollection."""
import release_runtime
import html
import re
import requests
from urllib.parse import urlsplit, parse_qs
BASE = 'http://lianz.zju.edu.cn/'
CODES = {'CULTURALHISTORY', 'WONDERFULVIDEO', 'LAW', 'CLEANGOVERNMENTPIC', 'GREATSTATE', 'BOOKREVIEW', 'THEORETICALLITERATU', 'CLEANGOVERNANCEBOOK'}

def annotate_opac_url(item):
    u = urlsplit(item.get('url') or '')
    q = parse_qs(u.query, keep_blank_values=True)
    if u.hostname == 'opac.zju.edu.cn' and q.get('find_code') == ['SYS'] and (q.get('request') == ['']):
        item['url_warning'] = '原站馆藏链接缺少系统号，无法定位具体书目；可用题名在浙大 OPAC 另行检索。'
    return item

def validate_page_data(data, page):
    if not isinstance(data, dict) or not isinstance(data.get('countNumber'), int) or isinstance(data.get('countNumber'), bool) or (data['countNumber'] < 0) or (not isinstance(data.get('data'), list)) or (len(data['data']) != min(20, max(0, data['countNumber'] - (page - 1) * 20))) or any((not isinstance(row, dict) for row in data['data'])):
        raise ValueError('subcollection total or page records inconsistent')

def search(keyword, code='LAW', page=1, timeout=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must contain 1 to 100 characters')
    if code not in CODES:
        raise ValueError('unsupported subcollection code')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be an integer from 1 to 100')
    s = requests.Session()
    res = s.post(BASE + 'index/getDBConfigList', data={'classcode': '003'}, timeout=timeout)
    res.raise_for_status()
    config = res.json().get('data', [])
    matches = [x for x in config if x.get('dbcode') == code and x.get('defaultselected') == '1']
    if len(matches) != 1:
        raise ValueError('subcollection configuration not available')
    x = matches[0]
    db = {'id': x['dbid'], 'code': x['dbcode'], 'name': x['cnname']}
    body = {'classcode': '003', 'selectField': 'sys_fld_sysid,题名,密级,分类,关键词,语言,作者单位,发表时间', 'searchConditions': [{'isAnd': 'and', 'field': '题名', 'fieldView': '题名', 'value': keyword.strip(), 'vague': '%'}], 'dbList': [db], 'databasecode': code, 'limit': '20', 'treekey': '所属单位', 'treeSearchConditions': [], 'hospitalNames': '', 'pageNumber': page, 'saveLog': False, 'orderby': '题名', 'sort': 'desc'}
    res = s.post(BASE + 'DigitalResources/getMultiSearchList', json=body, timeout=timeout)
    res.raise_for_status()
    data = res.json()
    validate_page_data(data, page)
    records = []
    for row in data['data']:
        if row.get('databasename') != db['name']:
            raise ValueError('response includes an unexpected subcollection')
        item = {'title': html.unescape(re.sub('<[^>]*>', '', row.get('题名', ''))), 'source': row.get('databasename'), 'date': row.get('发表时间'), 'url': row.get('jumpUrl')}
        records.append(annotate_opac_url(item))
    return {'source': '浙江大学廉政文献专题库', 'subcollection': db['name'], 'code': code, 'keyword': keyword.strip(), 'page': page, 'total': data['countNumber'], 'records': records, 'note': '站点题录及外链不保证法律现行有效；HTTP 明文，勿提交敏感词。'}
