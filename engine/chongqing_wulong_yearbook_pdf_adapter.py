"""Official Wulong district statistical data collection PDFs."""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
INDEX = 'https://cqwl.gov.cn/bmjz_sites/bm/tjj/zwgk_98942/fdzdgknr_98944/tjxxtj/sjfb/tjnj/'

def catalog():
    r = requests.get(INDEX, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    result = []
    for a in soup.select('a[href]'):
        title = ' '.join(a.get_text(' ', strip=True).split())
        m = re.fullmatch('武隆统计资料汇编[—－-]+(\\d{4})', title)
        href = a['href']
        if m and re.fullmatch('\\./\\d{6}/t\\d+_\\d+\\.html', href):
            result.append({'edition': int(m.group(1)), 'title': title, 'article_url': urljoin(INDEX, href), 'catalog_url': INDEX})
    if not result:
        raise ValueError('catalog missing or format changed')
    return result

def document(year):
    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError('year must be an integer')
    items = [i for i in catalog() if i['edition'] == year]
    if len(items) != 1:
        raise ValueError('edition missing or ambiguous')
    item = items[0]
    r = requests.get(item['article_url'], timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    refs = []
    for a in soup.select('[onclick]'):
        m = re.search("downloadFj\\('[^']*','(\\./W\\d+\\.pdf)'\\)", a['onclick'], re.I)
        if m:
            refs.append(m.group(1))
    refs = list(dict.fromkeys(refs))
    if len(refs) != 1:
        raise ValueError('PDF link missing or ambiguous')
    url = urljoin(item['article_url'], refs[0])
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.netloc != 'cqwl.gov.cn':
        raise ValueError('unexpected source host')
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    if not r.content.startswith(b'%PDF-'):
        raise ValueError('response is not a PDF')
    return {**item, 'url': url, 'source': '重庆市武隆区统计局', 'content_type': 'application/pdf', 'content': r.content}
