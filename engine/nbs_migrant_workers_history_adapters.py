"""国家统计局 2023—2024 年农民工监测调查报告原表。"""
import release_runtime
import argparse
import json
import requests
from bs4 import BeautifulSoup
from moe_education_statistics_adapters import _LeafTables
URLS = {2023: 'https://www.stats.gov.cn/sj/zxfb/202404/t20240430_1948783.html', 2024: 'https://www.stats.gov.cn/sj/zxfb/202504/t20250430_1959523.html'}
TITLES = ['外出农民工地区分布及构成', '农民工输出和输入地区分布', '农民工年龄构成', '农民工就业行业分布情况', '分行业农民工月均收入及增速']

def report(year, table=0):
    if year not in URLS:
        raise ValueError('仅支持 2023 和 2024 年，2025 年请使用现有适配器')
    if table not in range(6):
        raise ValueError('table 为 0（全部）或 1—5')
    url = URLS[year]
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if not r.url.startswith('https://www.stats.gov.cn/sj/zxfb/'):
        raise ValueError('非国家统计局 HTTPS 页面')
    r.encoding = 'utf-8'
    html = r.text
    if f'{year}年农民工监测调查报告' not in html:
        raise ValueError('报告标题未能核对')
    parser = _LeafTables()
    parser.feed(html)
    tables = parser.tables
    if len(tables) == 10 and all((tables[i] == tables[i + 5] for i in range(5))):
        tables = tables[:5]
    if len(tables) != 5:
        raise ValueError('报告表格数量或重复结构变化')
    if any((not t or not any(('单位' in c['text'] for c in t[0])) for t in tables)):
        raise ValueError('表格单位缺失')
    s = BeautifulSoup(html, 'html.parser')
    body = s.select_one('.txt-content')
    return {'source_url': url, 'reference_year': year, 'tables': [{'table': i + 1, 'title': TITLES[i], 'rows': t} for i, t in enumerate(tables) if table in (0, i + 1)], 'report_text': body.get_text('\n', strip=True) if body else None, 'note': '报告文字保留调查与地区口径；原表保留单位和空单元格。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('year', type=int, choices=sorted(URLS))
    p.add_argument('--table', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(report(a.year, a.table), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
