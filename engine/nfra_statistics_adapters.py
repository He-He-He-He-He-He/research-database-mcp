"""国家金融监督管理总局统计栏目近期目录及正文，只读公开数据。"""
import release_runtime
import re
from urllib.parse import urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.nfra.gov.cn'
STATIC = BASE + '/cn/static/data/DocInfo/'

def _json(url):
    response = requests.get(url, timeout=25, allow_redirects=False)
    response.raise_for_status()
    if response.is_redirect or len(response.content) > 8000000:
        raise ValueError('响应重定向或过大')
    value = response.json()
    if value.get('rptCode') != 200 or value.get('data') is None:
        raise ValueError('监管总局返回异常或数据为空')
    return value['data']

def _safe_url(value):
    if not isinstance(value, str) or not value.strip():
        return None
    url = urljoin(BASE, value.strip())
    p = urlsplit(url)
    return url if p.scheme == 'https' and p.hostname == 'www.nfra.gov.cn' else None

def catalog(page=1, keyword=''):
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 10000):
        raise ValueError('页码必须在 1–10000 之间')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词过长')
    if page <= 3:
        url = STATIC + f'SelectDocByItemIdAndChild/data_itemId=954,pageIndex={page},pageSize=18.json'
    else:
        url = BASE + f'/cbircweb/DocInfo/SelectDocByItemIdAndChild?itemId=954&pageIndex={page}&pageSize=18'
    data = _json(url)
    rows = []
    for row in data.get('rows', []):
        title = row.get('docTitle') or row.get('docSubtitle') or ''
        if keyword not in title:
            continue
        doc_id = row.get('docId')
        if not isinstance(doc_id, int):
            continue
        rows.append({'doc_id': doc_id, 'title': title, 'published': row.get('publishDate'), 'page_url': f'{BASE}/cn/view/pages/ItemDetail.html?docId={doc_id}&itemId=954', 'pdf_url': _safe_url(row.get('pdfFileUrl')), 'doc_url': _safe_url(row.get('docFileUrl'))})
    return {'source': '国家金融监督管理总局统计信息栏目', 'page': page, 'keyword': keyword, 'reported_total': data.get('total'), 'items': rows, 'note': '关键词仅筛选本页；总数由上游提供，超过最后页时上游可能返回 0。分页可随更新变化，不代表已检索全目录。'}

def search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词须为不超过 200 字符的字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 10000 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–10000 的整数，最多查询连续 20 页')
    items = []
    seen = set()
    total = None
    for page in range(start_page, end_page + 1):
        result = catalog(page, keyword)
        current = result['reported_total']
        if not isinstance(current, int) or isinstance(current, bool) or current < 0:
            raise ValueError('上游总数无效')
        if total is None:
            total = current
        elif total != current:
            raise ValueError('跨页总数变化，或超出末页；请重新查询')
        for item in result['items']:
            if item['doc_id'] in seen:
                raise ValueError('跨页出现重复编号，目录可能已更新；请重新查询')
            seen.add(item['doc_id'])
            items.append(item)
    return {'source': '国家金融监督管理总局统计信息栏目', 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'upstream_total': total, 'matched_count': len(items), 'items': items, 'note': '仅筛选指定页标题；上游总数不是匹配总数。目录动态变化，跨页并非原子快照，不代表完整历史；数据单位及口径应核对原件。'}

def detail(doc_id):
    if isinstance(doc_id, bool) or not isinstance(doc_id, int) or (not 1 <= doc_id <= 99999999):
        raise ValueError('doc_id 应为正整数')
    data = _json(STATIC + f'SelectByDocId/data_docId={doc_id}.json')
    if data.get('docId') != doc_id:
        raise ValueError('返回文档编号不符')
    soup = BeautifulSoup(data.get('docClob') or '', 'html.parser')
    for element in soup.select('script,style,head'):
        element.decompose()
    paragraphs = []
    for p in soup.select('p'):
        text = re.sub('\\s+', '', p.get_text('', strip=True))
        if text and (not paragraphs or text != paragraphs[-1]):
            paragraphs.append(text)
    images = [u for image in soup.select('img[src]') if (u := _safe_url(image.get('src')))]
    links = []
    for a in soup.select('a[href]'):
        u = _safe_url(a.get('href'))
        if u:
            links.append({'title': a.get_text(' ', strip=True), 'url': u})
    return {'source': '国家金融监督管理总局', 'doc_id': doc_id, 'title': data.get('docTitle'), 'published': data.get('publishDate'), 'publisher': data.get('docSource'), 'page_url': f'{BASE}/cn/view/pages/ItemDetail.html?docId={doc_id}&itemId=954', 'paragraphs': paragraphs, 'images': images, 'links': links, 'pdf_url': _safe_url(data.get('pdfFileUrl')), 'doc_url': _safe_url(data.get('docFileUrl')), 'note': '返回可提取原文与官方图片/文件链接；图片表格未做识别，空文本不代表无数据。请核对原文中的统计口径。'}
