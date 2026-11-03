"""国家统计局中国创新指数报告原表和方法说明。"""
import release_runtime
import argparse
import json
import requests
from bs4 import BeautifulSoup
from moe_education_statistics_adapters import _LeafTables
URLS = {2025: 'https://www.stats.gov.cn/sj/zxfb/202610/t20261023_1965677.html', 2024: 'https://www.stats.gov.cn/sj/zxfb/202510/t20251029_1961727.html', 2023: 'https://www.stats.gov.cn/sj/zxfb/202410/t20241025_1957132.html', 2022: 'https://www.stats.gov.cn/sj/zxfb/202310/t20231020_1943765.html', 2021: 'https://www.stats.gov.cn/sj/zxfb/202302/t20230203_1901640.html'}

def report(year, keyword=''):
    if year not in URLS:
        raise ValueError('仅支持已验证的 2021—2025 年')
    u = URLS[year]
    r = requests.get(u, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if not r.url.startswith('https://www.stats.gov.cn/sj/zxfb/'):
        raise ValueError('非官方 HTTPS 跳转')
    r.encoding = 'utf8'
    html = r.text
    if f'{year}年中国创新指数' not in html:
        raise ValueError('未核对到报告名称')
    p = _LeafTables()
    p.feed(html)
    tables = p.tables
    if len(tables) % 2 == 0 and tables[:len(tables) // 2] == tables[len(tables) // 2:]:
        tables = tables[:len(tables) // 2]
    if len(tables) != (6 if year == 2022 else 2):
        raise ValueError('上游表结构变化')
    output = []
    for t in tables:
        if keyword:
            matched = [row for row in t if keyword in ''.join((c['text'] for c in row))]
            output.append({'header_rows': t[:2], 'rows': matched})
        else:
            output.append({'rows': t})
    s = BeautifulSoup(html, 'html.parser')
    body = s.select_one('.txt-content')
    return {'report_year': year, 'source_url': u, 'tables': output, 'report_text': body.get_text('\n', strip=True) if body else None, 'note': '筛选为报告内表格行；不同版本和基期不可直接拼接。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(URLS))
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(report(a.year, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
