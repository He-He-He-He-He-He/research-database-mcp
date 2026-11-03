"""第三次全国农业普查五号公报及官方 HTML 原表。"""
import release_runtime
import argparse
import json
import requests
from bs4 import BeautifulSoup
from moe_education_statistics_adapters import _LeafTables
BASE = 'https://www.stats.gov.cn/sj/tjgb/nypcgb/qgnypcgb/202302/'
COUNTS = {1: 0, 2: 5, 3: 6, 4: 5, 5: 3}
NAMES = {1: '综合情况与普查说明', 2: '农业生产经营', 3: '农村基础设施与社会服务', 4: '农民生活条件', 5: '农业生产经营人员'}

def report(number, table=0):
    if number not in COUNTS:
        raise ValueError('公报编号须为 1—5')
    if table < 0:
        raise ValueError('表号须为 0 或正整数')
    url = BASE + f't20230206_190210{number}.html'
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if not r.url.startswith(BASE):
        raise ValueError('报告跳转到其他地址')
    r.encoding = 'utf8'
    s = BeautifulSoup(r.text, 'html.parser')
    h = s.select_one('h1')
    if not h or '第三次全国农业普查主要数据公报' not in h.get_text(' ', strip=True):
        raise ValueError('报告标题无法核对')
    p = _LeafTables()
    p.feed(r.text)
    tables = p.tables
    if tables and len(tables) % 2 == 0 and (tables[:len(tables) // 2] == tables[len(tables) // 2:]):
        tables = tables[:len(tables) // 2]
    if len(tables) != COUNTS[number]:
        raise ValueError('表格数量变化，需重新核验')
    if table > len(tables):
        raise ValueError('本号公报无该表号')
    body = s.select_one('.txt-content')
    return {'number': number, 'topic': NAMES[number], 'title': h.get_text(' ', strip=True), 'source_url': url, 'table_count': len(tables), 'tables': [{'number': i + 1, 'rows': t} for i, t in enumerate(tables) if table in (0, i + 1)], 'report_text': body.get_text('\n', strip=True) if body else None, 'note': '保留表头、单位、合并属性及报告全文；第一号无 HTML 表。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('number', type=int, choices=range(1, 6))
    p.add_argument('--table', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(report(a.number, a.table), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
