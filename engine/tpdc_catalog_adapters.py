"""国家青藏高原科学数据中心公开索引页及数据集结构化元数据。"""
import release_runtime
import json
import re
import requests
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs
BASE = 'https://www.tpdc.ac.cn/view/googleSearch/'
UUID = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'

class _Links(HTMLParser):

    def __init__(self):
        super().__init__()
        self.href = None
        self.parts = []
        self.items = []

    def handle_starttag(self, t, attrs):
        if t == 'a':
            self.href = dict(attrs).get('href')
            self.parts = []

    def handle_data(self, s):
        if self.href is not None:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.href is not None:
            self.items.append((self.href, ' '.join(''.join(self.parts).split())))
            self.href = None

class _Metadata(HTMLParser):

    def __init__(self):
        super().__init__()
        self.active = False
        self.parts = []

    def handle_starttag(self, t, attrs):
        if t == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.active = True

    def handle_data(self, s):
        if self.active:
            self.parts.append(s)

    def handle_endtag(self, t):
        if t == 'script':
            self.active = False

def _get(path, params=None):
    r = requests.get(BASE + path, params=params, timeout=20, allow_redirects=False)
    if r.status_code != 200:
        raise RuntimeError('上游 HTTP ' + str(r.status_code))
    r.encoding = 'utf-8'
    return r.text

def tpdc_catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词长度须不超过 100')
    p = _Links()
    p.feed(_get('dataList'))
    out = []
    for href, title in p.items:
        u = urlparse(href)
        ids = parse_qs(u.query).get('metadataId', [])
        if u.path == 'dataDetail' and len(ids) == 1 and re.fullmatch(UUID, ids[0]) and (keyword in title):
            out.append({'id': ids[0], 'title': title})
    if not out and (not keyword):
        raise ValueError('未识别公开索引页')
    return out

def tpdc_catalog_detail(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(UUID, identifier):
        raise ValueError('请输入数据集 UUID')
    p = _Metadata()
    p.feed(_get('dataDetail', {'metadataId': identifier}))
    x = json.loads(''.join(p.parts))
    if x.get('@type') != 'Dataset' or x.get('@id') != identifier:
        raise ValueError('未识别数据集元数据')
    keys = ('@id', 'name', 'description', 'keywords', 'identifier', 'url', 'datePublished', 'spatialCoverage', 'inLanguage')
    return {k: x.get(k) for k in keys}
