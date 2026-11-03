"""CADAL special-collection catalog search, without images or full text."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://tecang.cadal.edu.cn/metadata/api/tsk/port/v1.0/searchAll'
COLLECTIONS = {'maps': 'MUST_map', 'manuscripts': 'xiebeniterature', 'photos': 'photo', 'inscriptions': 'inscriptions', 'posters': 'poster', 'taiwan_resistance': 'twkrwx', 'wartime': 'SinoJpnDocs', 'chiang': 'cksdb', 'arts': 'zhysbk', 'pathology': 'pathology'}

def _field(seq, key):
    if not isinstance(seq, list):
        return None
    for x in seq:
        if isinstance(x, dict) and x.get('key') == key and isinstance(x.get('value'), dict):
            return x['value'].get('fieldvalue')
    return None

def _clean(v):
    return BeautifulSoup(v, 'html.parser').get_text('', strip=True) if isinstance(v, str) else v

def search(collection, keyword, page=1, limit=10, session=None, field='all'):
    if collection not in COLLECTIONS:
        raise ValueError('不支持的专题库')
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or '^^' in keyword:
        raise ValueError('关键词须为 1–100 字且不能包含 ^^')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 30):
        raise ValueError('每页最多 30 条')
    fields = {'photos': {'title': 'title', 'creator': 'creator', 'date': 'date', 'spatial': 'spatial', 'collection': 'collection', 'subject': 'subject'}, 'arts': {'title': 'title', 'era': 'era'}, 'inscriptions': {'title': 'title', 'date': 'date'}, 'chiang': {'title': 'title', 'creator': 'creator', 'key-figure': 'key_figure'}, 'manuscripts': {'title': 'title', 'digital-id': 'ID', 'qzwh': 'qzwh', 'filenum': 'filenum', 'filmnum': 'filmnum', 'collector': 'collector', 'years': 'years', 'note': 'note'}, 'maps': {'title': 'title', 'creator': 'creator', 'language': 'language', 'year': 'year', 'publisher': 'publisher'}, 'posters': {'title': 'title', 'creator': 'creator', 'publisher': 'publisher', 'date': 'date'}, 'wartime': {'title': 'title', 'creator': 'creator', 'publisher': 'Publisher', 'date': 'date'}, 'taiwan_resistance': {'title': 'title', 'creator': 'creator', 'issue': 'issue'}, 'pathology': {'title': 'title', 'creator': 'creator', 'publisher': 'publisher', 'date': 'date', 'type': 'type', 'isbn': 'isbn', 'relation': 'relation', 'classification': 'classification'}}
    if field != 'all' and field not in fields.get(collection, {}):
        raise ValueError('该专题与字段组合尚未验证')
    source_field = 'all' if field == 'all' else fields[collection][field]
    q = keyword.strip()
    s = session or requests.Session()
    body = {'dbname': COLLECTIONS[collection], 'collectionSearchType': 'onecollectionsearch', 'curpage': page, 'pagesize': limit, 'sfields': [source_field + '^^' + q + '^^wildcard'], 'sortWord': ['hitcount:1']}
    r = s.post(URL, json=body, timeout=20)
    r.raise_for_status()
    j = r.json()
    d = j.get('data') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('code') != 200 or (not isinstance(d, dict)) or (type(d.get('total')) is not int) or (d['total'] < 0) or (not isinstance(d.get('dataTablemaps'), list)) or (len(d['dataTablemaps']) > limit):
        raise RuntimeError('站方检索响应异常')
    if collection in ('maps', 'photos', 'manuscripts'):
        expected = min(limit, max(0, d['total'] - (page - 1) * limit))
        if len(d['dataTablemaps']) != expected:
            raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in d['dataTablemaps']:
        if not isinstance(x, dict):
            raise RuntimeError('题录异常')
        c = x.get('custom')
        n = x.get('notDisplayed')
        ident = _field(n, 'docid')
        title = _clean(_field(c, 'title'))
        if ident is None or not isinstance(title, str) or (not title):
            raise RuntimeError('题录缺少编号或标题')
        item = {'id': ident, 'database': _field(n, 'dbname'), 'collection': _field(n, 'dbtitle'), 'title': title, 'creator': _clean(_field(c, 'creator')), 'year': _field(c, 'year')}
        display_omitted = []
        for key in ('title', 'creator'):
            value = _field(c, key)
            valid = value is None or isinstance(value, str)
            if not valid or (isinstance(value, str) and re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', value, re.I)):
                item['source_' + key + '_raw'] = None
                display_omitted.append(key)
            else:
                item['source_' + key + '_raw'] = value
        if display_omitted:
            item['source_display_fields_omitted'] = display_omitted
        if field != 'all' and collection != 'manuscripts':
            value = _field(c, source_field)
            valid = value is None or isinstance(value, str) or (isinstance(value, list) and all((isinstance(v, str) for v in value)))
            strings = [value] if isinstance(value, str) else value if isinstance(value, list) and valid else []
            if not valid or any((re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', v, re.I) for v in strings)):
                item['source_filter_value_raw'] = None
                item['source_filter_value_omitted'] = True
            else:
                item['source_filter_value_raw'] = value
        if collection == 'manuscripts':
            omitted = []
            for key in ('author', 'years', 'collector', 'note', 'filenum', 'qzwh', 'num', 'references', 'ID', 'filmnum'):
                value = _field(c, key)
                valid = value is None or isinstance(value, str) or (isinstance(value, list) and all((isinstance(v, str) for v in value)))
                strings = [value] if isinstance(value, str) else value if isinstance(value, list) and valid else []
                if not valid or any((re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', v, re.I) for v in strings)):
                    item['source_' + key + '_raw'] = None
                    omitted.append(key)
                else:
                    item['source_' + key + '_raw'] = value
            if omitted:
                item['source_fields_omitted'] = omitted
        items.append(item)
    result = {'source': 'CADAL 专题资料库', 'collection': collection, 'query': q, 'page': page, 'page_size': limit, 'total': d['total'], 'items': items[:limit], 'note': '仅返回选定专题的目录元数据，条目原始数据库标识与专题代码可能不同；写本 source_*_raw 保留上游原始字段及高亮 HTML，含链接、凭据标记或异常结构的字段省略并标记；机构身份、影像和全文权限未验证。'}
    result['note'] += ' source_title_raw 和 source_creator_raw 保留标题及责任者原值与高亮，含链接、凭据标记或异常结构时省略并标记。'
    if collection in ('maps', 'photos', 'manuscripts'):
        result['note'] += ' 已按总数和请求页码校验条数；站方不回显页码，数据可能变化。'
    if field != 'all':
        result['field_requested'] = field
        result['note'] += ' 按专题站方字段搜索，可能关联简繁或分词；站方未回显字段或页码，需核对相关性，字段名称和原始含义以源站为准。'
    return result
