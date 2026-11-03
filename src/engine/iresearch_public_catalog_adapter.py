"""iResearch e-book public catalog, not a purchased-only filter."""
import release_runtime
import requests
BASE = 'https://www.iresearchbook.cn/'

def search(keyword, page=1, limit=5, session=None, field='all', author=''):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('每页最多 10 条')
    fields = {'all': 'all', 'title': 'name_all', 'author': 'author', 'publisher': 'publishCompany', 'year': 'publishYear', 'isbn': 'isbn', 'subtitle': 'subtitle', 'series': 'seriesName', 'subject': 'antistop', 'summary': 'summary', 'classification': 'classZtf'}
    if field not in fields:
        raise ValueError('不支持的检索字段')
    if not isinstance(author, str) or len(author) > 100 or any((ord(c) < 32 for c in author)):
        raise ValueError('作者须为不超过100字的单行文本')
    author = author.strip()
    if author and field != 'title':
        raise ValueError('作者组合仅支持书名字段')
    q = keyword.strip()
    s = session or requests.Session()
    s.get(BASE + 'search/book/queryAll', params={'searchField': fields[field], 'searchValue': q, 'officeId': '', 'searchKey': ''}, timeout=20).raise_for_status()
    p = {'pageNo': str(page), 'pageSize': str(limit), 'searchField': fields[field], 'searchValue': q, 'secondSearchField': 'author' if author else 'all', 'secondSearchValue': author, 'onlyReadBuyed': '0', 'hasFacet': 'true'}
    r = s.post(BASE + 'search/book/query', data=p, timeout=25)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or type(j.get('total')) is not int or j['total'] < 0 or (not isinstance(j.get('books'), list)) or (len(j['books']) > limit):
        raise RuntimeError('书目响应异常')
    expected = min(limit, max(0, j['total'] - (page - 1) * limit))
    if len(j['books']) != expected:
        raise RuntimeError('站方返回条数与总数及页码不一致，可能数据变化或响应不完整')
    items = []
    for x in j['books']:
        if not isinstance(x, dict) or not isinstance(x.get('id'), str) or (not isinstance(x.get('name'), str)):
            raise RuntimeError('书目编号或名称缺失')
        item = {'id': x['id'], 'title': x['name'], 'original_title': x.get('nameENG'), 'author': x.get('author'), 'publisher': x.get('publishCompany'), 'publish_year': x.get('publishYear'), 'publish_date_raw': x.get('publishDate'), 'print_isbn': x.get('pisbn'), 'ebook_isbn': x.get('eisbn')}
        if field == 'classification':
            item['classification_raw'] = x.get('classZtf')
        if field in ('subtitle', 'series', 'subject', 'summary'):
            item.update({'subtitle_raw': x.get('subtitle'), 'series_raw': x.get('seriesName'), 'subject_terms_raw': x.get('antistop')})
        items.append(item)
    result = {'source': '爱学术电子书平台', 'query': q, 'page': page, 'page_size': limit, 'total': j['total'], 'items': items[:limit], 'note': '公开全部字段检索，未筛选已购；出版日期数值保留原站原值，浙江大学机构身份和全文权限未验证。'}
    if field != 'all':
        result['field_requested'] = field
        result['note'] = '公开题录的单字段请求，源站未回显字段或页码；匹配方式及 ISBN 精确性须逐项核对，未限定已购，学校机构身份和全文权限未验证。出版日期保留原站原值。'
    if field == 'classification':
        result['note'] += ' 源站样本为分类前缀匹配，规则及逐项分类须核对。'
    if field == 'summary':
        result['note'] += ' 简介仅用于检索，不输出简介或正文。'
    result['note'] += ' 已按源总数与请求页次校验条数；站方未回显页码，数据可能变化。'
    if author:
        result['author_requested'] = author
        result['note'] += ' 书名与作者组合已抽验，站方不回显条件与页码；逐项相关性须核对。'
    return result
