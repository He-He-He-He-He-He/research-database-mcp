"""广州大典公开单册著录，不获取图片或全文。"""
import release_runtime
import re
import requests
from guangzhou_dadian_catalog_adapter import BASE, _clean
FIELDS = ('Title', 'Responsibility', 'Section', 'Catalog', 'BookNum', 'Pages', 'Edition', 'Navigation', 'Physicalpages', 'Languages', 'CollectionUnits', 'Frame', 'Description', 'ReadCount')

def detail(book_id, expected_title, session=None):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9]{1,80}', book_id):
        raise ValueError('书目编号格式无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供完整题名')
    s = session or requests.Session()
    try:
        r = s.get(BASE + 'api/Search/Detail', params={'id': book_id}, headers={'Referer': BASE + 'website/gzddDatabase'}, timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('详情服务不可用')
        j = r.json()
        x = j.get('Data') if isinstance(j, dict) and j.get('Code') == 1 else None
        if not isinstance(x, dict) or x.get('BookId') != book_id or _clean(x.get('Title')) != expected_title.strip():
            raise RuntimeError('书目编号或题名与检索结果不一致')
        values = {k: x.get(k) for k in FIELDS if x.get(k) is None or type(x.get(k)) in (str, int, float)}
        return {'source': '广州大典数据库公开著录', 'book_id': book_id, 'fields_raw': values, 'note': '原始字段与空值保留；Pages、Physicalpages 的计量含义未核，勿擅作页数推断。仅公开书目，未确认浙大机构身份或逐册全文、影像权限。'}
    except (requests.RequestException, ValueError):
        raise RuntimeError('详情服务连接失败或响应无法解析') from None
