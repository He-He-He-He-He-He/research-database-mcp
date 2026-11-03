"""最高人民法院网站公开站内检索与资讯正文。"""
import release_runtime
import re
import subprocess
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse
ROOT = 'https://www.court.gov.cn'

class SearchResults(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.items = []
        self.date = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if not self.depth and tag == 'div' and ('search_list' in a.get('class', '').split()):
            self.depth = 1
            return
        if not self.depth:
            return
        if tag == 'div':
            self.depth += 1
        if tag == 'a' and re.fullmatch('/zixun/xiangqing/\\d+\\.html', a.get('href', '')):
            self.items.append({'title': re.sub('<[^>]*>', '', a.get('title', '')).strip(), 'url': ROOT + a['href'], 'date': ''})
        if tag == 'i' and 'date' in a.get('class', '').split():
            self.date = True

    def handle_data(self, data):
        if self.date and self.items:
            self.items[-1]['date'] += data.strip()

    def handle_endtag(self, tag):
        if tag == 'i':
            self.date = False
        if self.depth and tag == 'div':
            self.depth -= 1

class ArticleBody(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.found = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if self.depth:
                self.depth += 1
            elif 'txt_txt' in dict(attrs).get('class', '').split():
                self.depth = 1
                self.found = True
        if self.depth and tag in ('p', 'br'):
            self.parts.append('\n')

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.depth and tag == 'div':
            self.depth -= 1

def _get(url):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.court.gov.cn' or p.fragment or (not (p.path == '/search.html' or (re.fullmatch('/zixun/xiangqing/\\d+\\.html', p.path) and (not p.query)))):
        raise ValueError('仅支持最高人民法院官网搜索及资讯正文')
    return release_runtime.run(['curl', '--compressed', '--fail', '--silent', '--show-error', '--max-time', '20', url], check=True, capture_output=True).stdout.decode('utf-8')

def court_site_search(keyword, page=1):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or (not isinstance(page, int)) or (not 1 <= page <= 100):
        raise ValueError('请输入关键词及 1–100 的页码')
    url = ROOT + '/search.html?' + urlencode({'content': keyword, 'page': page})
    p = SearchResults()
    p.feed(_get(url))
    return {'source_url': url, 'items': p.items, 'note': '官网站内检索结果，仅保留资讯详情链接；空结果也可能因网页改版，请核对原站。'}

def court_site_article_detail(url):
    p = urlparse(url)
    if not re.fullmatch('/zixun/xiangqing/\\d+\\.html', p.path):
        raise ValueError('仅支持资讯详情')
    body = ArticleBody()
    body.feed(_get(url))
    text = '\n'.join((x.strip() for x in ''.join(body.parts).splitlines() if x.strip()))
    if not body.found or len(text) < 100:
        raise ValueError('未识别正文')
    return {'url': url, 'text': text, 'note': '最高人民法院官网资讯文章；不是裁判文书网或全部法律案例。'}
