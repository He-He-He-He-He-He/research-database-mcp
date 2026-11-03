"""Campus-local theory resources book catalog; no book text."""
import release_runtime
import requests
from bs4 import BeautifulSoup
BASE = 'http://10.203.97.151/'
COLUMNS = '769,313,314,315,327,415,416,419,422,423,424,425,426,427'

def search(keyword, page=1, limit=5, session=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 8):
        raise ValueError('每页最多 8 条')
    q = keyword.strip()
    s = session or requests.Session()
    r = s.get(BASE, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, 'html.parser')
    if not soup.title or '中国共产党思想理论资源数据库' not in soup.title.get_text():
        raise RuntimeError('未识别馆藏网站')
    p = {k: '' for k in ('orderby', 'name', 'author', 'isbn', 'relatedWords', 'translator', 'starttime', 'endtime', 'filtersql')}
    p.update(specialid=COLUMNS, columnId=COLUMNS, page=str(page - 1), pageSize=str(limit), searchtext=q, panel='system')
    r = s.post(BASE + 'Service/', params={'logic': 'bookController', 'call': 'searchBookByColumnAndBookinfo'}, data=p, timeout=20)
    r.raise_for_status()
    j = r.json()
    d = j.get('result') if isinstance(j, dict) else None
    if not isinstance(d, dict) or type(d.get('totalCount')) is not int or d['totalCount'] < 0 or (not isinstance(d.get('bookinfo'), list)) or (len(d['bookinfo']) > limit):
        raise RuntimeError('图书检索响应异常')
    items = []
    for x in d['bookinfo']:
        if not isinstance(x, dict) or not isinstance(x.get('bookid'), str) or (not isinstance(x.get('bookname'), str)):
            raise RuntimeError('书目编号或名称缺失')
        items.append({'id': x['bookid'], 'title': BeautifulSoup(x['bookname'], 'html.parser').get_text('', strip=True), 'author': x.get('author') or None, 'isbn': x.get('isbn') or None, 'publisher': x.get('publish') or None, 'release_date': x.get('releaseDate') or None})
    return {'source': '中国共产党思想理论资源数据库及扩展库', 'query': q, 'page': page, 'page_size': limit, 'total': d['totalCount'], 'items': items[:limit], 'note': '校内 HTTP 图书检索，包含历史和哲学扩展库；页面未单独确认浙江大学机构标识，全文未验证。'}
