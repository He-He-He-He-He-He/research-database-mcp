"""国家统计局季度居民人均消费支出累计值及分类。"""
import release_runtime
import argparse
import json
import re
from research import get
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external'
CID = '71e8c15775d242b8b212edb4cab6e808'
ROOT = 'a94b8b7365a94874968cabbe392cf679'
GROUPS = {'total': ('8e8fb36d72e544658caebd7419900d2a', '居民人均消费支出累计值'), 'food': ('51aedf82379d40a4b9c4bf99d6f9175e', '居民人均食品烟酒支出累计值'), 'clothing': ('c7a3dc6de3ff4281a0da84a30b5daadb', '居民人均衣着支出累计值'), 'housing': ('c5d10091993f49ea90a77fca36e8992d', '居民人均居住支出累计值'), 'household': ('46b713d5ba274243a090409846104c82', '居民人均生活用品及服务支出累计值'), 'transport': ('d31eba40ce184d85b662b5ad6379e083', '居民人均交通通信支出累计值'), 'education': ('b16aad9836a4489b967819c51a8b3a2a', '居民人均教育文化娱乐支出累计值'), 'health': ('7823010ff53e4963a9e18ac7bd126aa7', '居民人均医疗保健支出累计值'), 'other': ('3e924c1be05f4aef9230777cfdb56990', '居民人均其他用品及服务支出累计值')}

def groups():
    response = get(BASE + '/new/queryIndicatorsByCid', {'cid': CID})
    if not response.get('success') or not isinstance(response.get('data', {}).get('list'), list):
        raise ValueError('指标元数据响应异常')
    lookup = {x.get('_id'): x for x in response['data']['list']}
    out = []
    for key, (identifier, name) in GROUPS.items():
        x = lookup.get(identifier)
        if not x or not (x.get('i_showname') or '').startswith(name) or x.get('du_name') != '元/人':
            raise ValueError('指标编码、名称或单位变化：' + key)
        out.append({'group': key, 'id': identifier, 'name': x.get('i_showname'), 'unit': x.get('du_name'), 'upstream_annotation': x.get('i_annotation')})
    return {'source': '国家统计局数据发布库', 'catalog_id': CID, 'items': out, 'note': '季度分类值均为年初至该季末人均支出；官方显示名称括号为元，单位元/人。'}

def _quarter(value):
    if not isinstance(value, str) or not re.fullmatch('(19|20)\\d{2}Q[1-4]', value):
        raise ValueError('季度格式为 YYYYQ1 至 YYYYQ4')
    return (int(value[:4]) * 4 + int(value[-1]), value[:4] + '0' + value[-1] + 'SS')

def spending(group, start, end):
    selected = list(GROUPS) if group == 'all' else [group]
    if any((x not in GROUPS for x in selected)):
        raise ValueError('未知类别，请先查看 groups')
    a, sa = _quarter(start)
    b, sb = _quarter(end)
    if b < a or b - a > 39:
        raise ValueError('季度顺序须正确且跨度不超过 40 个季度')
    metadata = [x for x in groups()['items'] if x['group'] in selected]
    ids = {x['id']: x for x in metadata}
    result = get(BASE + '/stream/esData', body={'cid': CID, 'indicatorIds': list(ids), 'das': [{'text': '全国', 'value': '000000000000'}], 'dts': [sa + '-' + sb], 'showType': '1', 'rootId': ROOT})
    if not result.get('success') or not isinstance(result.get('data'), list):
        raise ValueError('上游数据响应异常')
    for point in result['data']:
        for item in point.get('values', []):
            expected = ids.get(item.get('_id'))
            if not expected or item.get('du_name') != '元/人' or item.get('i_showname') != expected['name']:
                raise ValueError('返回指标或单位不符')
    return {'source': '国家统计局数据发布库', 'groups': metadata, 'start': start, 'end': end, 'data': result['data'], 'note': '全国居民每人年初至当季末累计支出，单位元/人，不是该季度单季支出；元数据中人均消费支出增速为实际增速，本接口只查询金额。缺失不补零。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('groups')
    q = s.add_parser('data')
    q.add_argument('group', choices=['all', *GROUPS])
    q.add_argument('start')
    q.add_argument('end')
    a = p.parse_args()
    print(json.dumps(groups() if a.cmd == 'groups' else spending(a.group, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
