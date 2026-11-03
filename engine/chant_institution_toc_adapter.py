"""漢達文庫学校 IP 单册章节目录及层级，不读取正文。"""
import release_runtime
import json
import re
import requests
from bs4 import BeautifulSoup
from chant_ip_search_adapter import BASE
from chant_institution_chapter_adapter import UUID

def contents(book_id, expected_title):
    if not isinstance(book_id, str) or not re.fullmatch(UUID, book_id, re.I):
        raise ValueError('书目编号须为 UUID')
    if not isinstance(expected_title, str) or not expected_title.strip() or len(expected_title) > 200:
        raise ValueError('须提供完整书名')
    r = requests.get(BASE + '/text/book/' + book_id, timeout=30)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    if '[Zhejiang University]' not in p.get_text(' ', strip=True):
        raise RuntimeError('未识别浙大机构会话')
    if not p.title or p.title.get_text(' ', strip=True) != 'CHANT - 文本 - ' + expected_title.strip():
        raise RuntimeError('书目标题不匹配')
    match = re.search("'data'\\s*:\\s*(\\[)", r.text)
    if not match:
        raise RuntimeError('站方章节目录缺失')
    try:
        tree, _ = json.JSONDecoder().raw_decode(r.text[match.start(1):])
    except ValueError:
        raise RuntimeError('站方章节目录格式异常') from None
    if not isinstance(tree, list) or len(tree) > 50000:
        raise RuntimeError('章节目录结构异常')
    items = []
    for x in tree:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('parent'), str)) or (not isinstance(x.get('text'), str)):
            raise RuntimeError('目录节点缺少字段')
        items.append({'id': x['id'], 'parent_id': x['parent'], 'title': x['text']})
    return {'source': '漢達文庫', 'institution': 'Zhejiang University', 'book_id': book_id, 'title': expected_title.strip(), 'entries': items, 'note': '原站目录节点及父子层级；非每个节点都是可读章节。仅目录，不代表逐章节正文权限。'}
