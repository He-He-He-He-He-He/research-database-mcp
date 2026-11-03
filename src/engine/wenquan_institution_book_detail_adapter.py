"""文泉学堂学校 IP 图书元数据；仅白名单字段，不保存临时令牌。"""
import release_runtime
import re
import requests
from wenquan_institution_catalog_adapter import BASE, _plain
FIELDS = {'nameSub': 'subtitle_raw', 'serName': 'series_raw', 'author': 'author_raw', 'edtName': 'editor_raw', 'translator': 'translator_raw', 'isbn': 'isbn_raw', 'lang': 'language_raw', 'date': 'publication_date_raw', 'pub': 'publisher_raw', 'edition': 'edition_raw', 'pages': 'pages_raw', 'keyword': 'keywords_raw', 'libClass': 'classification_raw', 'descript': 'description_raw', 'authorBiography': 'author_biography_raw', 'audience': 'audience_raw'}
BAD = re.compile('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=|<\\s*(?:script|iframe|object|embed|style)\\b|\\bon\\w+\\s*=|[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f]', re.I)

def detail(book_id, expected_title, session=None):
    if not isinstance(book_id, str) or not re.fullmatch('book_[0-9]{1,18}', book_id):
        raise ValueError('编号须为搜索结果的 book_ 类型')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供搜索结果的完整标题')
    bid = book_id.removeprefix('book_')
    s = session or requests.Session()
    try:
        r = s.post(BASE + 'api/v7/rz/jxjwt', params={'s': 'wqxuetang'}, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('学校会话初始化失败')
        j = r.json()
        token = j.get('data') if isinstance(j, dict) and j.get('errcode') == 0 else None
        if not isinstance(token, str) or not token:
            raise RuntimeError('学校会话初始化失败')
        headers = {'Authorization': token}
        r = s.get(BASE + 'api/v7/search/libdata', headers=headers, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('学校身份不可用')
        j = r.json()
        identity = j.get('data') if isinstance(j, dict) and j.get('errcode') == 0 else None
        if not isinstance(identity, dict) or identity.get('name') != '浙江大学' or identity.get('inip') is not True:
            raise RuntimeError('未确认浙江大学校内 IP')
        r = s.get(BASE + 'api/v7/book/initbook', params={'bid': bid}, headers=headers, timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('书目详情不可用')
        j = r.json()
        data = j.get('data') if isinstance(j, dict) and j.get('errcode') == 0 else None
        if not isinstance(data, dict) or str(data.get('bid')) != bid or _plain(data.get('name')) != expected_title.strip():
            raise RuntimeError('书号或标题与检索结果不一致')
        result = {'source': '文泉学堂学校 IP 图书详情', 'institution': '浙江大学', 'campus_ip': True, 'book_id': book_id, 'title': expected_title.strip()}
        omitted = []
        for src, out in FIELDS.items():
            v = data.get(src)
            if v is None or v == '':
                result[out] = None
            elif isinstance(v, str) and len(v) <= 20000 and (not BAD.search(v)):
                result[out] = v
            elif type(v) in (int, float) and src == 'pages':
                result[out] = v
            else:
                result[out] = None
                omitted.append(src)
        result['source_fields_omitted'] = omitted
        result['note'] = '机构校内 IP 与站方书号、标题已核；字段为站方原值，可能缺失。安全异常字段省略并标记；简介不等于正文，机构身份不证明逐书全文权限。未输出临时令牌、阅读链接或正文。'
        return result
    except (requests.RequestException, ValueError):
        raise RuntimeError('文泉机构详情连接失败或响应无法解析') from None
