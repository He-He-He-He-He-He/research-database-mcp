"""天禄云枢校园 IP 单册书目详情。"""
import release_runtime
import re
import requests
from tianlu_ip_catalog_adapter import BASE

def detail(book_id, expected_title):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9]{1,100}', book_id):
        raise ValueError('图书编号无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300:
        raise ValueError('须提供完整书名')
    with requests.Session() as s:
        r = s.get(BASE + 'common/isCompanyUser', timeout=20)
        r.raise_for_status()
        j = r.json()
        identity = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
        if not isinstance(identity, dict) or identity.get('companyName') != '浙江大学':
            raise RuntimeError('未确认浙江大学机构身份')
        r = s.get(BASE + 'business/book/bookInfo/' + book_id, timeout=20)
        r.raise_for_status()
        j = r.json()
        x = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
    if not isinstance(x, dict) or x.get('bookId') != book_id or x.get('bookName') != expected_title.strip():
        raise RuntimeError('站方图书编号或书名不一致')
    keys = ('bookId', 'bookName', 'categoryName', 'copier', 'writer', 'country', 'summary', 'wordNum', 'publishTime', 'publisher', 'bookVersion')
    return {'source': '天禄云枢古籍数据库', 'institution': '浙江大学', 'institution_validity_date': identity.get('validityDate'), 'book': {k: x.get(k) for k in keys}, 'note': '原站单册书目字段及简介（如有），空值原样保留；机构身份不等于逐书阅读权限，未读取正文或图像。'}
