"""Institution IP gazetteer advanced title and author search."""
import release_runtime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from digital_fangzhi_ip_catalog_adapter import BASE, ID_RE, _plain

def search(title='', author='', page=1, limit=15, session=None, publication_year='', edition=''):
    values = (title, author, publication_year, edition)
    if any((not isinstance(v, str) or len(v) > 100 or any((ord(c) < 32 for c in v)) for v in values)) or not any((v.strip() for v in values)):
        raise ValueError('须提供至少一个检索条件，单项不超过100字')
    if type(page) is not int or page < 1 or type(limit) is not int or (not 1 <= limit <= 15):
        raise ValueError('页码或数量无效')
    s = session or requests.Session()
    r = s.get(BASE, timeout=20)
    r.raise_for_status()
    if '欢迎您：浙江大学' not in BeautifulSoup(r.content, 'html.parser').get_text(' ', strip=True):
        raise RuntimeError('未确认浙江大学机构身份')
    body = {'action': 'getpagedata', 'pagenum': str(page), 'pSet': '13', 'pTitle': title.strip(), 'pChopsticksAre': author.strip(), 'pVolumes': '', 'pVersion': edition.strip(), 'pCLC': '', 'pVolumeName': '', 'pVolumeNumber': '', 'pPublicationYear': publication_year.strip(), 'pPublisher': '', 'pCharacterization': '', 'ptextsearch': ''}
    r = s.post(BASE + 'bookListHandler.ashx', data=body, timeout=20)
    r.raise_for_status()
    try:
        rows = r.json()
    except ValueError:
        raise RuntimeError('方志高级检索未返回 JSON') from None
    if not isinstance(rows, list) or len(rows) > 15:
        raise RuntimeError('方志高级检索响应异常')
    items = []
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError('题录异常')
        raw = row.get('Title_Liability') or ''
        a = BeautifulSoup(raw, 'html.parser').find('a', href=True)
        m = ID_RE.match(a['href']) if a else None
        if not m or not a.get_text(' ', strip=True):
            raise RuntimeError('书号或标题缺失')
        ident = m.group(1)
        items.append({'id': ident, 'title': a.get_text(' ', strip=True), 'title_responsibility_raw': _plain(raw), 'section': _plain(row.get('ContenTtitle')), 'edition': _plain(row.get('pVersion')) or None, 'publication_year': _plain(row.get('pPublicationYear')) or None, 'url': BASE + 'BookDetails.aspx?' + urlencode({'pID': ident})})
    result = {'source': '中国数字方志库高级检索', 'institution': '浙江大学', 'title_query': title.strip(), 'author_query': author.strip(), 'page': page, 'source_page_items': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'note': '官网高级条件组合；源未回显筛选条件或页码，繁简及分词须核对。无总数，空页不区分零结果或超页；同书可能按章节重复。limit 只截取当前源页，连续读取请用15；内网 HTTP 勿输入敏感信息；正文权限未核。'}
    if publication_year.strip() or edition.strip():
        result['extra_filters'] = {'publication_year': publication_year.strip(), 'edition': edition.strip()}
    return result
