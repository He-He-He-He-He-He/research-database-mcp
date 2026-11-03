"""查询 NCBI Bookshelf Landes Bioscience 出版记录公开元数据。"""
import release_runtime
import requests
BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

def ncbi_landes_books_search(keyword, page=1, page_size=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150 or any((x in keyword for x in ['"', '[', ']'])):
        raise ValueError('关键词须为1–150字且不含引号或方括号')
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or (not 1 <= page_size <= 10):
        raise ValueError('页码须大于零，每页1至10条')
    q = keyword.strip()
    term = '"Landes Bioscience"[Publisher] AND "' + q + '"[All Fields]'
    r = requests.get(BASE + 'esearch.fcgi', params={'db': 'books', 'term': term, 'retmode': 'json', 'retstart': (page - 1) * page_size, 'retmax': page_size}, timeout=20)
    r.raise_for_status()
    sr = r.json().get('esearchresult', {})
    ids = sr.get('idlist', [])
    if 'count' not in sr:
        raise ValueError('NCBI 未返回结果数量')
    items = []
    if ids:
        r = requests.get(BASE + 'esummary.fcgi', params={'db': 'books', 'id': ','.join(ids), 'retmode': 'json'}, timeout=20)
        r.raise_for_status()
        d = r.json().get('result', {})
        for uid in ids:
            x = d.get(uid)
            if not x or not x.get('title'):
                raise ValueError('NCBI 题录结果不完整')
            acc = x.get('accessionid')
            items.append({'uid': uid, 'title': x['title'], 'type': x.get('rtype'), 'publication_date': x.get('pubdate'), 'accession': acc, 'book_accession': x.get('bookaccessionid'), 'url': 'https://www.ncbi.nlm.nih.gov/books/' + acc + '/' if acc and acc.startswith('NBK') else None})
    return {'source': 'NCBI Bookshelf Landes Bioscience 出版记录元数据', 'query': q, 'query_translation': sr.get('querytranslation'), 'total': int(sr['count']), 'page': page, 'items': items, 'note': '仅出版社字段限定的公开 NCBI Books 元数据；结果可能为章节或小节，不等于浙大购买的完整馆藏，未下载正文。'}
