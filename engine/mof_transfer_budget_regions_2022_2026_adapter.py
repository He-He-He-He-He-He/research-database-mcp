"""财政部中央预算转移支付分地区汇总原表，2022–2026预算版。"""
import release_runtime
import re
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
KINDS = {'public': '一般公共预算', 'general': '一般性', 'joint': '共同财政事权', 'special': '专项', 'fund': '政府性基金', 'capital': '国有资本经营'}

def catalog(year):
    if isinstance(year, bool) or year not in range(2022, 2027):
        raise ValueError('预算版次须为2022—2026')
    url = f'https://yss.mof.gov.cn/{year}zyczys/'
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    items = []
    for a in s.select('a[href]'):
        title = ''.join(a.get_text().split())
        href = a['href'].strip()
        if not title.startswith(str(year) + '年') or not title.endswith('转移支付分地区情况汇总表'):
            continue
        matches = [k for k, v in KINDS.items() if v + '转移支付分地区情况汇总表' in title]
        if len(matches) != 1 or not re.fullmatch('\\./\\d{6}/t\\d{8}_\\d+\\.htm', href):
            continue
        items.append({'kind': matches[0], 'title': title, 'url': urljoin(url, href)})
    if set((x['kind'] for x in items)) != set(KINDS) or len(items) != len(KINDS):
        raise ValueError('官方目录表项不完整或发生变化')
    return {'source': '财政部中央财政预算', 'year': year, 'catalog_url': url, 'items': items}

def table(year, kind='public', region=''):
    if kind not in KINDS:
        raise ValueError('未知转移支付类型')
    if not isinstance(region, str) or len(region) > 80:
        raise ValueError('地区筛选不合法')
    item = next((x for x in catalog(year)['items'] if x['kind'] == kind))
    r = requests.get(item['url'], timeout=30)
    r.raise_for_status()
    s = BeautifulSoup(r.content, 'html.parser')
    tables = []
    for t in s.select('table'):
        rows = []
        for tr in t.select('tr'):
            cells = [{'text': ' '.join(c.get_text(' ', strip=True).split()), 'rowspan': int(c.get('rowspan', 1)), 'colspan': int(c.get('colspan', 1))} for c in tr.find_all(['td', 'th'], recursive=False)]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    if len(tables) != 1:
        raise ValueError('官方页面表格数量变化')
    allrows = tables[0]
    q = ''.join(region.split())
    matched = [{'row': i, 'cells': row} for i, row in enumerate(allrows, 1) if q and q in ''.join((''.join(c['text'].split()) for c in row))]
    return {'source': '财政部中央财政预算分地区汇总表', 'year': year, 'kind': kind, 'title': item['title'], 'source_url': item['url'], 'unit': '亿元', 'headers': allrows[:4], 'rows': matched if region else [{'row': i, 'cells': row} for i, row in enumerate(allrows, 1)], 'note': '原表保留预算数、上年预算/执行数等不同列；不能把预算数当决算。省级总额、其不含计划单列市部分及单列市行有包含关系，不能相加；空白不视为零。各类型存在包含关系。'}
