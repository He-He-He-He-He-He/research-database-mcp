"""Official China Statistical Yearbook 2015-2020 image tables."""
import release_runtime
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
import requests
ROOT = 'https://www.stats.gov.cn/sj/ndsj/'
PATH = re.compile('/sj/ndsj/(2015|2016|2017|2018|2019|2020)/html/[A-Za-z0-9_-]+\\.jpg', re.I)

class CatalogParser(HTMLParser):

    def __init__(self, base):
        super().__init__()
        self.base = base
        self.current = None
        self.parts = []
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag != 'a':
            return
        href = dict(attrs).get('href', '')
        u = urlsplit(urljoin(self.base, href))
        if u.scheme == 'https' and u.netloc == 'www.stats.gov.cn' and PATH.fullmatch(u.path) and (not u.query) and (not u.fragment):
            self.current = u.geturl()
            self.parts = []

    def handle_data(self, data):
        if self.current is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            title = ' '.join(''.join(self.parts).split())
            if re.match('^\\d+[.-]\\d+', title):
                self.items.append({'title': title, 'url': self.current})
            self.current = None

def catalog(year, keyword=''):
    if type(year) is not int or year not in range(2015, 2021):
        raise ValueError('year must be 2015-2020')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    base = ROOT + str(year) + '/'
    r = requests.get(base + 'left.htm', timeout=30)
    r.raise_for_status()
    p = CatalogParser(base)
    p.feed(r.content.decode('gb18030'))
    if not p.items:
        raise RuntimeError('no image table entries found')
    items = [x for x in p.items if keyword in x['title']]
    return {'source_url': base + 'left.htm', 'yearbook_year': year, 'total': len(p.items), 'items': items, 'returned': len(items)}

def table_image(url):
    u = urlsplit(url)
    if u.scheme != 'https' or u.netloc != 'www.stats.gov.cn' or (not PATH.fullmatch(u.path)) or u.query or u.fragment:
        raise ValueError('URL must be an official 2015-2020 yearbook image')
    r = requests.get(url, timeout=45, allow_redirects=False)
    r.raise_for_status()
    if len(r.content) > 20 * 1024 * 1024 or not r.content.startswith(bytes.fromhex('ffd8ff')):
        raise ValueError('response is not a bounded JPEG')
    return r.content
