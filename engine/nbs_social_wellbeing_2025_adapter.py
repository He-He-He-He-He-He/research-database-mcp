"""国家统计局 2025 年社会民生统计报告，按网页正文段落查找。"""
import release_runtime
import requests
from bs4 import BeautifulSoup
URL = 'https://www.stats.gov.cn/sj/zxfbhjd/202610/t20261030_1965711.html'

def search(keyword='', offset=0, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词须为不超过100字的字符串')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('offset 须非负、limit 须为1至100')
    with requests.get(URL, timeout=(12, 25), allow_redirects=False, stream=True) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise RuntimeError('官网页面发生重定向')
        chunks = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 3000000:
                raise RuntimeError('响应超过3MB上限')
            chunks.append(c)
    s = BeautifulSoup(b''.join(chunks).decode('utf-8'), 'html.parser')
    if not s.title or '2025年社会民生统计报告' not in s.title.get_text(' ', strip=True):
        raise RuntimeError('未识别官方报告标题')
    body = s.select_one('.trs_editor_view')
    if not body:
        raise RuntimeError('官方正文区域未识别')
    lines = [p.get_text(' ', strip=True) for p in body.find_all('p') if p.get_text(' ', strip=True)]
    if len(lines) < 10:
        raise RuntimeError('官方正文不完整')
    rows = [{'paragraph_index': i + 1, 'text': line} for i, line in enumerate(lines) if not keyword or keyword.casefold() in line.casefold()]
    return {'source': '国家统计局社会民生统计报告', 'url': URL, 'year': 2025, 'publication_date': '2026-10-30', 'keyword': keyword, 'total_paragraphs': len(lines), 'matched_paragraphs': len(rows), 'offset': offset, 'limit': limit, 'items': rows[offset:offset + limit], 'note': '网页正文段落的本地包含检索，非结构化数据库。报告所用指标可能来自其他部门，含不同年度、期间、单位、预测和方法；需核原文与脚注。图片、附件未识别。'}
