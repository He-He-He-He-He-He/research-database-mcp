"""中华经典古籍库学校 IP 单册元数据及目录，不读取正文。"""
import release_runtime
import re
import requests
from zhonghua_classics_institution_catalog_adapter import BASE, HEADERS, _plain
FIELDS = ('author', 'author2', 'editor', 'publisher', 'version', 'pubdate', 'isbn', 'origin', 'reign', 'picCount')

def _has_private(s):
    return any((57344 <= ord(c) <= 63743 or 983040 <= ord(c) <= 1048573 or 1048576 <= ord(c) <= 1114109 for c in s))

def _value(v):
    if v is None or type(v) in (int, float, bool):
        return (v, False)
    if not isinstance(v, str):
        return (None, True)
    text = _plain(v)
    return (None, True) if _has_private(text) else (text, False)

def detail(book_id, expected_title, session=None):
    if type(book_id) is not int or book_id < 1:
        raise ValueError('图书编号须为正整数')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供完整书名')
    s = session or requests.Session()
    try:
        r = s.get(BASE + 'user/checkuserlogininfo', headers=HEADERS, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('机构认证不可用')
        j = r.json()
        ins = j.get('data', {}).get('ins') if isinstance(j, dict) and isinstance(j.get('data'), dict) else None
        if not isinstance(ins, dict) or ins.get('name') != '浙江大学':
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.get(BASE + 'books/' + str(book_id), params={'libId': 6, 'isBook': 'false'}, headers=HEADERS, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('书目详情不可用')
        j = r.json()
        book = j.get('data') if isinstance(j, dict) and j.get('success') is True and (j.get('code') == 200) else None
        if not isinstance(book, dict) or book.get('contentId') != book_id or _plain(book.get('title')) != expected_title.strip():
            raise RuntimeError('书目编号或书名不匹配')
        r = s.get(BASE + 'books/' + str(book_id) + '/catalog', params={'parentId': 0, 'allTree': 'true'}, headers=HEADERS, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('目录服务不可用')
        j = r.json()
        tree = j.get('data') if isinstance(j, dict) and j.get('success') is True and (j.get('code') == 200) else None
        if not isinstance(tree, list):
            raise RuntimeError('目录结构异常')
        count = 0

        def convert(nodes, depth=0):
            nonlocal count
            if depth > 50:
                raise RuntimeError('目录层级超限')
            out = []
            for x in nodes:
                count += 1
                if count > 10000 or not isinstance(x, dict) or type(x.get('contentId')) is not int or (not isinstance(x.get('title'), str)):
                    raise RuntimeError('目录节点异常')
                title, omitted = _value(x['title'])
                children = x.get('childs') or []
                if not isinstance(children, list):
                    raise RuntimeError('目录子节点异常')
                out.append({'content_id': x['contentId'], 'title': title, 'title_omitted_encoded': omitted, 'parent_id_raw': x.get('parentId') if type(x.get('parentId')) is int else None, 'level_raw': x.get('level') if type(x.get('level')) is int else None, 'is_leaf_raw': x.get('isLeaf') if type(x.get('isLeaf')) is bool else None, 'children': convert(children, depth + 1)})
            return out
        catalog = convert(tree)
        meta = {}
        omitted = []
        for k in FIELDS:
            value, skip = _value(book.get(k))
            meta[k] = value
            if skip:
                omitted.append(k)
        return {'source': '中华经典古籍库学校机构元数据', 'institution': '浙江大学', 'book_id': book_id, 'title': expected_title.strip(), 'metadata': meta, 'metadata_omitted_encoded_or_invalid': omitted, 'catalog_node_count': count, 'catalog': catalog, 'note': '目录树及站方元数据，不代表逐章全文权限；私用区或异常类型的字段置空标记，未解码、未输出简介或正文。'}
    except (requests.RequestException, ValueError):
        raise RuntimeError('机构服务连接失败或响应无法解析') from None
