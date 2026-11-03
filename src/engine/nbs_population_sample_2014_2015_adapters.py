"""国家数据：2014—2019、2021—2024年按年龄和性别分组的人口调查样本数。"""
import release_runtime
import argparse
import json
import re
from research import get
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external'
ROOT = '69c574ab128a44e595cc0b24502b771b'
GROUPS = {'total': '16f09026c6b34e688b307c4b7c9f4633', 'male': '0dcabfd7cd074300a28677825cd00217', 'female': '8e796f1413004b9fac67b1d709c87483'}

def metadata(group):
    if group not in GROUPS:
        raise ValueError('group 为 total、male、female')
    x = get(BASE + '/new/queryIndicatorsByCid', {'cid': GROUPS[group]})
    if not x.get('success') or not isinstance(x.get('data', {}).get('list'), list):
        raise ValueError('上游元数据异常')
    rows = x['data']['list']
    if not rows or any((v.get('du_name') != '人' or '人口抽样调查' not in (v.get('i_showname') or '') for v in rows)):
        raise ValueError('上游单位或指标类型变化')
    return {'group': group, 'catalog_id': GROUPS[group], 'items': [{'id': v['_id'], 'name': v.get('i_showname'), 'unit': v.get('du_name'), 'annotation': v.get('i_annotation')} for v in rows]}

def data(group, indicator_id, start=2014, end=2015):
    if not (2014 <= start <= end <= 2019 or 2021 <= start <= end <= 2024):
        raise ValueError('仅支持2014—2019或2021—2024，不能跨越未验证的2020年')
    meta = metadata(group)
    hits = [x for x in meta['items'] if x['id'] == indicator_id]
    if len(hits) != 1:
        raise ValueError('指标不属于所选类别；先查询 metadata')
    body = {'cid': meta['catalog_id'], 'indicatorIds': [indicator_id], 'das': [{'text': '全国', 'value': '000000000000'}], 'dts': [f'{start}YY-{end}YY'], 'showType': '1', 'rootId': ROOT}
    result = get(BASE + '/stream/esData', body=body)
    if not result.get('success') or not isinstance(result.get('data'), list):
        raise ValueError('上游数据异常')
    for point in result['data']:
        if not re.fullmatch('[0-9]{4}YY', point.get('code', '')) or not start <= int(point['code'][:4]) <= end:
            raise ValueError('上游年份不符')
        for item in point.get('values', []):
            if item.get('_id') != indicator_id or item.get('du_name') != '人' or item.get('da') != '000000000000':
                raise ValueError('上游指标、单位或地区不符')
    return {'source': '国家统计局数据发布库', 'metadata': hits[0], 'start': start, 'end': end, 'data': result['data'], 'note': '调查样本人数，非全国总人口；各年抽样比不同，不可直接比较样本数。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    m = s.add_parser('metadata')
    m.add_argument('group', choices=GROUPS)
    d = s.add_parser('data')
    d.add_argument('group', choices=GROUPS)
    d.add_argument('indicator_id')
    d.add_argument('--start', type=int, default=2014)
    d.add_argument('--end', type=int, default=2015)
    a = p.parse_args()
    print(json.dumps(metadata(a.group) if a.command == 'metadata' else data(a.group, a.indicator_id, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
