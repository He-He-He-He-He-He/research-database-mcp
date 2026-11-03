"""Public citation metadata from Gujidh ancient-book literature database."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.gujidh.com/'
DB = '100013122'

def _plain(v):
    return BeautifulSoup(v, 'html.parser').get_text('', strip=True) if isinstance(v, str) else v

def search(keyword, page=1, limit=5, session=None, database='classics'):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    databases = {'classics': (DB, '典籍整理文献数据库'), 'wenyuan': ('100020122', '文渊阁四库全书数据库')}
    if database not in databases:
        raise ValueError('不支持的数据库')
    db_id, db_name = databases[database]
    q = keyword.strip()
    s = session or requests.Session()
    body = {'keywords': q, 'page': page, 'size': limit, 'sortBy': {'name': 'time', 'method': 'DESC'}, 'type': 'content', 'databaseId': [db_id], 'terminalType': 'pc'}
    r = s.post(BASE + 'ancient-books/global/search/normal', json=body, timeout=25)
    r.raise_for_status()
    j = r.json()
    d = j.get('result') if isinstance(j, dict) else None
    if not isinstance(j, dict) or j.get('status') != 200 or (not isinstance(d, dict)) or (d.get('success') is not True) or (d.get('type') != 'content'):
        raise RuntimeError('站方搜索响应异常')
    c = d.get('contentResults')
    if c is None:
        return {'source': '尚古汇典·' + db_name, 'query': q, 'page': page, 'total': None, 'items': [], 'note': '原站返回空内容结果，未提供总数，不能断定为零；学校机构身份和全文权限未验证。' if database == 'wenyuan' else '原站返回空内容结果，未提供总数，不能断定为零；学校机构身份、第五期子集和全文权限未验证。'}
    if not isinstance(c, dict) or type(c.get('totalNumber')) is not int or c['totalNumber'] < 0 or (not isinstance(c.get('results'), list)) or (len(c['results']) > limit):
        raise RuntimeError('站方目录数量异常')
    if database == 'wenyuan' and (c.get('firstRow') != (page - 1) * limit or c.get('maxRows') != limit):
        raise RuntimeError('站方分页偏移异常')
    if c['totalNumber'] < 10000:
        expected = min(limit, max(0, c['totalNumber'] - (page - 1) * limit))
        if len(c['results']) != expected:
            raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in c['results']:
        if not isinstance(x, dict) or not isinstance(x.get('bookId'), str) or (not isinstance(x.get('from'), str)) or (not any((isinstance(z, dict) and z.get('databaseId') == db_id for z in x.get('databaseList') or []))):
            raise RuntimeError('条目来源未确认')
        item = {'book_id': x['bookId'], 'page_id': x.get('pageId'), 'source_path': _plain(x['from']), 'author': _plain(x.get('author')), 'publisher': _plain(x.get('publisher'))}
        omitted = []
        for source_key, out_key in (('from', 'source_path_raw'), ('author', 'author_raw'), ('publisher', 'publisher_raw')):
            value = x.get(source_key)
            if value is not None and (not isinstance(value, str) or re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', value, re.I)):
                item[out_key] = None
                omitted.append(source_key)
            else:
                item[out_key] = value
        if omitted:
            item['source_fields_omitted'] = omitted
        items.append(item)
    return {'source_fields_note': '出处、作者与出版者 raw 字段保留站方原值与高亮；含链接、疑似凭据或异常结构时省略并标记。总数低于10000时按请求页次校验条数；总数可能受站方上限影响，数据可能变化。', 'source': '尚古汇典·' + db_name, 'query': q, 'page': page, 'page_size': limit, 'total': c['totalNumber'], 'items': items[:limit], 'note': '正文关键词匹配结果的出处题录，非书目或命中书数；总数可能受站方上限影响，学校机构身份和全文权限未确认。' if database == 'wenyuan' else '正文关键词匹配结果的出处题录，非书目或命中书数；总数可能受站方上限影响，本次未确认学校机构身份、第五期子集及全文权限。'}
