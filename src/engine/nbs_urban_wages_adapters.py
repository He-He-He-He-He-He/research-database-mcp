"""国家统计局数据发布库城镇单位就业人员年度平均工资。"""
import release_runtime
import argparse
import json
import re
from research import get
BASE = 'https://data.stats.gov.cn/dg/website/publicrelease/web/external'
ROOT = '884c062607104a91967b22742537f44f'
GROUPS = {'nonprivate': ('c6946b6df4d744b28f10aa5b8c7e8a54', 'a015ca16f7e54fb6873b4953c25d3b76', '城镇非私营单位就业人员平均工资'), 'private': ('e8cf28ec4ebe4dd5a331d2c1d0b820f6', '1990a76984a04edbaa0d5e615002b7fc', '城镇私营单位就业人员平均工资')}

def wage_metadata(group):
    if group not in GROUPS:
        raise ValueError('类别仅支持 nonprivate 或 private')
    cid, identifier, name = GROUPS[group]
    result = get(BASE + '/new/queryIndicatorsByCid', {'cid': cid})
    if not result.get('success') or not isinstance(result.get('data', {}).get('list'), list):
        raise ValueError('指标元数据响应异常')
    items = [x for x in result['data']['list'] if x.get('_id') == identifier]
    if len(items) != 1 or name not in (items[0].get('i_showname') or '') or items[0].get('du_name') != '元':
        raise ValueError('上游指标编码、名称或单位变化')
    x = items[0]
    return {'group': group, 'catalog_id': cid, 'indicator_id': identifier, 'name': x.get('i_showname'), 'unit': x.get('du_name'), 'definition': x.get('i_mark'), 'upstream_annotation': x.get('i_annotation')}

def wages(group, start, end):
    if not isinstance(start, str) or not isinstance(end, str) or (not re.fullmatch('(19|20)\\d{2}', start)) or (not re.fullmatch('(19|20)\\d{2}', end)):
        raise ValueError('年份须为 YYYY')
    if int(end) < int(start) or int(end) - int(start) > 49:
        raise ValueError('年份顺序须正确且跨度不超过 50 年')
    meta = wage_metadata(group)
    result = get(BASE + '/stream/esData', body={'cid': meta['catalog_id'], 'indicatorIds': [meta['indicator_id']], 'das': [{'text': '全国', 'value': '000000000000'}], 'dts': [start + 'YY-' + end + 'YY'], 'showType': '1', 'rootId': ROOT})
    if not result.get('success') or not isinstance(result.get('data'), list):
        raise ValueError('上游数据响应异常')
    for point in result['data']:
        for item in point.get('values', []):
            if item.get('_id') != meta['indicator_id'] or item.get('du_name') != '元' or GROUPS[group][2] not in (item.get('i_showname') or ''):
                raise ValueError('返回指标或单位不符')
    out = {'source': '国家统计局数据发布库', 'metadata': meta, 'start': start, 'end': end, 'data': result['data'], 'note': '单位为元/年，统计的是对应城镇单位就业人员货币工资平均值，不是个人工资中位数或所有劳动者收入；空字符串、空值和缺失年份保留、不当作零。'}
    if group == 'private' and int(start) <= 2025 <= int(end):
        points = [v for point in result['data'] if point.get('code') == '2025YY' for v in point.get('values', []) if v.get('_id') == meta['indicator_id']]
        if not points or all((v.get('value') in ('', None) for v in points)):
            out['crosscheck_note'] = '发布库该指标 2025 年为空；国家统计局同期工资报告另有数值，应查正式报告，不自动填补。'
            out['crosscheck_url'] = 'https://www.stats.gov.cn/sj/zxfb/202605/t20260515_1963707.html'
    return out

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
    print(json.dumps(wage_metadata(a.group) if a.cmd == 'metadata' else wages(a.group, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
