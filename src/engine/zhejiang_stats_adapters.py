"""通过国家统计局数据发布库查询浙江省年度指标，只读。"""
import release_runtime
import argparse, json, re, sys
from research import get
from china_data_adapters import stats_search
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external'

def zhejiang_search(keyword, page=1):
    if not keyword.strip():
        raise ValueError('请输入指标关键词')
    raw = stats_search('浙江' + keyword, page, 10)
    items = [x for x in raw['data'].get('data', []) if x.get('da') == '330000000000' and x.get('type_value') == '6']
    return {'source': '国家统计局数据发布库', 'source_url': 'https://data.stats.gov.cn/', 'query': keyword, 'page': page, 'items': items, 'note': '只保留当前一页搜索结果中浙江省分省年度数据；不同时间段、单位、统计口径需核对。'}

def zhejiang_annual(cid, indicator, root_id, year):
    if any((not re.fullmatch('[0-9a-fA-F]{32}', s) for s in (cid, indicator, root_id))) or not 1900 <= int(year) <= 2100:
        raise ValueError('数据集、指标和根节点需为 32 位 ID，年份需有效')
    body = {'cid': cid, 'indicatorIds': [indicator], 'das': [{'text': '浙江省', 'value': '330000000000'}], 'dts': [str(year) + 'YY'], 'showType': '2', 'rootId': root_id}
    data = get(BASE + '/stream/esData', body=body)
    if not data.get('success'):
        raise ValueError('国家数据未返回成功结果')
    return {'source': '国家统计局数据发布库', 'area': '浙江省', 'year': int(year), 'data': data.get('data'), 'note': '单一年度；请同时参考指标元数据的单位、解释和修订情况。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('annual')
    q.add_argument('cid')
    q.add_argument('indicator')
    q.add_argument('root_id')
    q.add_argument('year', type=int)
    a = p.parse_args()
    print(json.dumps(zhejiang_search(a.keyword, a.page) if a.cmd == 'search' else zhejiang_annual(a.cid, a.indicator, a.root_id, a.year), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
