"""江苏网信办生成式 AI 增量备案公告及原图。"""
import release_runtime
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from nppa_statistics_adapters import fetch
from szse_chinext_adapters import _Links
from jiangsu_cyberspace_policies_adapters import jiangsu_cyberspace_policy_detail
BASE = 'https://www.jswx.gov.cn/fwhd/tzgg/'

def jiangsu_genai_notices(keyword=''):
    parser = _Links()
    parser.feed(fetch(BASE).decode('utf-8'))
    rows = []
    seen = set()
    for href, title in parser.links:
        url = urljoin(BASE, href)
        if re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.shtml', url) and '江苏省生成式人工智能服务' in title and ('信息公告' in title) and (keyword in title) and (url not in seen):
            rows.append({'title': ' '.join(title.split()), 'url': url})
            seen.add(url)
    return {'source_url': BASE, 'items': rows, 'scope': '只筛选栏目当前页面江苏公告标题，非全国名单或全部历史数据。'}

class _Images(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div':
            if self.depth:
                self.depth += 1
            elif 'TRS_Editor' in attrs.get('class', '').split():
                self.depth = 1
        if self.depth and tag == 'img' and attrs.get('src'):
            self.urls.append(attrs['src'])

    def handle_endtag(self, tag):
        if tag == 'div' and self.depth:
            self.depth -= 1

def jiangsu_genai_notice_detail(url):
    if not re.fullmatch(re.escape(BASE) + '\\d{6}/t\\d{8}_\\d+\\.shtml', url):
        raise ValueError('仅支持江苏网信通知公告')
    detail = jiangsu_cyberspace_policy_detail(url)
    if '江苏省生成式人工智能服务' not in detail['text'] and '我省' not in detail['text']:
        raise ValueError('正文不是可识别的江苏生成式 AI 备案公告')
    parser = _Images()
    parser.feed(fetch(url).decode('utf-8'))
    images = []
    for href in parser.urls:
        link = urljoin(url, href)
        p = urlsplit(link)
        if p.scheme == 'https' and p.hostname == 'www.jswx.gov.cn' and (link not in images):
            images.append(link)
    return {'source_url': url, 'text': detail['text'], 'images': images, 'note': '原表以图片发布，未识别为结构化数据；新增、累计及统计日期应以当期公告为准。'}
