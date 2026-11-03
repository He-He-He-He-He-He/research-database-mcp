"""漢達文庫學校 IP 單章原始排版 HTML，不遍历或下载图像。"""
import release_runtime
import json
import re
import requests
from bs4 import BeautifulSoup
from chant_ip_search_adapter import BASE
UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

def chapter(book_id, chapter_id, book_title, chapter_title):
    if any((not isinstance(v, str) or not re.fullmatch(UUID, v, re.I) for v in (book_id, chapter_id))):
        raise ValueError('书目和章节编号须为 UUID')
    if any((not isinstance(v, str) or not v.strip() or len(v) > 200 for v in (book_title, chapter_title))):
        raise ValueError('须提供书名与章节名')
    with requests.Session() as s:
        r = s.get(BASE + '/text/book/' + book_id + '/' + chapter_id, timeout=30)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        if '[Zhejiang University]' not in p.get_text(' ', strip=True):
            raise RuntimeError('未识别浙大机构会话')
        if not p.title or p.title.get_text(' ', strip=True) != 'CHANT - 文本 - ' + book_title.strip():
            raise RuntimeError('书目标题不匹配')
        match = re.search("'data'\\s*:\\s*(\\[)", r.text)
        if not match:
            raise RuntimeError('站方章节目录缺失')
        try:
            tree, _ = json.JSONDecoder().raw_decode(r.text[match.start(1):])
        except ValueError:
            raise RuntimeError('站方章节目录格式异常') from None
        nodes = [x for x in tree if isinstance(x, dict) and x.get('id', '').lower() == chapter_id.lower()] if isinstance(tree, list) else []
        if len(nodes) != 1 or nodes[0].get('text') != chapter_title.strip():
            raise RuntimeError('章节编号与标题不匹配')
        r = s.get(BASE + '/text/chapter/' + chapter_id + '/', timeout=30)
        r.raise_for_status()
    if len(r.content) > 8000000:
        raise RuntimeError('单章响应超过8 MB，未解析')
    p = BeautifulSoup(r.content, 'html.parser')
    nodes = p.select('.Chapter')
    if len(nodes) != 1 or chapter_id.lower() not in r.text.lower() or (not nodes[0].select('.Word')):
        raise RuntimeError('未确认原站章节内容')
    return {'source': '漢達文庫', 'institution': 'Zhejiang University', 'book_id': book_id, 'chapter_id': chapter_id, 'book_title': book_title.strip(), 'chapter_title': chapter_title.strip(), 'chapter_html': str(nodes[0]), 'word_elements': len(nodes[0].select('.Word')), 'note': '单章原站排版 HTML，保留正文、标点和注释结构；元素数不等于字数。当前 IP 会话可返回此章，不代表其他书或章节权限。'}
