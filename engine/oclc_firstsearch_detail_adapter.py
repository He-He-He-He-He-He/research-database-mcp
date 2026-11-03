"""Read a selected first-page FirstSearch detailed record, using a temporary library session."""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ENTRY = 'https://firstsearch.oclc.org/FSIP'
DATABASES = ('ArticleFirst', 'ClasePeriodica', 'Ebooks', 'ECO', 'ERIC', 'GPO', 'MEDLINE', 'OpenAccessContent', 'SCIPIO', 'WorldCat', 'WorldCatDissertations')
FIELDS = {'Title:': 'title', 'Author(s):': 'authors_as_printed', 'Publication:': 'publication', 'Year:': 'year', 'Description:': 'description', 'Language:': 'language', 'Standard No:': 'standard_numbers', 'Source:': 'source', 'Document Type:': 'document_type'}

def detail_first(query, database='WorldCat', session=None, *, record_index=1, page=1):
    if not isinstance(query, str) or not query.strip() or len(query) > 200 or (database not in DATABASES) or (type(record_index) is not int) or (not 1 <= record_index <= 10) or (type(page) is not int) or (not 1 <= page <= 5):
        raise ValueError('需要关键词、支持的数据库、1–5 页及 1–10 的页内序号')
    q = query.strip()
    s = session or requests.Session()

    def get(url):
        if urlparse(url).scheme != 'https' or urlparse(url).hostname != 'firstsearch.oclc.org':
            raise ValueError('FirstSearch 链接域名不匹配')
        r = s.get(url, timeout=25)
        r.raise_for_status()
        return (r, BeautifulSoup(r.content, 'html.parser'))
    r, p = get(ENTRY)
    if 'ZHEJIANG UNIV' not in p.get_text(' ', strip=True):
        raise ValueError('未识别浙江大学机构会话')
    link = next((a for a in p.find_all('a', href=True) if a.get_text(strip=True) == database), None)
    if not link:
        listing = next((a for a in p.find_all('a', href=True) if a.get_text(strip=True) == 'List All Databases'), None)
        if not listing:
            raise ValueError('未找到数据库目录')
        r, p = get(urljoin(r.url, listing['href']))
        link = next((a for a in p.find_all('a', href=True) if a.get_text(strip=True) == database), None)
    if not link:
        raise ValueError('数据库不存在或未显示')
    r, p = get(urljoin(r.url, link['href']))
    form = next((f for f in p.find_all('form') if 'FSQUERY' in f.get('action', '')), None)
    if not form:
        raise ValueError('检索表单缺失')
    action = urljoin(r.url, form['action'])
    if urlparse(action).scheme != 'https' or urlparse(action).hostname != 'firstsearch.oclc.org':
        raise ValueError('检索入口异常')
    r = s.post(action, data={'action': 'Search', 'dbname': database, 'term1': q, 'index1': 'kw:', 'term2': '', 'term3': ''}, timeout=25)
    r.raise_for_status()
    p = BeautifulSoup(r.content, 'html.parser')
    for _ in range(1, page):
        nextlink = next((a for a in p.find_all('a', href=True) if any(('Next page of results' in (im.get('alt') or '') for im in a.find_all('img')))), None)
        if not nextlink:
            raise ValueError('结果没有下一页')
        r, p = get(urljoin(r.url, nextlink['href']))
    rows = [tr for tr in p.find_all('tr') if tr.find('input', attrs={'name': re.compile('^BookMark_')})]
    if len(rows) < record_index:
        raise ValueError('该序号超出当前页结果数')
    a = next((x for x in rows[record_index - 1].find_all('a', href=True) if 'fetchtype=fullrecord' in x['href'] and x.get_text(' ', strip=True)), None)
    if not a:
        raise ValueError('所选结果缺少详情入口')
    expected = a.get_text(' ', strip=True)
    r, p = get(urljoin(r.url, a['href']))
    title = p.title.get_text(' ', strip=True) if p.title else ''
    expected_db_title = {'Ebooks': 'Electronic Books', 'ClasePeriodica': 'Clase and Periodica', 'OpenAccessContent': 'Open Access Content', 'WorldCatDissertations': 'WorldCat dissertations and theses'}.get(database, database)
    if 'detailed record' not in title.casefold() or expected_db_title.casefold() not in title.casefold() or 'ZHEJIANG UNIV' not in p.get_text(' ', strip=True):
        raise ValueError('详情页面或机构会话不匹配')
    fields = {}
    for tr in p.find_all('tr'):
        cells = tr.find_all(['td', 'th'], recursive=False)
        if len(cells) < 2:
            continue
        key = FIELDS.get(cells[0].get_text(' ', strip=True))
        if key and key not in fields:
            fields[key] = cells[1].get_text(' ', strip=True)

    def normalize_title(text):
        return re.sub('\\s+([.,;:!?])', '\\1', re.sub('\\s+', ' ', text)).strip()
    if normalize_title(fields.get('title', '')) != normalize_title(expected):
        raise ValueError('详情题名与所选结果不匹配')
    return {'source': 'OCLC FirstSearch / ' + database, 'institution': 'ZHEJIANG UNIV', 'query': q, 'page': page, 'record_index': record_index, 'fields': fields, 'note': '当前机构会话正常搜索后当前页所选序号详情的题录字段；未读取摘要、正文或保存会话链接。未证明学校持有该作品全文；不同数据库字段可能不同。' + ('该库实测部分西班牙语、葡萄牙语字符在上游响应中已显示异常，原样保留，请核对原始出处。' if database == 'ClasePeriodica' else '')}
