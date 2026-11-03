"""Numdam 法国数学数字图书馆公开题录搜索。"""
import release_runtime
import re
from urllib.parse import quote, urljoin, urlsplit
import requests
from bs4 import BeautifulSoup
BASE = 'https://www.numdam.org'

def search(keyword, page=1, limit=20):
    if not isinstance(keyword, str) or not re.fullmatch('[A-Za-z0-9]+(?: [A-Za-z0-9]+)*', keyword) or len(keyword) > 100:
        raise ValueError('目前只支持不超过 100 字的英文字母数字单词及单个空格')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('每页最多返回 20 条')
    url = BASE + '/search?' + quote(keyword, safe='') + '-' + str(page) + '-qt'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    h = BeautifulSoup(r.text, 'html.parser')
    field = h.select_one('input[name=q0]')
    if not field or field.get('value') != keyword:
        raise RuntimeError('Numdam 未回显查询词')
    counts = []
    for z in h.select('h4'):
        m = re.fullmatch('\\s*(\\d+)\\s+résultats?\\s*', z.get_text(' ', strip=True), re.I)
        if m:
            counts.append(int(m.group(1)))
    if len(counts) != 1:
        raise RuntimeError('未确认 Numdam 结果总数')
    total = counts[0]
    active = [x.get_text(' ', strip=True) for x in h.select('.pagination .active')]
    if total and (not active or any((x != str(page) for x in active))):
        raise RuntimeError('Numdam 回显页码异常')
    items = []
    for a in h.select('a[href]'):
        title = a.select_one('.article-title')
        if not title:
            continue
        u = urljoin(BASE, a['href'])
        parsed = urlsplit(u)
        if parsed.scheme != 'https' or parsed.hostname != 'www.numdam.org' or (not parsed.path.startswith(('/item/', '/articles/'))):
            raise RuntimeError('异常题录链接')
        container = a.find_parent('div', class_='col-12')
        paragraphs = container.find_all('p', recursive=False) if container else []
        if len(paragraphs) < 2:
            raise RuntimeError('题录作者及出处缺失')
        items.append({'title': title.get_text(' ', strip=True), 'authors_raw': paragraphs[0].get_text(' ', strip=True), 'citation_raw': paragraphs[1].get_text(' ', strip=True), 'url': u})
    if len(items) > 20 or (total == 0 and items) or (total > 0 and (not items)):
        raise RuntimeError('Numdam 题录与总数不一致')
    return {'source': 'Numdam 法国数学数字图书馆', 'query': keyword, 'page': page, 'total': total, 'source_page_items': len(items), 'truncated': len(items) > limit, 'items': items[:limit], 'note': '公开平台搜索涵盖全文等多个字段，包含 SMF 历史期刊及其他出版社，不等于浙大 SMF 订购范围；仅题录，全文及逐项许可未核验；limit只截取原站当前页，若truncated为true，翻到下一源页会遗漏余项，请用limit=20取整页。'}
