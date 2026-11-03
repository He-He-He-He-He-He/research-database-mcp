"""教育部育人体系政策目录及政策正文。"""
import release_runtime
import re
from html.parser import HTMLParser
from urllib.parse import urlparse
from moe_special_education_policy_adapters import _Body, _get
API = 'https://www.moe.gov.cn/was5/web/search?channelid=251673&chnlid=2147442951&page='

class _Catalog(HTMLParser):

    def __init__(self):
        super().__init__()
        self.rows = []

    def handle_starttag(self, t, attrs):
        a = dict(attrs)
        if t != 'a':
            return
        x = urlparse(a.get('href', ''))
        title = a.get('title', '')
        if x.hostname == 'www.moe.gov.cn' and re.fullmatch('/srcsite/(?:[^/]+/)+\\d{6}/t\\d{8}_\\d+\\.html', x.path) and title:
            self.rows.append({'title': title, 'url': 'https://www.moe.gov.cn' + x.path})

def student_development_list(page=1, keyword=''):
    page = int(page)
    if not 1 <= page <= 100:
        raise ValueError('页码超出范围')
    p = _Catalog()
    p.feed(_get(API + str(page)))
    return [x for x in p.rows if keyword in x['title']]

def student_development_detail(url):
    p = _Body()
    p.feed(_get(url))
    text = '\n'.join((s.strip() for s in ''.join(p.parts).splitlines() if s.strip()))
    if len(text) < 100:
        raise ValueError('未识别政策正文')
    return {'url': url, 'text': text, 'note': '教育部育人体系政策栏目正文，目录并非仅心理健康；政策效力和附件请核对原页。'}
