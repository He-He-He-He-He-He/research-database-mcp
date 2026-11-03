"""国家统计局全国科技经费投入公报的行业与地区原表。"""
import release_runtime
import argparse
import json
import requests
from bs4 import BeautifulSoup
from moe_education_statistics_adapters import _LeafTables
URLS = {2025: 'https://www.stats.gov.cn/sj/zxfb/202610/t20261016_1965512.html', 2024: 'https://www.stats.gov.cn/sj/zxfb/202509/t20250929_1961429.html', 2023: 'https://www.stats.gov.cn/sj/zxfb/202410/t20241002_1956810.html'}

def report(year, keyword=''):
    if year not in URLS:
        raise ValueError('仅支持已核验的 2023、2024、2025 年')
    url = URLS[year]
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if not r.url.startswith('https://www.stats.gov.cn/sj/zxfb/'):
        raise ValueError('非国家统计局 HTTPS 跳转')
    r.encoding = 'utf8'
    html = r.text
    if f'{year}年全国科技经费投入统计公报' not in html:
        raise ValueError('未找到目标报告标题')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) % 2 == 0 and tables[:len(tables) // 2] == tables[len(tables) // 2:]:
        tables = tables[:len(tables) // 2]
    expected = 3 if year in (2024, 2025) else 2
    if len(tables) != expected:
        raise ValueError('原表数量变化')
    result = []
    for t in tables:
        header = t[0]
        body = t[1:]
        matched = [row for row in body if ''.join(keyword.split()) in ''.join((''.join(c['text'].split()) for c in row))] if keyword else body
        result.append({'header': header, 'rows': matched})
    s = BeautifulSoup(html, 'html.parser')
    body = s.select_one('.txt-content')
    return {'year': year, 'source_url': url, 'tables': result, 'report_text': body.get_text('\n', strip=True) if body else None, 'note': '筛选仅限表格行；报告文字含完整方法和注释。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(URLS))
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
