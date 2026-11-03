"""Browse the ZJU large-document collection's series catalogue, one page at a time."""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'http://csid.zju.edu.cn/doclib/'
CATEGORIES = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'X', 'Z'}

def _validate_page(actual, pages, total, requested, records):
    if actual != requested or total < 0 or pages < 0 or (total > 0 and (pages != (total + 11) // 12 or actual > pages)) or (len(records) != min(12, max(0, total - (actual - 1) * 12))):
        raise ValueError('catalogue page or parsed record count inconsistent')

def browse(category='', page=1, timeout=20):
    if not isinstance(category, str) or category not in CATEGORIES | {''}:
        raise ValueError('category must be empty or a supported classification letter')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be an integer from 1 to 100')
    r = requests.get(urljoin(BASE, 'books'), params={'tag': '1', 'text': '', 'c': category, 'oc': '', 'pageNumber': page, 'pageSize': 12}, timeout=timeout)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    body = s.get_text(' ', strip=True)
    m = re.search('(\\d+)\\s*/\\s*(\\d+)\\s*页\\s*共\\s*(\\d+)\\s*条记录', body)
    if not m:
        raise ValueError('catalogue pagination not recognized')
    records = []
    for a in s.select('a[href^="book?id="]'):
        name, href = (a.get_text(' ', strip=True), a.get('href', ''))
        match = re.fullmatch('book\\?id=([a-fA-F0-9]{32})', href)
        if name and match:
            records.append({'id': match.group(1), 'title': name, 'url': urljoin(BASE, href)})
    actual, pages, total = map(int, m.groups())
    _validate_page(actual, pages, total, page, records)
    return {'source': '浙江大学大型文献信息库', 'category': category, 'page': actual, 'total_pages': pages, 'total': total, 'records': records, 'note': '馆方提示数据尚不完整；目录非全文。上游为 HTTP，请勿提交敏感信息。'}
