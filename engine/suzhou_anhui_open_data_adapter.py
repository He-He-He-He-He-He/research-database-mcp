"""宿州市公共数据开放平台：目录检索及无条件开放 Excel 网页预览。"""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.ahsz.gov.cn'
ID = re.compile('[0-9a-f]{32}')

def _page(path, params=None):
    r = requests.get(urljoin(BASE, path), params=params, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect or 'text/html' not in r.headers.get('Content-Type', '').lower():
        raise RuntimeError('平台未返回预期网页')
    return BeautifulSoup(r.content, 'html.parser')

def search(keyword='', page=1):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词不能超过100字')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    s = _page('/oportal/catalog/index', {'Q': keyword, 'page': page})
    items = []
    for a in s.select('.cata-title > a[href]'):
        match = re.fullmatch('/oportal/catalog/([0-9a-f]{32})', a['href'])
        if not match:
            continue
        card = a.find_parent('li')
        text = card.get_text(' ', strip=True)
        fields = {}
        for el in card.select('.cata-information .information'):
            spans = el.select('span')
            if len(spans) >= 2:
                fields[spans[0].get_text(strip=True).rstrip('：:')] = spans[1].get_text(' ', strip=True)
        items.append({'id': match.group(1), 'title': a.get_text(' ', strip=True), 'url': urljoin(BASE, a['href']), 'metadata': fields, 'open_condition': '无条件' if re.search('开放条件：\\s*无条件', text) else '有条件' if re.search('开放条件：\\s*有条件', text) else None})
    return {'source': '宿州市公共数据开放平台', 'keyword': keyword, 'page': page, 'items': items, 'note': '检索返回官网当前页目录，包含有条件开放资源；目录不等于可读取数据。目录更新时间不一定等于数据所属时期。'}

def preview(catalog_id):
    if not isinstance(catalog_id, str) or not ID.fullmatch(catalog_id):
        raise ValueError('目录 ID 无效')
    detail = _page('/oportal/catalog/' + catalog_id)
    raw = detail.get_text(' ', strip=True)
    if not re.search('开放类型：\\s*无条件开放', raw):
        raise ValueError('目录未确认为无条件开放，不能调用预览')
    links = detail.select('a[href^="/oportal/catalog/viewExcel?"]')
    if not links:
        raise ValueError('该目录未提供 Excel 网页预览')
    href = links[0].get('href', '')
    if not href.startswith('/oportal/catalog/viewExcel?'):
        raise RuntimeError('预览链接异常')
    page = _page(href)
    table = page.find('table')
    if not table:
        raise RuntimeError('官网预览未返回表格，可能需要登录或服务暂不可用')
    rows = [[cell.get_text(' ', strip=True) for cell in tr.find_all(['th', 'td'], recursive=False)] for tr in table.find_all('tr')]
    rows = [x for x in rows if x]
    if not rows:
        raise RuntimeError('官网预览表为空')
    title = detail.find('title')
    return {'source': '宿州市公共数据开放平台', 'catalog_id': catalog_id, 'catalog_url': BASE + '/oportal/catalog/' + catalog_id, 'title': title.get_text(' ', strip=True) if title else None, 'open_condition': '无条件开放', 'preview_url': urljoin(BASE, href), 'rows': rows, 'note': '这是官网 Excel 网页预览，保留原值、字段、单位与 null；预览可能不完整或存在原始数据差异，应核对原文、统计口径及数据时期。按平台许可注明来源。'}
