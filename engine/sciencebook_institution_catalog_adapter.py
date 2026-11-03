"""Science Reading campus-IP book metadata first page."""
import release_runtime
import re
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
BASE = 'https://book.sciencereading.cn/'

def search(keyword, limit=5, session=None, page=1, sort='default', year=None, subject_code=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100:
        raise ValueError('关键词须为 1–100 字')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 10):
        raise ValueError('首屏最多 10 条')
    if type(page) is not int or not 1 <= page <= 5000:
        raise ValueError('页码须为 1–5000')
    sorts = {'default': None, 'date-desc': 'booksimple.publishDate desc', 'date-asc': 'booksimple.publishDate', 'title': 'booksimple.name', 'author': 'booksimple.author'}
    if sort not in sorts:
        raise ValueError('sort 须为 default、date-desc、date-asc、title 或 author')
    if year is not None and (type(year) is not int or not 1000 <= year <= 9999):
        raise ValueError('年份须为 1000–9999 的整数')
    if subject_code is not None and (not isinstance(subject_code, str) or not re.fullmatch('[0-9]{1,10}', subject_code)):
        raise ValueError('学科代码须为 1–10 位数字')
    q = keyword.strip()
    s = session or requests.Session()
    r = s.get(BASE + 'shop/main/Login/shopFrame.do', timeout=25)
    r.raise_for_status()
    r = s.post(BASE + 'shop/main/Login/checkOrgNameByIp.do', timeout=20)
    r.raise_for_status()
    if r.text.strip() != '浙江大学':
        raise RuntimeError('未确认浙江大学 IP 机构身份')
    subject_label = None
    subject_count = None
    subject_facets = []
    if subject_code is not None:
        facet_payload = {'showQueryModel.nameIsbnAuthor': q, 'pageSplit.nowPageNumber': '1', 'pageSplit.showRow': '10'}
        if year is not None:
            facet_payload['showQueryModel.publishYear'] = str(year)
        r = s.post(BASE + 'shop/book/Booksimple/list.do', data=facet_payload, timeout=40)
        r.raise_for_status()
        facets = BeautifulSoup(r.content, 'html.parser')
        if not facets.select_one('#bookListForm') or q not in facets.get_text(' ', strip=True):
            raise RuntimeError('无法确认当前查询的学科分面')
        matches = [e for e in facets.select('input[name="book_xueke"]') if e.get('xueke') == subject_code]
        if len(matches) != 1:
            raise ValueError('学科代码不在当前查询的站方分面中')
        spans = matches[0].select('span') or matches[0].find_next_siblings('span', limit=2)
        if len(spans) < 2 or not re.fullmatch('\\(\\d+\\)', spans[1].get_text(strip=True)):
            raise RuntimeError('站方学科分面格式异常')
        subject_label = spans[0].get_text(' ', strip=True)
        subject_count = int(spans[1].get_text(strip=True)[1:-1])
    offset = (page - 1) * limit
    source_page = offset // 10 + 1
    index = offset % 10
    items = []
    total = None
    for source_index in (source_page, source_page + 1):
        if total is not None and (offset >= total or len(items) >= index + limit):
            break
        payload = {'showQueryModel.nameIsbnAuthor': q, 'pageSplit.nowPageNumber': str(source_index), 'pageSplit.showRow': '10'}
        if year is not None:
            payload['showQueryModel.publishYear'] = str(year)
        if subject_code is not None:
            payload['showQueryModel.dp3Value'] = "'" + subject_code + "'"
        if sorts[sort] is not None:
            payload['showQueryModel.bookOrderColumn'] = sorts[sort]
        r = s.post(BASE + 'shop/book/Booksimple/list.do', data=payload, timeout=40)
        r.raise_for_status()
        p = BeautifulSoup(r.content, 'html.parser')
        text = p.get_text(' ', strip=True)
        m = re.search('共计[：:]\\s*([\\d,]+)\\s*种图书', text)
        if subject_code is not None:
            echoed_subject = p.select_one('input[name="showQueryModel.dp3Value"]')
            if not echoed_subject or echoed_subject.get('value') != "'" + subject_code + "'":
                raise RuntimeError('源站未回显请求学科')
        if year is not None:
            echoed_year = p.select_one('input[name="showQueryModel.publishYear"]')
            if not echoed_year or echoed_year.get('value') != str(year):
                raise RuntimeError('源站未回显请求年份')
        if sorts[sort] is not None:
            selected_order = p.select_one('select[name="showQueryModel.bookOrderColumn"] option[selected]')
            if not selected_order or selected_order.get('value') != sorts[sort]:
                raise RuntimeError('源站未回显所请求排序')
        if not p.select_one('#bookListForm') or not m or q not in text:
            raise RuntimeError('检索页或总数未确认')
        if subject_code is None and (not subject_facets):
            for e in p.select('input[name="book_xueke"]'):
                code = e.get('xueke')
                spans = e.select('span') or e.find_next_siblings('span', limit=2)
                if code and re.fullmatch('[0-9]{1,10}', code) and (len(spans) >= 2) and re.fullmatch('\\(\\d+\\)', spans[1].get_text(strip=True)):
                    subject_facets.append({'code': code, 'label': spans[0].get_text(' ', strip=True), 'count': int(spans[1].get_text(strip=True)[1:-1])})
        current_total = int(m.group(1).replace(',', ''))
        if total is not None and current_total != total:
            raise RuntimeError('分页结果总数不一致')
        total = current_total
        if subject_code is not None and total != subject_count:
            raise RuntimeError('筛选总数与同次学科分面计数不一致')
        if offset >= total:
            break
        number = p.select_one('input[name="pageSplit.nowPageNumber"]')
        size = p.select_one('input[name="pageSplit.showRow"]')
        if not number or number.get('value') != str(source_index) or (not size) or (size.get('value') != '10'):
            raise RuntimeError('源站未确认请求页码或页长')
        anchors = p.select('.book_detail_title a[href]')
        if len(anchors) != min(10, max(0, total - (source_index - 1) * 10)):
            raise RuntimeError('源站题录数量不完整')
        for a in anchors:
            card = a.parent.parent.parent
            href = urljoin(BASE, a['href'])
            u = urlparse(href)
            ids = parse_qs(u.query).get('id', [])
            if u.scheme != 'https' or u.hostname != 'book.sciencereading.cn' or u.path != '/shop/book/Booksimple/show.do' or (len(ids) != 1) or (set(parse_qs(u.query)) != {'id'}):
                raise RuntimeError('题录链接异常')

            def field(label):
                for block in card.select('.book_detail_info .row > div'):
                    spans = block.select('span')
                    if spans and label in spans[0].get_text('', strip=True):
                        return spans[-1].get_text(' ', strip=True) or None
                return None
            items.append({'id': ids[0], 'title': a.get_text('', strip=True), 'author': field('作者'), 'isbn': field('ISBN'), 'publisher': field('出版社'), 'publish_date': field('出版日期'), 'url': href})
    selected = items[index:index + limit]
    if len(selected) != min(limit, max(0, total - offset)):
        raise RuntimeError('分页结果不完整')
    result = {'source': '科学文库', 'institution': '浙江大学', 'query': q, 'page': page, 'page_size': limit, 'total': total, 'items': selected, 'note': 'IP 机构识别后的全库图书目录；按请求页长连续返回，源站每页 10 条。未限定有全文权限，逐书全文未验证。'}
    if subject_code is None and subject_facets:
        result['subject_facets'] = subject_facets
    if subject_code is not None:
        result['subject_requested'] = {'code': subject_code, 'label': subject_label, 'facet_count': subject_count}
        result['note'] += ' 学科分面计数与筛选总数已核对，逐条学科归类未验证。'
    if year is not None:
        result['year_requested'] = year
        result['note'] += ' 站方回显出版年份，已抽验样本；逐书权限未验证。'
    if sort != 'default':
        result['sort_requested'] = sort
        result['note'] += ' 排序按站方规则；缺失日期、同月记录顺序及书名与作者排序规则未核，跨请求目录可能变化。'
    return result
