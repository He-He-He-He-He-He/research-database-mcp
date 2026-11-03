"""全国哲学社会科学工作办公室成果展示栏目。"""
import release_runtime
import re
import subprocess
from urllib.parse import urlparse
from szse_chinext_adapters import _Links
from nopss_annual_project_adapters import _Body
BASE = 'https://www.nopss.gov.cn'
INDEX = BASE + '/GB/219544/'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nopss.gov.cn' or p.query or p.fragment or (not (p.path == '/GB/219544/' or re.fullmatch('/n1/\\d{4}/\\d{4}/c219544-\\d+\\.html', p.path))):
        raise ValueError('仅允许社科工作办成果展示栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def social_research_articles(keyword=''):
    p = _Links()
    p.feed(_get(INDEX))
    out = []
    for href, title in p.links:
        if re.fullmatch('/n1/\\d{4}/\\d{4}/c219544-\\d+\\.html', href) and keyword in title:
            out.append({'title': ' '.join(title.split()), 'url': BASE + href})
    if not out and (not keyword):
        raise ValueError('未找到成果展示目录')
    return out

def social_research_article_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别文章正文')
    return {'url': url, 'text': text, 'note': '社科工作办公开成果展示文章，不是全部项目成果或同行评议数据库；来源、作者观点及原始资料请核对原文。'}
