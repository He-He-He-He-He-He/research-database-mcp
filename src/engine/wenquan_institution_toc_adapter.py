"""文泉学堂浙大机构书目目录；临时令牌不持久化。"""
import release_runtime
import re
import requests
from wenquan_institution_catalog_adapter import BASE, _plain

def toc(book_id, expected_title, session=None):
    if not isinstance(book_id, str) or not re.fullmatch('(?:book_)?[0-9]{1,18}', book_id):
        raise ValueError('图书编号须来自 book_ 类型书目')
    bid = book_id.removeprefix('book_')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200 or re.search('[\\x00-\\x1f]', expected_title):
        raise ValueError('须提供完整书名')
    s = session or requests.Session()
    try:
        r = s.post(BASE + 'api/v7/rz/jxjwt', params={'s': 'wqxuetang'}, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('会话初始化失败')
        j = r.json()
        token = j.get('data') if isinstance(j, dict) else None
        if not isinstance(token, str) or not token:
            raise RuntimeError('会话初始化失败')
        headers = {'Authorization': token}
        r = s.get(BASE + 'api/v7/search/libdata', headers=headers, timeout=20, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('机构身份不可用')
        j = r.json()
        identity = j.get('data') if isinstance(j, dict) and j.get('errcode') == 0 else None
        if not isinstance(identity, dict) or identity.get('name') != '浙江大学' or identity.get('inip') is not True:
            raise RuntimeError('未确认浙江大学校内 IP')
        r = s.get(BASE + 'api/v7/book/initbook', params={'bid': bid}, headers=headers, timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('书目详情不可用')
        j = r.json()
        book = j.get('data') if isinstance(j, dict) and j.get('errcode') == 0 else None
        if not isinstance(book, dict) or str(book.get('bid')) != bid or _plain(book.get('name')) != expected_title.strip():
            raise RuntimeError('书号或题名不匹配')
        r = s.get(BASE + 'deep/book/v1/catatree', params={'bid': bid}, headers=headers, timeout=25, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('目录不可用')
        j = r.json()
        tree = j.get('data') if isinstance(j, dict) and j.get('code') == 0 else None
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
                if count > 10000 or not isinstance(x, dict) or (not isinstance(x.get('label'), str)) or (not x['label'].strip()):
                    raise RuntimeError('目录节点异常')
                label = x['label']
                if re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', label, re.I):
                    raise RuntimeError('目录标题包含链接或敏感参数')
                children = x.get('children') or []
                if not isinstance(children, list):
                    raise RuntimeError('目录子节点异常')

                def raw(k):
                    v = x.get(k)
                    if isinstance(v, str) and re.search('[a-z][a-z0-9+.-]*://|www\\.|(?:href|src)\\s*=|(?:token|session|sid|apikey|api_key)\\s*=', v, re.I):
                        raise RuntimeError('目录字段包含链接或敏感参数')
                    return v if v is None or type(v) in (str, int, float, bool) else None
                out.append({'id_raw': raw('id'), 'parent_id_raw': raw('pid'), 'level_raw': raw('level'), 'page_raw': raw('pnum'), 'title': label, 'is_leaf_raw': raw('isLeaf'), 'children': convert(children, depth + 1)})
            return out
        items = convert(tree)
        return {'source': '文泉学堂浙大机构图书目录', 'institution': '浙江大学', 'campus_ip': True, 'book_id': bid, 'title': expected_title.strip(), 'catalog_node_count': count, 'catalog': items, 'note': '节点编号、层级和页码为站方原值，页码是否对应印刷页须核；目录可见不代表逐页全文权限。不输出令牌、文件或阅读链接。'}
    except (requests.RequestException, ValueError):
        raise RuntimeError('机构服务连接失败或目录响应无法解析') from None
