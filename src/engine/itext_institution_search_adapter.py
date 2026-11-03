"""爱教材浙大 IP 通用书目查询，不读取书籍或链接中的会话参数。"""
import release_runtime
import json
import re
from urllib.parse import urlsplit, parse_qs
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.itextbook.cn/'

def search(keyword, page=1, limit=10, session=None, field='all', year=None):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or re.search('[\\x00-\\x1f`~!@#$%^&*_+=<>?"{}|/;\\\\\\[\\]·！￥%……&*（）()。——+={}|《》？“”【】‘]', keyword):
        raise ValueError('关键词须为 1–100 字且符合站方普通搜索规则')
    if type(page) is not int or not 1 <= page <= 1000:
        raise ValueError('page 须为 1–1000')
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError('limit 须为 1–10')
    fields = {'all': '10', 'title': '20', 'author': '30', 'publisher': '40', 'isbn': '70', 'subject': '65', 'year': '50'}
    if field not in fields:
        raise ValueError('field 须为 all、title、author、publisher、isbn、subject 或 year')
    if field == 'year' and (not re.fullmatch('[1-9][0-9]{3}', keyword.strip())):
        raise ValueError('出版年份须为四位数字')
    q = keyword.strip()
    s = session or requests.Session()
    body = {'oneSearch': [{'fieldType': fields[field], 'relationshipType': 10, 'fieldVal': q, 'vague': 0}], 'pageNo': str(page), 'pageSize': '10'}
    if year is not None:
        if field not in ('all', 'author') or type(year) is not int or (not 1000 <= year <= 9999):
            raise ValueError('组合年份须为四位数字，且仅支持 all 或 author')
        body['oneSearch'].append({'fieldType': '50', 'relationshipType': 10, 'fieldVal': str(year), 'vague': 0})
    try:
        r = s.post(BASE + 'f/book/retrieveInfo', data={'paramJson': json.dumps(body, ensure_ascii=False)}, timeout=30, allow_redirects=False)
        if r.status_code != 200:
            raise RuntimeError('书目搜索服务不可用')
        p = BeautifulSoup(r.content, 'html.parser')
        text = p.get_text(' ', strip=True)
        if not re.search('浙江大学\\s*IP\\s*(?:Reader|读者)', text, re.I):
            raise RuntimeError('未确认浙江大学 IP 读者')
        queries = p.select('input[name=plist]')
        pg = p.select_one('input[name=pageNo]')
        nav = p.select_one('div.page')
        if len(queries) != (2 if year is not None else 1) or queries[0].get('fieldval') != q or queries[0].get('fieldtype') != fields[field] or (not pg) or (pg.get('value') != str(page)):
            raise RuntimeError('查询词或页码未确认')
        if year is not None and (queries[1].get('fieldtype') != '50' or queries[1].get('fieldval') != str(year) or any((x.get('relationshiptype') != '10' for x in queries))):
            raise RuntimeError('组合年份或关系未确认')
        m = re.search('(?:total\\s*:|总计[：:])\\s*([\\d,]+)', nav.get_text(' ', strip=True), re.I) if nav else None
        if not m:
            raise RuntimeError('站方总数未识别')
        total = int(m.group(1).replace(',', ''))
        cards = p.select('.book-info')
        expected = min(10, max(0, total - (page - 1) * 10))
        if len(cards) != expected:
            raise RuntimeError('站方书目数量与当前页不一致')
        items = []
        for x in cards[:limit]:
            a = x.select_one('p.title a')
            u = urlsplit(a.get('href', '')) if a else None
            if not a or u.path != '/f/book/bookDetail' or u.netloc not in ('', 'www.itextbook.cn'):
                raise RuntimeError('题录链接异常')
            ids = parse_qs(u.query).get('bookId', [])
            if len(ids) != 1 or not re.fullmatch('[A-Za-z0-9]{32}', ids[0]):
                raise RuntimeError('书目编号异常')
            title = a.get_text(' ', strip=True)
            author = x.select_one('.start-group')
            if not title:
                raise RuntimeError('书名缺失')
            items.append({'book_id': ids[0], 'title': title, 'author_raw': author.get_text(' ', strip=True) if author else None, 'other_lines_raw': [v.get_text(' ', strip=True) for v in x.select('p.text')]})
        result = {'source': '爱教材普通书目搜索', 'institution': '浙江大学 IP Reader', 'query': q, 'page': page, 'source_page_size': 10, 'total_raw': total, 'source_page_items': len(cards), 'page_truncated': len(items) < len(cards), 'items': items, 'note': '站方通用搜索未限定学校已购，身份标识不证明逐书全文权限。源页最多 10 条；本地截断时下一页不会补齐，请取完整源页。未输出链接或会话参数。'}
        if field != 'all':
            result['field_requested'] = field
            result['note'] += ' 源站已回显所选字段；匹配方式和逐书授权仍需核对。'
        if year is not None:
            result['year_requested'] = year
            result['note'] += ' 站方回显与年份且关系，已验通用字段和作者字段；字段匹配与逐书权限须核对。'
        return result
    except requests.RequestException:
        raise RuntimeError('爱教材连接失败') from None
