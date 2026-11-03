"""农业农村部三农数据中已验证的两项年度指标，只读。"""
import release_runtime
import argparse, json, sys
from research import get
CATALOG = {'qgnmggm': '农民工规模年度变化', 'qgnlmyyzcz': '农林牧渔业总产值年度变化'}

def rural_list(keyword=''):
    return {'source': '农业农村部三农数据', 'source_url': 'https://data.moa.gov.cn/nyb/pc/agriculture.jsp', 'scope': '仅列出已验证的两个年度指标', 'items': [{'id': k, 'title': v} for k, v in CATALOG.items() if keyword in v]}

def rural_detail(id):
    if id not in CATALOG:
        raise ValueError('指标不在已验证目录中')
    d = get('https://data.moa.gov.cn/nyb/queryEchartsData', body={'query': id})
    chart = (d.get('data') or {}).get('echarts')
    if d.get('code') != 200 or not isinstance(chart, dict):
        raise ValueError('上游未返回有效图表数据')
    return {'source': '农业农村部三农数据', 'source_url': 'https://data.moa.gov.cn/nyb/pc/agriculture.jsp', 'id': id, 'title': CATALOG[id], 'chart': chart, 'note': '保留原图表字段与坐标轴单位，不自动推断每条系列与坐标轴的对应关系；年份、统计口径和修订以官网为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(rural_list(a.keyword) if a.cmd == 'list' else rural_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
