"""浙大馆方 31 本 RSC 书单中单书的 Crossref 公开章节题录。"""
import release_runtime
import requests
from rsc_zju_books_adapters import search
BASE = 'https://api.crossref.org/works/'

def rsc_book_chapters(query, book_doi, page=1, page_size=10, timeout=25):
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('关键词须为 1–200 字')
    if not isinstance(book_doi, str):
        raise ValueError('请选择馆方书单中的书籍 DOI')
    books = {x['doi'].lower(): x for x in search()['items']}
    doi = book_doi.strip().lower()
    if doi not in books:
        raise ValueError('请选择馆方 31 本书单中的书籍 DOI')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (page, page_size))) or page < 1 or (not 1 <= page_size <= 20):
        raise ValueError('页码须大于零，每页 1–20 条')
    if (page - 1) * page_size + page_size > 10000:
        raise ValueError('Crossref offset + rows must not exceed 10000')
    r = requests.get(BASE + doi, timeout=timeout)
    r.raise_for_status()
    book = r.json().get('message', {})
    if book.get('DOI', '').lower() != doi:
        raise ValueError('Crossref 书籍 DOI 不一致')
    isbn = next((x['value'] for x in book.get('isbn-type', []) if x.get('type') == 'print' and x.get('value')), None)
    if not isbn:
        raise ValueError('Crossref 未提供纸本 ISBN，无法准确限定章节范围')
    r = requests.get(BASE, params={'filter': f'isbn:{isbn},type:book-chapter', 'query': query.strip(), 'rows': page_size, 'offset': (page - 1) * page_size}, timeout=timeout)
    r.raise_for_status()
    d = r.json().get('message', {})
    items = d.get('items')
    total = d.get('total-results')
    if not isinstance(items, list) or not isinstance(total, int):
        raise ValueError('Crossref 返回结构异常')
    rows = []
    for x in items:
        chapter_doi = x.get('DOI', '')
        titles = x.get('title', [])
        if not chapter_doi.lower().startswith(doi + '-') or not titles:
            continue
        rows.append({'doi': chapter_doi, 'title': titles[0], 'url': x.get('URL'), 'published': x.get('published', {}).get('date-parts')})
    return {'source': 'Crossref 公开章节元数据', 'book': books[doi], 'print_isbn': isbn, 'query': query.strip(), 'page': page, 'upstream_total': total, 'items': rows, 'library_url': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1079', 'note': '书目来自馆方 31 册快照；按 Crossref 纸本 ISBN 查询后再按所选书 DOI 前缀筛选，上游总数不一定等于筛选后总数，可能空页或遗漏。公开题录不证明当前订购及全文权限。'}
