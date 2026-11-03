"""国家统计局季度居民人均可支配收入累计值。"""
import release_runtime
import argparse
import json
import re
from research import get
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external'
ROOT = 'a94b8b7365a94874968cabbe392cf679'
GROUPS = {'national': ('ec2d57ed282f456e8d025aff035b4fad', 'bb5699c5ad534b568cca7c946227225a', '居民人均可支配收入累计值'), 'urban': ('564537ad2e5049a6aee74c834b675748', 'e0b8d37be1b3445e8cbef405a28c5d95', '城镇居民人均可支配收入累计值'), 'rural': ('62c5dd0cb4b74602b64e19e948460472', 'e80dbdec8c354aebaef94cb4d27a1ecb', '农村居民人均可支配收入累计值')}

def income_metadata(group):
    if group not in GROUPS:
        raise ValueError('类别仅支持 national、urban、rural')
    cid, identifier, name = GROUPS[group]
    response = get(BASE + '/new/queryIndicatorsByCid', {'cid': cid})
    if not response.get('success') or not isinstance(response.get('data', {}).get('list'), list):
        raise ValueError('指标元数据响应异常')
    items = [x for x in response['data']['list'] if x.get('_id') == identifier]
    if len(items) != 1 or not (items[0].get('i_showname') or '').startswith(name) or items[0].get('du_name') != '元':
        raise ValueError('上游指标编码、名称或单位变化')
    x = items[0]
    return {'group': group, 'catalog_id': cid, 'indicator_id': identifier, 'name': x.get('i_showname'), 'unit': x.get('du_name'), 'definition': x.get('i_mark'), 'upstream_annotation': x.get('i_annotation')}

def _quarter(value):
    if not isinstance(value, str) or not re.fullmatch('(19|20)\\d{2}Q[1-4]', value):
        raise ValueError('季度格式为 YYYYQ1 至 YYYYQ4')
    return (int(value[:4]) * 4 + int(value[-1]), value[:4] + '0' + value[-1] + 'SS')

def income(group, start, end):
    a, sa = _quarter(start)
    b, sb = _quarter(end)
    if b < a or b - a > 39:
        raise ValueError('季度顺序须正确且跨度不超过 40 个季度')
    meta = income_metadata(group)
    result = get(BASE + '/stream/esData', body={'cid': meta['catalog_id'], 'indicatorIds': [meta['indicator_id']], 'das': [{'text': '全国', 'value': '000000000000'}], 'dts': [sa + '-' + sb], 'showType': '1', 'rootId': ROOT})
    if not result.get('success') or not isinstance(result.get('data'), list):
        raise ValueError('上游数据响应异常')
    for point in result['data']:
        for item in point.get('values', []):
            if item.get('_id') != meta['indicator_id'] or item.get('du_name') != '元' or (not (item.get('i_showname') or '').startswith(GROUPS[group][2])):
                raise ValueError('返回指标或单位不符')
    return {'source': '国家统计局数据发布库', 'metadata': meta, 'start': start, 'end': end, 'data': result['data'], 'note': '季度数值为自当年年初至该季度末的累计人均可支配收入，单位元，不是单季度收入，也不是工资中位数；缺失不补零。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('metadata')
    q.add_argument('group', choices=list(GROUPS))
    q = s.add_parser('data')
    q.add_argument('group', choices=list(GROUPS))
    q.add_argument('start')
    q.add_argument('end')
    a = p.parse_args()
    print(json.dumps(income_metadata(a.group) if a.cmd == 'metadata' else income(a.group, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
