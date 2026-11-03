"""尚古汇典典籍整理文献数据库公开图书题录。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from gujidh_classics_catalog_adapter import BASE, DB

def plain(v):
    return BeautifulSoup(v, 'html.parser').get_text('', strip=True) if isinstance(v, str) else v

def search(keyword, page=1, limit=5, session=None, database='classics'):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or any((ord(c) < 32 for c in keyword)):
        raise ValueError('关键词须为1–100字单行文本')
    if type(page) is not int or page < 1 or type(limit) is not int or (not 1 <= limit <= 10):
        raise ValueError('页码须为正整数，每页1–10条')
    databases = {'classics': (DB, '典籍整理文献数据库'), 'wenyuan': ('100020122', '文渊阁四库全书数据库')}
    if database not in databases:
        raise ValueError('不支持的数据库')
    db_id, db_name = databases[database]
    q = keyword.strip()
    body = {'keywords': q, 'page': page, 'size': limit, 'sortBy': {'name': 'time', 'method': 'DESC'}, 'type': 'book', 'databaseId': [db_id], 'terminalType': 'pc'}
    r = (session or requests.Session()).post(BASE + 'ancient-books/global/search/normal', json=body, timeout=25)
    r.raise_for_status()
    j = r.json()
    d = j.get('result') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('status') != 200 or (not isinstance(d, dict)) or (d.get('success') is not True) or (d.get('type') != 'book'):
        raise RuntimeError('站方图书检索响应异常')
    c = d.get('bookResults')
    note = '公开书目匹配范围由站方决定，不保证书名精确匹配；学校机构身份和全文权限未验证，不读取简介、正文、图片及链接。'
    if database == 'classics':
        note += ' 第五期子集未验证。'
    if c is None:
        return {'source': '尚古汇典·' + db_name, 'query': q, 'page': page, 'page_size': limit, 'total': None, 'items': [], 'note': note + ' 站方未提供总数，不能断定为零。'}
    if not isinstance(c, dict) or type(c.get('totalNumber')) is not int or c['totalNumber'] < 0 or (c.get('firstRow') != (page - 1) * limit) or (c.get('maxRows') != limit) or (not isinstance(c.get('results'), list)) or (len(c['results']) > limit):
        raise RuntimeError('站方书目分页或总数异常')
    if c['totalNumber'] < 10000:
        expected = min(limit, max(0, c['totalNumber'] - (page - 1) * limit))
        if len(c['results']) != expected:
            raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in c['results']:
        if not isinstance(x, dict) or not isinstance(x.get('bookId'), str) or (not isinstance(x.get('bookName'), str)) or (not any((isinstance(z, dict) and z.get('databaseId') == db_id for z in x.get('databaseList') or []))):
            raise RuntimeError('书目编号、标题或来源异常')
        if x.get('classify') is not None and (not isinstance(x.get('classify'), str)):
            raise RuntimeError('分类字段类型异常')
        item = {'id': x['bookId'], 'title': plain(x['bookName']), 'author': plain(x.get('author')), 'publisher': plain(x.get('publisher')), 'classification_raw': x.get('classify')}
        omitted = []
        for k, out in (('bookName', 'title_raw'), ('author', 'author_raw'), ('publisher', 'publisher_raw')):
            v = x.get(k)
            if v is not None and (not isinstance(v, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', v, re.I)):
                item[out] = None
                omitted.append(k)
            else:
                item[out] = v
        classification = x.get('classify')
        if isinstance(classification, str) and re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', classification, re.I):
            item['classification_raw'] = None
            omitted.append('classify')
        if omitted:
            item['source_fields_omitted'] = omitted
        items.append(item)
    return {'source': '尚古汇典·' + db_name, 'query': q, 'page': page, 'page_size': limit, 'total': c['totalNumber'], 'items': items, 'note': note + ' 原始书名、作者与出版者保留高亮；含链接、疑似凭据或异常结构的原字段省略并标记。低于10000时按请求页次校验条数；连续翻页须保持页长一致，上游数据及排序可能变化。'}
