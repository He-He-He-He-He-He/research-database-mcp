"""科学文库 IP 机构会话图书书目与简介。"""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
from sciencebook_institution_toc_adapter import BASE

def detail(book_id, expected_title):
    if not isinstance(book_id, str) or not re.fullmatch('[A-Za-z0-9]{1,100}', book_id):
        raise ValueError('图书编号无效')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200:
        raise ValueError('须提供完整图书名称')
    with requests.Session() as s:
        r = s.get(BASE + 'shop/main/Login/shopFrame.do', timeout=25)
        r.raise_for_status()
        r = s.post(BASE + 'shop/main/Login/checkOrgNameByIp.do', timeout=20)
        r.raise_for_status()
        if r.text.strip() != '浙江大学':
            raise RuntimeError('未确认浙江大学 IP 机构身份')
        r = s.get(BASE + 'shop/book/Booksimple/show.do', params={'id': book_id}, timeout=25)
        r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    bid = p.select_one('input#id')
    title = p.title.get_text(' ', strip=True) if p.title else ''
    if not bid or bid.get('value') != book_id or title != expected_title.strip():
        raise RuntimeError('站方图书编号或标题不一致')
    fields = []
    for row in p.select('.book_info_row'):
        vals = row.select(':scope > div')
        if len(vals) >= 2:
            name = vals[0].get_text(' ', strip=True).rstrip('：:')
            value = vals[1].get_text(' ', strip=True)
            if name:
                fields.append({'name': name, 'value': value or None})
    if not fields:
        raise RuntimeError('站方图书详情缺少书目字段')
    synopsis = p.select_one('#introduction-body')
    return {'source': '科学文库', 'institution': '浙江大学（IP）', 'book_id': book_id, 'title': title, 'fields': fields, 'introduction': synopsis.get_text(' ', strip=True) or None if synopsis else None, 'note': '原站公开展示的图书简介和书目信息；机构身份不代表该书全文权限，未读取正文。'}
