"""全国国民阅读调查官网目录及第二十三次调查全文段落查询。"""
import release_runtime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import re
ROOT = Path(__file__).parent
INDEX_URL = 'https://www.nationalreading.gov.cn/ydzg/dcbg/qggmyddc/'
REPORT_URL = 'https://www.nationalreading.gov.cn/wzzt/dwjqmyddh/dhzx/bd/202604/t20260420_985575.html'

class _Links(HTMLParser):

    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.parts = []

    def handle_data(self, data):
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            text = ' '.join(''.join(self.parts).split())
            if re.search('全国国民阅读调查.*\\d{4}-\\d{2}-\\d{2}', text):
                self.links.append({'title': text, 'url': urljoin(INDEX_URL, self.href)})
            self.href = None

class _Paragraphs(HTMLParser):

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.in_p = False
        self.text = []
        self.paragraphs = []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            if tag == 'div':
                self.depth += 1
            if tag == 'p':
                self.in_p = True
                self.text = []
        elif tag == 'div' and 'trs_editor_view' in dict(attrs).get('class', '').split():
            self.depth = 1

    def handle_data(self, data):
        if self.depth and self.in_p:
            self.text.append(data)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == 'p' and self.in_p:
            text = ' '.join(''.join(self.text).split())
            if text:
                self.paragraphs.append(text)
            self.in_p = False
        if tag == 'div':
            self.depth -= 1

def list_reading_surveys():
    """2026 年 10 月取得的官网目录快照，提供发布年份和原文链接。"""
    p = _Links()
    p.feed((ROOT / '全国国民阅读调查目录快照.html').read_text(encoding='utf-8'))
    if len(p.links) != 8:
        raise ValueError('目录解析结果异常')
    return p.links

def search_reading_survey_2025(keyword=''):
    """在 2025 年阅读状况（第二十三次调查）发布正文中按段落搜索。"""
    p = _Paragraphs()
    p.feed((ROOT / '第二十三次全国国民阅读调查主要发现.html').read_text(encoding='utf-8'))
    if not p.paragraphs:
        raise ValueError('调查正文未识别到段落')
    keyword = keyword.strip()
    return [{'paragraph': n, 'text': text, 'reference_year': 2025, 'publication_year': 2026, 'source_url': REPORT_URL} for n, text in enumerate(p.paragraphs, 1) if not keyword or keyword in text]
