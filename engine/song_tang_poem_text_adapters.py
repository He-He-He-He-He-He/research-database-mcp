"""Read visible trial poem and its metrical annotations in page order."""
import release_runtime
from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup
BASE = 'http://www.chinabooktrading.com/'

def detail(kind, poem_id, session=None):
    if kind not in ('song', 'tang') or type(poem_id) is not int or (not 1 <= poem_id <= 9999999):
        raise ValueError('需要 song/tang 和有效作品编号')
    params = {'a': '1', 'e': '1' if kind == 'song' else '0', 'u': str(poem_id), 'b': '4'}
    r = (session or requests).get(BASE + kind + '/fullText.jsp', params=params, timeout=20)
    r.raise_for_status()
    r.encoding = 'utf-8'
    s = BeautifulSoup(r.text, 'html.parser')
    head = s.select_one('h2.nametitle')
    title = s.select_one('h3.TEXT_DARK')
    block = title.parent if title else None
    expected = '詩:宋詩' if kind == 'song' else '詩:唐詩'
    if not head or not head.get_text(' ', strip=True).startswith(expected) or (not block):
        raise ValueError('作品或诗集类型不匹配')
    author = block.select_one('h4.TEXT_LIGHT')
    segments = []
    for p in block.find_all('p', recursive=False):
        t = p.get_text('', strip=True)
        if t:
            segments.append({'type': '格律' if 'gl' in (p.get('class') or []) else '诗句', 'text': t})
    if not author or not segments or (not any((x['type'] == '诗句' for x in segments))):
        raise ValueError('未识别试用诗句内容')
    return {'source': '全宋诗分析系统' if kind == 'song' else '全唐诗分析系统', 'scope': '试用库仅含部分作品和页面展示内容', 'id': poem_id, 'title': title.get_text(' ', strip=True), 'author': author.get_text(' ', strip=True), 'segments': segments, 'record_url': BASE + kind + '/fullText.jsp?' + urlencode(params), 'note': '逐行保留网站诗句及格律原文，包括异常字符；试用页可能不完整，不推断全文或机构权限。上游 HTTP 明文。'}
