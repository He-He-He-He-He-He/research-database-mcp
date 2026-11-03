"""中华经典古籍库机构会话图书聚合检索，仅未加字体编码的书目字段。"""
import release_runtime
import json
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://jingdian.ancientbooks.cn/v1/'
HEADERS = {'siteid': '1', 'X-Requested-With': 'XMLHttpRequest'}

def _plain(v):
    return BeautifulSoup(v, 'html.parser').get_text('', strip=True) if isinstance(v, str) else v

def search(keyword, page=1, limit=5, field='text'):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 20 or any((ord(c) < 32 for c in keyword)):
        raise ValueError('关键词须为1–20字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页最多10条')
    fields = {'text': 'txt', 'book-title': 'book_title', 'author': 'book_author', 'publisher': 'book_publisher'}
    if field not in fields:
        raise ValueError('不支持的检索字段')
    q = keyword.strip()
    body = {'libId': 6, 'modelId': 2, 'catId': None, 'sortMethod': 1, 'isAdvance': field != 'text', 'isWordDistance': False, 'distance': False, 'useSynonyms': True, 'useProperNouns': False, 'conditionJson': json.dumps([{'column': fields[field], 'searchTxt': q, 'relation': 'and'}], ensure_ascii=False), 'myBookSelf': False, 'crossingZhu': False, 'ignorePunc': True, 'orderByColumn': 'score', 'hasBuy': False, 'isAsc': 'desc', 'needRecord': False, 'pageNum': page, 'pageSize': limit}
    with requests.Session() as s:
        r = s.get(BASE + 'user/checkuserlogininfo', headers=HEADERS, timeout=20)
        r.raise_for_status()
        j = r.json()
        ins = j.get('data', {}).get('ins') if isinstance(j, dict) and isinstance(j.get('data'), dict) else None
        if not isinstance(ins, dict) or ins.get('name') != '浙江大学':
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.post(BASE + 'search', json=body, headers=HEADERS, timeout=25)
        r.raise_for_status()
        j = r.json()
    d = j.get('data') if isinstance(j, dict) and j.get('success') is True and (j.get('code') == 200) else None
    if not isinstance(d, dict) or d.get('pageNum') != page or d.get('pageSize') != limit or (type(d.get('total')) is not int) or (d['total'] < 0) or (not isinstance(d.get('rows'), list)) or (len(d['rows']) > limit):
        raise RuntimeError('原站图书聚合响应异常')
    expected = min(limit, max(0, d['total'] - (page - 1) * limit))
    if len(d['rows']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for row in d['rows']:
        if not isinstance(row, dict) or type(row.get('contentId')) is not int or (not isinstance(row.get('title'), str)):
            raise RuntimeError('书目编号或标题缺失')
        item = {'id': row['contentId'], 'title': _plain(row['title']), 'author': _plain(row.get('author')), 'editor': _plain(row.get('author2')), 'publisher': _plain(row.get('publisher')), 'version': _plain(row.get('version')), 'source': _plain(row.get('source')), 'has_auth_raw': row.get('hasAuth')}
        omitted = []
        for key in ('title', 'author', 'author2', 'publisher', 'version', 'source'):
            v = row.get(key)
            if v is not None and (not isinstance(v, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=|[\\ue000-\\uf8ff\\U000f0000-\\U000ffffd\\U00100000-\\U0010fffd]', v, re.I)):
                item['source_' + key + '_raw'] = None
                omitted.append(key)
            else:
                item['source_' + key + '_raw'] = v
        for out in ('title', 'author', 'editor', 'publisher', 'version', 'source'):
            value = item[out]
            if value is not None and (not isinstance(value, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:token|session|sid|apikey|api_key)\\s*=|[\\ue000-\\uf8ff\\U000f0000-\\U000ffffd\\U00100000-\\U0010fffd]', value, re.I)):
                item[out] = None
        if omitted:
            item['source_fields_omitted'] = omitted
        items.append(item)
    result = {'source': '中华经典古籍库', 'institution': '浙江大学', 'query': q, 'page': page, 'page_size': limit, 'source_total': d['total'], 'items': items[:limit], 'note': '原站全文检索条件下的图书聚合结果，支持同义词；站方 hasAuth 是原始标记，不代表已验证逐书全文。简介和正文使用网站字体编码，未输出或解码。'}
    if field != 'text':
        result['field_requested'] = field
        result['note'] = '浙大机构图书聚合题录，站方未回显检索条件，单字段匹配须核对；hasAuth 为原始标记，未验证逐书权限。正文和简介的字体编码未解码或输出。'
    result['note'] += ' source_*_raw 保留安全书目原字段及高亮；含链接、疑似凭据、私用区字符或异常结构时省略并标记。已按总数和回显页码校验条数，数据可能变化。'
    return result
