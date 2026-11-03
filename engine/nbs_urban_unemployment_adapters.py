"""国家统计局数据发布库城镇调查失业率，按已验证指标查询。"""
import release_runtime
import argparse
import json
import re
from research import get
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external'
CID = 'ee3b7046b390415b9b7745e3d16f6052'
ROOT_ID = 'fc982599aa684be7969d7b90b1bd0e84'
GROUPS = {'national': ('3888eac6062945a79c8a27e5f13d4953', '城镇调查失业率'), 'city31': ('1d550f3ec77a463bb607d4a3427e1465', '31个大城市城镇调查失业率'), 'age16_24': ('bd6da1abb26046c2acb38aa701d90e86', '不包含在校生的16—24岁劳动力失业率'), 'age25_29': ('7bc1bd5daeac48ae8bb413c34ece1d08', '不包含在校生的25—29岁劳动力失业率'), 'age30_59': ('c03a36c9562246b6bc8aab010951ef1c', '不包含在校生的30—59岁劳动力失业率')}

def _month(value):
    if not isinstance(value, str) or not re.fullmatch('(19|20)\\d{2}(0[1-9]|1[0-2])', value):
        raise ValueError('月份必须为 YYYYMM')
    return int(value[:4]) * 12 + int(value[4:])

def groups():
    response = get(BASE + '/new/queryIndicatorsByCid', {'cid': CID})
    if not response.get('success') or not isinstance(response.get('data', {}).get('list'), list):
        raise ValueError('国家统计局指标元数据异常')
    lookup = {x.get('_id'): x for x in response['data']['list']}
    out = []
    for key, (identifier, expected) in GROUPS.items():
        x = lookup.get(identifier)
        if not x or x.get('_name') != expected or x.get('du_name') != '%':
            raise ValueError('上游指标编码或定义变化：' + key)
        out.append({'group': key, 'id': identifier, 'name': x['_name'], 'display_name': x.get('i_showname'), 'unit': x.get('du_name'), 'definition': x.get('i_mark'), 'upstream_annotation': x.get('i_annotation')})
    return {'source': '国家统计局数据发布库', 'catalog_id': CID, 'items': out, 'note': '年龄分组从 2023 年 12 月起调整，往月数据包含在校生；年龄组与总体不是完全相同分母。'}

def unemployment(group, start, end):
    if group not in GROUPS:
        raise ValueError('未知人群，请先查看 groups')
    a, b = (_month(start), _month(end))
    if b < a or b - a > 119:
        raise ValueError('时间顺序须正确且不超过 120 个月')
    if group.startswith('age') and start < '202312':
        raise ValueError('年龄口径 2023 年 12 月调整；本接口年龄分组仅支持 202312 及以后')
    metadata = next((x for x in groups()['items'] if x['group'] == group))
    data = get(BASE + '/stream/esData', body={'cid': CID, 'indicatorIds': [metadata['id']], 'das': [{'text': '全国', 'value': '000000000000'}], 'dts': [start + 'MM-' + end + 'MM'], 'showType': '1', 'rootId': ROOT_ID})
    if not data.get('success') or not isinstance(data.get('data'), list):
        raise ValueError('上游数据响应异常')
    for time_point in data['data']:
        for item in time_point.get('values', []):
            if item.get('_id') != metadata['id'] or item.get('du_name') != '%' or item.get('_name') != metadata['name']:
                raise ValueError('返回指标身份或单位不符')
    return {'source': '国家统计局数据发布库', 'group': metadata, 'start': start, 'end': end, 'data': data['data'], 'note': '城镇调查失业率为城镇失业人口占就业与失业人口之和的百分比；年龄组不包含在校生，不能等同全体同龄人口失业比例。缺失月份不补零；数据可修订。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('groups')
    q = s.add_parser('data')
    q.add_argument('group', choices=list(GROUPS))
    q.add_argument('start')
    q.add_argument('end')
    a = p.parse_args()
    print(json.dumps(groups() if a.cmd == 'groups' else unemployment(a.group, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
