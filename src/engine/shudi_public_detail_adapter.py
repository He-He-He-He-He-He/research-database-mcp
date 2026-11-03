"""书递匿名单册公开书目信息，不读取目录或全文。"""
import release_runtime
import re
import requests
from shudi_public_catalog_adapter import BASE
FIELDS = ('isbn', 'language', 'publishdate', 'booktitle', 'author', 'publish', 'naturalnum')
FORBIDDEN = re.compile('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', re.I)

def detail(book_id, expected_title, include_description=False, session=None):
    if not isinstance(book_id, str) or not re.fullmatch('[0-9]{1,30}', book_id):
        raise ValueError('图书编号须为数字')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供完整题名')
    if type(include_description) is not bool:
        raise ValueError('include_description 须为布尔值')
    s = session or requests.Session()
    try:
        r = s.get(BASE + 'mdst/webapi/detail.action', params={'id': book_id}, timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('书目详情不可用')
        j = r.json()
        x = j.get('info') if isinstance(j, dict) and j.get('result') == 'success' else None
        if not isinstance(x, dict) or str(x.get('bookid')) != book_id or x.get('booktitle') != expected_title.strip():
            raise RuntimeError('书号或题名不匹配')
        fields = {}
        omitted = []
        for k in FIELDS:
            v = x.get(k)
            if v is not None and (type(v) not in (str, int, float) or (isinstance(v, str) and FORBIDDEN.search(v))):
                fields[k] = None
                omitted.append(k)
            else:
                fields[k] = v
        if include_description:
            v = x.get('bookdesc')
            if v is not None and (not isinstance(v, str) or FORBIDDEN.search(v)):
                fields['bookdesc'] = None
                omitted.append('bookdesc')
            else:
                fields['bookdesc'] = v
        return {'source': '书递匿名公开书目详情', 'book_id': book_id, 'fields_raw': fields, 'omitted_fields': omitted, 'note': '匿名公开书目信息，学校机构、逐书全文与目录权限未确认；包含链接、敏感参数或类型异常的字段置空并标记，不输出令牌或阅读链接。'}
    except (requests.RequestException, ValueError):
        raise RuntimeError('书目服务连接失败或响应无法解析') from None
