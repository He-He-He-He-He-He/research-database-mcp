"""PQDT 中国集团平台匿名公开论文题录；不输出摘要或全文。"""
import release_runtime
import re
import requests
BASE = 'https://www.pqdtcn.com/'
FIELDS = ('thesisTitleNotColor', 'thesisAuthor', 'thesisSchoolName', 'thesisYear', 'thesisType', 'thesisSource', 'thesisAdviser')

def search(keyword, page=1, limit=20, session=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 200 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('检索词须为 1–200 字的单行文本')
    if type(page) is not int or not 1 <= page <= 1000:
        raise ValueError('page 须为 1–1000')
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError('limit 须为 1–20')
    s = session or requests.Session()
    query = keyword.strip()
    body = {'searchText': query, 'pageSize': '20', 'pageNumber': page, 'exactSearch': 0, 'fullText': 0, 'facetsList': []}
    try:
        r = s.get(BASE, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('平台首页不可用')
        r = s.post(BASE + 'basic/basic_search', json=body, timeout=40, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('平台检索不可用')
        j = r.json()
        o = j.get('queryObject') if isinstance(j, dict) else None
        rows = j.get('results') if isinstance(j, dict) else None
        if not isinstance(o, dict) or o.get('searchText') != query or str(o.get('pageNumber')) != str(page) or (str(o.get('pageSize')) != '20') or (str(j.get('statusCode')) != '1') or (type(j.get('hits')) is not int) or (j['hits'] < 0) or (not isinstance(rows, list)) or (len(rows) > 20):
            raise RuntimeError('搜索结果未确认查询或页码')
        expected = min(20, max(0, j['hits'] - (page - 1) * 20))
        if len(rows) != expected:
            raise RuntimeError('站方源页条数与总数及页码不一致，可能数据变化或响应不完整')
        items = []
        for row in rows[:limit]:
            if not isinstance(row, dict) or not isinstance(row.get('thesisTitleNotColor'), str) or (not row['thesisTitleNotColor'].strip()):
                raise RuntimeError('题名缺失')
            item = {}
            for k in FIELDS:
                v = row.get(k)
                if v is None or type(v) in (str, int, float):
                    item[k] = v
            items.append(item)
        return {'source': 'PQDT 中国集团平台匿名题录', 'query': query, 'page': page, 'source_page_size': 20, 'source_hits_raw': j['hits'], 'source_page_items': len(rows), 'page_truncated': len(items) < len(rows), 'items': items, 'note': '模糊相关检索，未识别浙大机构身份；结果排序可能变化，分页可能重叠或遗漏；limit 小于源页条数会截断本页，翻页前须取完整 20 条。无关或随机检索词仍可能返回结果，不代表精确匹配。先核对源页条数与总数，再按 limit 截取；数据可能变化。仅题录，不表示学校订购、摘要或全文权限。'}
    except (requests.RequestException, ValueError):
        raise RuntimeError('PQDT 连接失败或响应无法解析') from None
