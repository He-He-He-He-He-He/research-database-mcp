"""国家自然科学基金管理制度目录及正文。"""
import release_runtime
import re
import subprocess
from urllib.parse import urlparse
from szse_chinext_adapters import _Links
from nsfc_guides_adapters import Detail
BASE = 'https://www.nsfc.gov.cn'
INDEX = BASE + '/p1/2871/2874/gjzrkxjjgzzd.html'

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.nsfc.gov.cn' or (not p.path.startswith('/p1/2871/2874/')) or p.query or p.fragment:
        raise ValueError('仅允许科学基金管理制度栏目')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def nsfc_rules(keyword=''):
    p = _Links()
    p.feed(_get(INDEX))
    out = []
    for href, title in p.links:
        if re.fullmatch('/p1/2871/2874/\\d+/\\d+\\.html', href) and keyword in title:
            out.append({'title': title, 'url': BASE + href})
    if not out and (not keyword):
        raise ValueError('未找到管理制度目录')
    return out

def nsfc_rule_detail(url):
    p = Detail()
    p.feed(_get(url))
    title = ' '.join(''.join(p.parts['detail-title']).split())
    text = '\n'.join((s.strip() for s in ''.join(p.parts['detail-p']).splitlines() if s.strip()))
    if not title or len(text) < 100:
        raise ValueError('未识别制度正文')
    return {'url': url, 'title': title, 'text': text, 'note': '仅科学基金管理制度栏目；旧版、修订、有效期和附件请核对最新官方公告。'}
