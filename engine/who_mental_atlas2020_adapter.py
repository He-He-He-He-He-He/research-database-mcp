"""WHO Mental Health Atlas 2020 current country directory and PDF text."""
import release_runtime
import io, re, urllib.parse, requests
from html.parser import HTMLParser
from pypdf import PdfReader
CATALOG = 'https://www.who.int/teams/mental-health-and-substance-use/data-research/mental-health-atlas'

class Links(HTMLParser):

    def __init__(self):
        super().__init__()
        self.items = []
        self.url = None
        self.label = []

    def handle_starttag(self, t, attrs):
        if t == 'a':
            self.url = dict(attrs).get('href')
            self.label = []

    def handle_data(self, s):
        if self.url:
            self.label.append(s)

    def handle_endtag(self, t):
        if t == 'a' and self.url:
            self.items.append((' '.join(''.join(self.label).split()), self.url))
            self.url = None

def fetch(url, maxsize=4000000):
    with requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=25, stream=True) as r:
        r.raise_for_status()
        data = b''
        for chunk in r.iter_content(65536):
            data += chunk
            if len(data) > maxsize:
                raise ValueError('来源文件超过大小限制')
        h = dict(r.headers)
    return (data, h)

def catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('关键词无效')
    data, h = fetch(CATALOG)
    p = Links()
    p.feed(data.decode('utf-8', 'replace'))
    items = []
    for title, url in p.items:
        if title.startswith('Mental Health Atlas ') and title.endswith(' 2020') and url.startswith('https://www.who.int/publications/m/item/') and (keyword.casefold() in title.casefold()):
            items.append({'title': title, 'item_url': url})
    return {'source': CATALOG, 'last_modified': h.get('Last-Modified'), 'query': keyword, 'count_returned': len(items), 'items': items, 'note': '这是当前 WHO 国家报告网页目录，目录本身可能增删修订；目录数不等同成员国或上报数。每份报告可能在 2020 年之后发布，不能按标题判断发布日期。'}

def document(keyword):
    x = catalog(keyword)
    if len(x['items']) != 1:
        raise ValueError('需要唯一匹配国家，请先通过目录搜索并输入更精确名称')
    item = x['items'][0]
    data, headers = fetch(item['item_url'])
    p = Links()
    p.feed(data.decode('utf-8', 'replace'))
    urls = []
    for _, url in p.items:
        u = urllib.parse.urlsplit(url)
        if u.scheme == 'https' and u.hostname == 'cdn.who.int' and u.path.startswith('/media/docs/default-source/mental-health/mental-health-atlas-2020-country-profiles/') and u.path.endswith('.pdf'):
            urls.append(url)
    if len(set(urls)) != 1:
        raise ValueError('官方条目未发现唯一 PDF，需人工核验')
    url = urls[0]
    body, head = fetch(url, 10000000)
    pdf = PdfReader(io.BytesIO(body))
    pages = [{'page': i + 1, 'text': page.extract_text() or ''} for i, page in enumerate(pdf.pages)]
    return {'item': item, 'source_pdf': url, 'http_last_modified': head.get('Last-Modified'), 'pdf_metadata': {str(k): str(v) for k, v in (pdf.metadata or {}).items()}, 'pages': pages, 'caution': '报告题为2020不代表2020年发布。各国条目和 PDF 可后来修改；服务器时间、PDF内部时间均不能单独证明历史文件不可变。内容多依成员国提供，年份和定义须逐项核实；文字抽取可能打乱行列，图表、图像未必能识别，请核对原 PDF。'}
