"""国家自然科学基金委部分学科资助成果栏目。"""
import release_runtime
import re
import subprocess
from urllib.parse import urlparse
from szse_chinext_adapters import _Links
from nsfc_guides_adapters import Detail
BASE = 'https://www.nsfc.gov.cn'
CATEGORIES = {'interdisciplinary': '/p1/2859/3190/jckxbzzcg.html', 'information': '/p1/2856/3157/xxkxzzcg.html', 'medical': '/p1/2858/3216/yxkxbzzcg.html', 'life': '/p1/2853/3103/zzcg1111.html'}

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nsfc.gov.cn' or p.query or p.fragment or (not (p.path in CATEGORIES.values() or re.fullmatch('/p1/3381/2825/\\d+\\.html', p.path))):
        raise ValueError('仅允许基金委已列成果栏目和成果正文')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def nsfc_results(category='interdisciplinary', keyword=''):
    if category not in CATEGORIES:
        raise ValueError('未知学科类别')
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    p = _Links()
    p.feed(_get(BASE + CATEGORIES[category]))
    out = []
    recognized = False
    for href, title in p.links:
        if re.fullmatch('/p1/3381/2825/\\d+\\.html', href):
            recognized = True
            if keyword in title:
                out.append({'title': ' '.join(title.split()), 'url': BASE + href})
    if not recognized:
        raise ValueError('未识别成果目录，无法确认检索结果')
    return out

def nsfc_result_detail(url):
    p = Detail()
    p.feed(_get(url))
    title = ' '.join(''.join(p.parts['detail-title']).split())
    text = '\n'.join((s.strip() for s in ''.join(p.parts['detail-p']).splitlines() if s.strip()))
    if not title or len(text) < 100:
        raise ValueError('未识别成果正文')
    return {'url': url, 'title': title, 'text': text, 'note': '基金委发布的研究进展介绍，不是论文全文或完整成果数据库；原始论文与结论须核对。'}
