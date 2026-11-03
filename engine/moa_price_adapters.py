"""农业农村部农产品批发价格指数，只读。"""
import release_runtime
import argparse, json, sys
from research import get
URL = 'https://data.moa.gov.cn/nyb/200zs'

def price_list(keyword=''):
    d = get(URL)
    if not isinstance(d, list) or len(d) < 3 or (not all((isinstance(x, list) for x in d[:3]))) or (not len(d[0]) == len(d[1]) == len(d[2])):
        raise ValueError('价格指数响应格式异常')
    items = [{'date': date, 'indicator': name, 'value': value} for date, name, value in zip(d[0], d[1], d[2]) if keyword in name]
    return {'source': '农业农村部农产品批发价格指数', 'source_url': 'https://data.moa.gov.cn/nyb/pc/200zs.jsp', 'items': items, 'note': '仅上游当前返回的数据点，日期可能不是今天；指数的编制口径变化请核对原站。'}

def price_detail(indicator):
    if not indicator.strip():
        raise ValueError('请输入指标名称')
    d = price_list()
    items = [x for x in d['items'] if x['indicator'] == indicator]
    if not items:
        raise ValueError('当前上游数据不包含该指标')
    return {'source': d['source'], 'source_url': d['source_url'], 'indicator': indicator, 'items': items, 'note': d['note']}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('indicator')
    a = p.parse_args()
    print(json.dumps(price_list(a.keyword) if a.cmd == 'list' else price_detail(a.indicator), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
