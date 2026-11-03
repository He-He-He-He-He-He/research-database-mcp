"""Book Delivery public book catalog; no institutional or full-text claim."""
import release_runtime
import requests
BASE = 'https://www.elib.link/'

def search(keyword, page=1, limit=10, session=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 24):
        raise ValueError('每页最多 24 条')
    q = keyword.strip()
    s = session or requests.Session()
    s.get(BASE, timeout=20).raise_for_status()
    p = {'publishcode': '', 'pageno': str(page), 'pagesize': str(limit), 'keyword': q, 'ordervalue': 'desc', 'sortcode': '', 'visitcode': '', 'label': ''}
    r = s.get(BASE + 'mdst/webapi/searchlist.action', params=p, timeout=20)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or j.get('result') != 'success' or type(j.get('total')) is not int or (j['total'] < 0) or (not isinstance(j.get('info'), list)) or (len(j['info']) > limit):
        raise RuntimeError('书目响应异常')
    expected = min(limit, max(0, j['total'] - (page - 1) * limit))
    if len(j['info']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in j['info']:
        b = x.get('info') if isinstance(x, dict) else None
        if not isinstance(b, dict) or not isinstance(b.get('BOOKID'), str) or (not isinstance(b.get('BOOKTITLE'), str)):
            raise RuntimeError('缺少书目编号或题名')
        items.append({'id': b['BOOKID'], 'title': b['BOOKTITLE'], 'author': b.get('AUTHOR') or None, 'publish_date': b.get('PUBLISHDATE') or None})
    return {'source': '书递中文电子图书平台', 'query': q, 'page': page, 'page_size': limit, 'total': j['total'], 'items': items[:limit], 'note': '原站全部图书公开书目，未限定学校馆藏；未核验浙江大学机构身份或全文访问；按总数和请求页次核验条数，源不回显页码，数据可能变化。'}
