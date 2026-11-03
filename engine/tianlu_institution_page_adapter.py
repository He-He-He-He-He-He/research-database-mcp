"""天禄云枢单页原文与站方标注；不输出页面图像。"""
import release_runtime
import re
import requests
from tianlu_ip_catalog_adapter import BASE

def page(book_id, expected_title, page=1):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9]{1,100}', book_id):
        raise ValueError('图书编号无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 300:
        raise ValueError('须提供完整书名')
    if type(page) is not int or not 1 <= page <= 100000:
        raise ValueError('页码须为正整数')
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
        book = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
        if not isinstance(book, dict) or book.get('bookId') != book_id or book.get('bookName') != expected_title.strip():
            raise RuntimeError('书目编号或标题不匹配')
        r = s.post(BASE + 'business/book/bookPageInfo', json={'bookId': book_id}, timeout=25)
        r.raise_for_status()
        j = r.json()
        pages = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
        if not isinstance(pages, list) or not pages or len(pages) > 100000 or any((not isinstance(x, str) or not re.fullmatch('[A-Za-z0-9]{32}', x) for x in pages)):
            raise RuntimeError('原站页面列表异常')
        if page > len(pages):
            raise ValueError('页码超过站方页面数')
        pid = pages[page - 1]
        r = s.post(BASE + 'business/book/singlePage', json={'bookId': book_id, 'pageId': pid}, timeout=30)
        r.raise_for_status()
        j = r.json()
        data = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
    if not isinstance(data, dict) or data.get('pageId') != pid or str(data.get('bookPage')) != str(page) or (not isinstance(data.get('mainText'), str)):
        raise RuntimeError('页面编号或原文响应异常')
    return {'source': '天禄云枢古籍数据库', 'institution': '浙江大学', 'institution_validity_date': identity.get('validityDate'), 'book_id': book_id, 'title': expected_title.strip(), 'page': page, 'page_id': pid, 'reader_page_count': len(pages), 'main_text_raw': data.get('mainText'), 'annotation_json_raw': data.get('specialText'), 'layout_json_raw': data.get('pageJson'), 'note': '返回原站页面文字、标注和布局原始字段，不输出页面图像；页面序号不一定是印刷页码。单页成功不代表其他图书及页面权限，文字须与原图校核。'}
