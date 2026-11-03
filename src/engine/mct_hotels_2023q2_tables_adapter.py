"""2023 Q2 star-rated hotel tables republished by China Tourism News."""
import release_runtime
import io
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import openpyxl
ARTICLE = 'https://www.ctnews.com.cn/xxk/tzgg/content/2023-08/25/content_148643.html'

def catalog():
    r = requests.get(ARTICLE, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    items = []
    seen = set()
    for a in s.select('a[href]'):
        url = urljoin(ARTICLE, a['href'])
        title = a.get_text(' ', strip=True)
        if url.startswith('https://www.ctnews.com.cn/') and url.lower().endswith('.xlsx') and (url not in seen):
            items.append({'title': title, 'url': url})
            seen.add(url)
    if not items:
        raise ValueError('no XLSX attachments found')
    return {'period': '2023年第二季度', 'publisher': '中国旅游新闻网转载文化和旅游部资料', 'article_url': ARTICLE, 'items': items}

def table(url, keyword=''):
    if not isinstance(keyword, str):
        raise ValueError('keyword must be a string')
    match = next((x for x in catalog()['items'] if x['url'] == url), None)
    if match is None:
        raise ValueError('URL is not in article attachment list')
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    if not r.content.startswith(b'PK\x03\x04'):
        raise ValueError('response is not XLSX')
    book = openpyxl.load_workbook(io.BytesIO(r.content), data_only=True)
    sheets = []
    for ws in book:
        if ws.max_row > 5000 or ws.max_column > 300:
            raise ValueError('sheet exceeds safety limit')
        rows = []
        for row in ws.iter_rows():
            values = [c.value for c in row]
            if any((v is not None for v in values)) and (not keyword or any((keyword in str(v) for v in values if v is not None))):
                rows.append({'row': row[0].row, 'cells': values})
        sheets.append({'name': ws.title, 'merged_ranges': [str(x) for x in ws.merged_cells.ranges], 'rows': rows})
    book.close()
    return {'period': '2023年第二季度', 'publisher': '中国旅游新闻网转载文化和旅游部资料', 'source_article': ARTICLE, **match, 'sheets': sheets}
