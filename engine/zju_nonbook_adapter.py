"""浙大非书资料系统的分类首页；仅公开题录，非全库关键词搜索。"""
import release_runtime
import re
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
BASE = 'http://210.32.137.198/'
CATEGORIES = 'ABCDEFGH IJK NOPQRSTUVXZ'.replace(' ', '')

def category_page(category: str, keyword: str='', page: int=1) -> dict:
    category = category.strip().upper()
    if category not in CATEGORIES or len(category) != 1:
        raise ValueError('分类须为有效的单个中图法字母')
    if len(keyword) > 200:
        raise ValueError('关键词不超过 200 字')
    if type(page) is not int or not 1 <= page <= 5000:
        raise ValueError('页码须为 1–5000')
    response = requests.get(urljoin(BASE, 'chinaclass.do'), params={'status': 'show', 'CValue': category}, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')

    def page_state(doc):
        text = doc.get_text(' ', strip=True)
        m = re.search('总共\\s*(\\d+)\\s*页\\s*当前第\\s*(\\d+)\\s*页', text)
        if not m:
            raise RuntimeError('分类页未显示可核验的页码')
        return (int(m.group(1)), int(m.group(2)))
    total_pages, current_page = page_state(soup)
    if current_page != 1:
        raise RuntimeError('分类首页页码异常')
    if page > total_pages:
        raise ValueError('页码超过该分类的总页数')
    count_raw = None
    next_link = next((a for a in soup.select('a[href]') if a.get_text(' ', strip=True) == '下一页'), None)
    if next_link:
        target = urlparse(urljoin(BASE, next_link['href']))
        params = parse_qs(target.query)
        if target.scheme != 'http' or target.hostname != '210.32.137.198' or target.path != '/chinaclass.do' or (len(params.get('Count', [])) != 1) or (not params['Count'][0].isdigit()) or (params.get('CValue', [''])[0].upper() != category):
            raise RuntimeError('分类下一页链接结构异常')
        count_raw = params['Count'][0]
    if page > 1:
        if count_raw is None:
            raise RuntimeError('分类分页参数缺失')
        response = requests.get(urljoin(BASE, 'chinaclass.do'), params={'status': 'show', 'CValue': category, 'Count': count_raw, 'PageCount': page}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        actual_total, current_page = page_state(soup)
        if current_page != page or actual_total != total_pages:
            raise RuntimeError('分类页码或总页数与请求不一致')
    items = []
    seen = 0
    for a in soup.select('a[href*="METAID="]'):
        row = a.find_parent('tr')
        if not row:
            continue
        cells = row.find_all('td', recursive=False)
        if len(cells) != 4:
            continue
        number = cells[0].get_text(' ', strip=True)
        if not number.isdigit() or int(number) != (page - 1) * 30 + seen + 1:
            raise RuntimeError('分类结果序号与页码不一致')
        seen += 1
        title = a.get('title') or a.get_text(' ', strip=True)
        author = cells[2].get_text(' ', strip=True)
        publisher = cells[3].get_text(' ', strip=True)
        if keyword and keyword.casefold() not in ' '.join((title, author, publisher)).casefold():
            continue
        items.append({'title': title.strip(), 'author': author, 'publisher': publisher, 'url': urljoin(BASE, a['href'])})
    if not soup.find(string=lambda s: s and '中图法分类' in s):
        raise RuntimeError('分类页面结构异常，无法确认结果')
    return {'source': '浙江大学非书资料（随书光盘）系统', 'category': category, 'page': page, 'total_pages_raw': total_pages, 'total_count_raw': count_raw, 'page_records_seen': seen, 'keyword': keyword, 'scope': '仅在指定分类当前页最多 30 条中筛选，非全库检索', 'transport': 'HTTP 明文，不要输入敏感信息', 'items': items}

def record_detail(record_id: int) -> dict:
    """读取单条书目描述，不探测、下载附带资源。"""
    if isinstance(record_id, bool) or not isinstance(record_id, int) or (not 1 <= record_id <= 2147483647):
        raise ValueError('记录编号必须是正整数')
    response = requests.get(urljoin(BASE, 'showpage.do'), params={'status': 'show', 'METAID': record_id}, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    fields = {}
    allowed = {'ISBN', '单价', '语种', '书名', '作者', '版次', '出版社', '出版日期', '从编', '文摘', '关键字', '分类号'}
    for paragraph in soup.find_all('p'):
        value = ' '.join(paragraph.get_text(' ', strip=True).split())
        if '：' not in value:
            continue
        key, value = value.split('：', 1)
        if key in allowed and value:
            fields.setdefault(key, []).append(value)
    if not fields.get('书名'):
        raise ValueError('未找到书目或上游返回异常页面')
    return {'source': '浙江大学非书资料（随书光盘）系统', 'record_id': record_id, 'url': response.url, 'fields': fields, 'scope': '书目描述；不代表附件可用或具有下载权限', 'transport': 'HTTP 明文'}
