"""国家统计局流通领域重要生产资料旬度市场价格原表。"""
import release_runtime
import argparse
import json
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
ROOT = 'https://www.stats.gov.cn'
BASE = ROOT + '/sj/zxfb/'
PATH = re.compile('^/sj/zxfb/\\d{6}/t\\d{8}_\\d+\\.html$')

def get(url):
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    p = urlparse(r.url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn':
        raise ValueError('跳转到非统计局 HTTPS')
    r.encoding = r.apparent_encoding
    return BeautifulSoup(r.text, 'html.parser')

def listing(page=1):
    if page < 1 or page > 999:
        raise ValueError('页码超出范围')
    url = BASE + ('index.html' if page == 1 else f'index_{page - 1}.html')
    s = get(url)
    items = []
    seen = set()
    source_items = 0
    for a in s.select('a[title][href]'):
        title = a['title']
        link = urljoin(url, a['href'])
        p = urlparse(link)
        if p.scheme == 'https' and p.hostname == 'www.stats.gov.cn' and PATH.fullmatch(p.path):
            source_items += 1
        if '流通领域重要生产资料市场价格变动情况' not in title or p.hostname != 'www.stats.gov.cn' or (not PATH.fullmatch(p.path)) or (link in seen):
            continue
        seen.add(link)
        items.append({'title': title, 'url': link})
    if not source_items:
        raise ValueError('未识别统计局发布目录，可能超出页数或网站变化；不能认定无匹配')
    return {'source_url': url, 'page': page, 'scope': '统计局综合数据发布目录当前页中的匹配报告', 'items': items}

def search_pages(keyword='', start_page=1, end_page=3):
    if not isinstance(keyword, str):
        raise ValueError('关键词须为字符串')
    if any((not isinstance(x, int) or isinstance(x, bool) for x in (start_page, end_page))) or not 1 <= start_page <= end_page <= 999 or end_page - start_page >= 20:
        raise ValueError('起止页须为 1–999 的整数，最多查询连续 20 页')
    items = []
    sources = []
    seen = set()
    for page in range(start_page, end_page + 1):
        result = listing(page)
        sources.append(result['source_url'])
        for item in result['items']:
            if item['url'] in seen:
                raise ValueError('跨页出现重复链接，目录可能已更新；请重新查询')
            seen.add(item['url'])
            if keyword in item['title']:
                items.append(item)
    return {'source': '国家统计局', 'keyword': keyword, 'start_page': start_page, 'end_page': end_page, 'source_urls': sources, 'matched_count': len(items), 'items': items, 'scope': '仅筛选指定页中的旬度价格报告标题；目录动态变化，跨页非原子快照，不代表全部历史。价格及涨跌幅应核对报告原表与单位。'}

def detail(url, keyword=''):
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname != 'www.stats.gov.cn' or (not PATH.fullmatch(p.path)) or p.query or p.fragment:
        raise ValueError('仅接受统计局数据发布正文 HTTPS 地址')
    s = get(url)
    h = s.select_one('h1')
    title = h.get_text(' ', strip=True) if h else ''
    if not title:
        meta = s.select_one('meta[name=ArticleTitle]')
        title = meta.get('content', '') if meta else ''
    if '流通领域重要生产资料市场价格变动情况' not in title:
        raise ValueError('并非目标报告')
    tables = s.select('.txt-content table')
    if not tables:
        raise ValueError('未找到市场价格表')
    rows = []
    category = None
    header = []
    notes = []
    for tr in tables[0].find_all('tr'):
        cells = [' '.join(c.get_text(' ', strip=True).split()) for c in tr.find_all(['td', 'th'], recursive=False)]
        if not cells:
            continue
        if len(cells) == 1:
            value = cells[0]
            if value.startswith('注'):
                notes.append(value)
            elif value:
                category = value
        elif len(cells) >= 5 and cells[0] and (not any(cells[1:])):
            category = cells[0]
        elif '产品名称' in cells[0]:
            header = cells
        elif len(cells) >= 5 and cells[0]:
            rows.append({'category': category, 'product': cells[0], 'unit': cells[1], 'current_price_yuan': cells[2], 'change_yuan': cells[3], 'change_pct': cells[4]})
    if not header or not rows:
        raise ValueError('价格表结构变化')
    return {'source_url': url, 'title': title, 'header': header, 'note_rows': notes, 'total_products': len(rows), 'filter_scope': '产品名或分类', 'items': [x for x in rows if keyword in x['product'] or keyword in (x['category'] or '')]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    l = sub.add_parser('list')
    l.add_argument('--page', type=int, default=1)
    l = sub.add_parser('search-pages')
    l.add_argument('--keyword', default='')
    l.add_argument('--start-page', type=int, default=1)
    l.add_argument('--end-page', type=int, default=3)
    d = sub.add_parser('detail')
    d.add_argument('url')
    d.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(listing(a.page) if a.command == 'list' else search_pages(a.keyword, a.start_page, a.end_page) if a.command == 'search-pages' else detail(a.url, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
