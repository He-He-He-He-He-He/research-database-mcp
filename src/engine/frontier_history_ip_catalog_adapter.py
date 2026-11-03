"""Campus-network catalog search for the China Frontier History database."""
import release_runtime
import re
import requests
from bs4 import BeautifulSoup
BASE = 'http://10.15.61.59:8080/'

def search(keyword, page=1, limit=20, session=None, search_type='all'):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must contain 1–100 characters')
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError('page must be a positive integer')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 20):
        raise ValueError('limit must be between 1 and 20')
    types = {'all': 'all', 'literature': 'liter', 'author': 'author', 'category': 'cat', 'dynasty': 'dt'}
    if search_type not in types:
        raise ValueError('不支持的检索类型')
    q = keyword.strip()
    client = session or requests.Session()
    params = {'keyword': q, 'pagenum': page}
    if search_type != 'all':
        params['type'] = types[search_type]
    response = client.get(BASE + 'searching.html', params=params, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text(' ', strip=True)
    if not re.search('用[戶户]\\s*[：:]\\s*zjdx\\b', text, re.I):
        raise RuntimeError('未确认学校账户界面')
    if '檢索結果' not in text or q not in text or (not soup.select_one('.list')):
        raise RuntimeError('检索结果页或查询词未确认')
    if search_type != 'all':
        chosen = soup.select_one('select[name=type] option[selected]')
        if not chosen or chosen.get('value') != types[search_type]:
            raise RuntimeError('站方未回显检索类型')
    selected = soup.select_one('.page select option[selected]')
    options = soup.select('.page select option')
    if not selected or not options:
        raise RuntimeError('未确认页码')
    actual_page = int(selected.get('value', '0'))
    total_pages = int(options[-1].get('value', '0'))
    items = []
    for a in soup.select('.list a[href]'):
        m = re.fullmatch('literature/(\\d+)/', a.get('href', ''))
        title = a.get_text(' ', strip=True)
        if m and title:
            items.append({'id': m.group(1), 'title': title, 'url': BASE + a['href']})
    result = {'source': '中国边疆史地研究资料数据库', 'query': q, 'requested_page': page, 'page': actual_page, 'total_pages': total_pages, 'source_page_items': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'note': '校内 HTTP 站点显示用户 zjdx；检索覆盖文献、作者、分类、朝代，题录不代表全文权限。超出末页时原站返回末页；结果总数未提供；limit 仅截取原站当前页，若 truncated 为 true，继续请求下一站方页会遗漏本页未返回记录，请改用 limit=20 取整页。'}
    if search_type != 'all':
        result['search_type_requested'] = search_type
        result['note'] += ' 站方已回显类型；匹配和逐书权限仍须核对。'
    return result
