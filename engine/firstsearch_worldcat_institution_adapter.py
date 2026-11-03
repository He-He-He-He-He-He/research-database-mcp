"""OCLC FirstSearch 的浙江大学 IP 会话 WorldCat 题录；不输出会话链接。"""
import release_runtime
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ENTRY = 'https://libdb.zju.edu.cn/s/lib/libtb/turning/474'
INFO = 'https://libdb.zju.edu.cn/s/lib/libtb/show/474'
DATABASES = {'WorldCat': 'WorldCat', 'ArticleFirst': 'ArticleFirst', 'ECO': 'Electronic Collections Online', 'ERIC': 'ERIC', 'Ebooks': 'Electronic Books', 'GPO': 'GPO Monthly Catalog', 'MEDLINE': 'Medline', 'OpenAccessContent': 'Open Access Content', 'SCIPIO': 'SCIPIO: Art and Rare Book Sales Catalog', 'WorldCatDissertations': 'WorldCat dissertations and theses', 'ClasePeriodica': 'Clase and Periodica'}

def _safe(base, href, path):
    if not isinstance(href, str):
        raise RuntimeError('FirstSearch 页面缺少操作链接')
    url = urljoin(base, href)
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'firstsearch.oclc.org' or p.path != path:
        raise RuntimeError('FirstSearch 操作链接目标异常')
    return url

def _page(html):
    b = BeautifulSoup(html, 'html.parser')
    text = b.get_text(' ', strip=True)
    if 'ZHEJIANG UNIV' not in text:
        raise RuntimeError('FirstSearch 未确认浙江大学机构会话')
    return (b, text)

def search(keyword, page=1, database='WorldCat', field='keyword'):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 200 or re.search('[\\x00-\\x1f]', keyword):
        raise ValueError('关键词须为 1–200 字单行文本')
    if type(page) is not int or not 1 <= page <= 10:
        raise ValueError('page 须为 1–10')
    if database not in DATABASES:
        raise ValueError('暂不支持该 FirstSearch 子库')
    fields = {'keyword': None, 'title': 'ti:', 'author': 'au:', 'isbn': 'nb:', 'subject': 'su:'}
    if field not in fields:
        raise ValueError('field 须为 keyword、title、author、isbn 或 subject')
    verified_fields = {'WorldCat': {'title', 'author', 'isbn', 'subject'}, 'ArticleFirst': {'title', 'author'}, 'ERIC': {'title', 'author', 'subject'}, 'MEDLINE': {'author', 'subject'}, 'Ebooks': {'title', 'author', 'subject'}, 'GPO': {'title', 'author', 'subject'}, 'OpenAccessContent': {'title', 'author', 'subject'}, 'SCIPIO': {'title'}, 'WorldCatDissertations': {'title', 'author', 'subject'}, 'ClasePeriodica': {'title', 'author', 'subject'}, 'ECO': {'title', 'author'}}
    if field != 'keyword' and field not in verified_fields.get(database, set()):
        raise ValueError('该子库与字段组合尚未验证')
    q = keyword.strip()
    s = requests.Session()
    try:
        r = s.get(ENTRY, timeout=25)
        r.raise_for_status()
        b, _ = _page(r.text)
        if urlparse(r.url).hostname != 'firstsearch.oclc.org':
            raise RuntimeError('FirstSearch 馆方入口目标异常')
        if field == 'keyword':
            forms = [f for f in b.select('form') if f.select_one('input[name="termqs"]') and f.select_one('select[name="topicdb"]')]
            if len(forms) != 1:
                raise RuntimeError('FirstSearch 首页检索表单异常')
            target = _safe(r.url, forms[0].get('action'), '/WebZ/FSHome')
            r = s.post(target, data={'termqs': q, 'topicdb': database, 'action': 'Search'}, timeout=25)
            r.raise_for_status()
            b, text = _page(r.text)
        else:
            link = next((a for a in b.find_all('a', href=True) if a.get_text(strip=True) == database), None)
            if not link:
                listing = next((a for a in b.find_all('a', href=True) if a.get_text(strip=True) == 'List All Databases'), None)
                if not listing:
                    raise RuntimeError('缺少子库列表入口')
                target = _safe(r.url, listing['href'], '/WebZ/FSPage')
                r = s.get(target, timeout=25)
                r.raise_for_status()
                b, _ = _page(r.text)
                link = next((a for a in b.find_all('a', href=True) if a.get_text(strip=True) == database), None)
            if not link:
                raise RuntimeError('缺少所选子库高级检索入口')
            target = _safe(r.url, link['href'], '/WebZ/LogDbChange')
            r = s.get(target, timeout=25)
            r.raise_for_status()
            b, _ = _page(r.text)
            forms = [f for f in b.select('form') if urlparse(urljoin(r.url, f.get('action', ''))).path == '/WebZ/FSQUERY' and f.select_one('select[name="index1"]')]
            if len(forms) != 1 or not forms[0].select_one('select[name="index1"] option[value="' + fields[field] + '"]'):
                raise RuntimeError('所选字段不在站方表单')
            target = _safe(r.url, forms[0].get('action'), '/WebZ/FSQUERY')
            r = s.post(target, data={'action': 'Search', 'dbname': database, 'term1': q, 'index1': fields[field], 'term2': '', 'term3': ''}, timeout=25)
            r.raise_for_status()
            b, text = _page(r.text)
        if 'No records matched your search:' in text:
            if page != 1:
                raise RuntimeError('FirstSearch 无结果，无法翻页')
            result = {'source': 'OCLC FirstSearch 浙大机构会话', 'database': database, 'library_info': INFO, 'query': q, 'page': 1, 'total_raw': 0, 'items': [], 'note': '源站报告无匹配；目录记录不代表浙大持有或全文可用。'}
            if field != 'keyword':
                result['field_requested'] = field
            return result
        match = re.search('Records found:\\s*([\\d,]+)', text)
        expected = DATABASES[database] + ' List of Records'
        if not match or expected not in text:
            raise RuntimeError('FirstSearch 未返回可确认的所选数据库结果')
        total = int(match.group(1).replace(',', ''))
        for _ in range(1, page):
            icon = b.find('img', alt='Next page of results')
            anchor = icon.find_parent('a') if icon else None
            if not anchor:
                raise RuntimeError('FirstSearch 没有下一页')
            target = _safe(r.url, anchor.get('href'), '/WebZ/FSFETCH')
            r = s.get(target, timeout=25)
            r.raise_for_status()
            b, text = _page(r.text)
            if expected not in text:
                raise RuntimeError('FirstSearch 翻页未返回所选数据库目录')
            current = re.search('Records found:\\s*([\\d,]+)', text)
            if not current or int(current.group(1).replace(',', '')) != total:
                raise RuntimeError('FirstSearch 翻页总数不一致')
        boxes = b.select('input[name^="BookMark_"]')
        if len(boxes) != min(10, max(0, total - (page - 1) * 10)) or not boxes:
            raise RuntimeError('FirstSearch 结果条数异常')
        items = []
        for i, box in enumerate(boxes):
            label = box.get('aria-label', '')
            m = re.fullmatch('Select Record (\\d+)', label)
            if not m or int(m.group(1)) != (page - 1) * 10 + i + 1:
                raise RuntimeError('FirstSearch 记录序号与页码不符')
            tr = box.find_parent('tr')
            tds = tr.find_all('td', recursive=False) if tr else []
            cell = tds[-1] if len(tds) >= 2 else None
            a = cell.select_one('a b') if cell else None
            if not a:
                raise RuntimeError('FirstSearch 题录缺少题名')
            title = a.get_text(' ', strip=True)
            raw = cell.get_text(' ', strip=True).split('More Like This:', 1)[0].strip()
            if not title or not raw:
                raise RuntimeError('FirstSearch 题录为空')
            items.append({'record_number': int(m.group(1)), 'title_raw': title, 'record_text_raw': raw})
    except requests.RequestException as e:
        raise RuntimeError('FirstSearch 网络请求失败：' + type(e).__name__) from None
    result = {'source': 'OCLC FirstSearch 浙大机构会话', 'database': database, 'library_info': INFO, 'query': q, 'page': page, 'total_raw': total, 'items': items, 'note': '一次新建浙大 IP 会话，所选子库结果按源站页面返回；WorldCat 为全球联合目录，每页至多 10 条，逐页核对序号。源站可能将关键词拆分成多个词；馆藏地、学校持有、电子全文和下载权限需逐条核实。最多查询前 10 页，顺序翻页导致请求次数随页数增加；仅 WorldCat 第 6、10 页实测，其他子库深页未逐项验证；不输出带会话标识的链接。'}
    if field != 'keyword':
        result['field_requested'] = field
        result['note'] += ' 按站方高级字段查询；词语可能分词或关联其他版本，非精确匹配。主题标引依子库而异。'
    return result
