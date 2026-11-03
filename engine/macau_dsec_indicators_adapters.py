"""澳门统计暨普查局官方网络服务：主要指标目录及最新值。"""
import release_runtime
import argparse
import json
from xml.etree import ElementTree as ET
import requests
BASE = 'https://www.dsec.gov.mo/TimeSeriesDatabase.asmx/'
DOC = 'https://www.dsec.gov.mo/TimeSeriesDatabase.asmx'
NS = {'d': 'http://www.dsec.gov.mo/'}

def _get(method, params):
    r = requests.get(BASE + method, params=params, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    if root.findtext('d:StatusCode', namespaces=NS) != '0':
        raise ValueError('统计局返回错误状态')
    return root

def indicators(keyword=''):
    root = _get('getKeyIndicatorList', {'vLanguageType': 'SimplifiedChinese'})
    out = []
    for item in root.findall('d:DSECKeyIndicator/d:DSECKeyIndicator', NS):
        name = item.findtext('d:Description', namespaces=NS)
        ident = item.findtext('d:KeyIndicatorID', namespaces=NS)
        period = item.findtext('d:DataPeriod', namespaces=NS)
        if not name or not ident or (not ident.isdigit()):
            raise ValueError('指标目录结构异常')
        if keyword.casefold() in name.casefold():
            out.append({'id': int(ident), 'name': name, 'period_type': period})
    return {'source': '澳门特别行政区政府统计暨普查局', 'api': BASE + 'getKeyIndicatorList', 'documentation': DOC, 'keyword': keyword, 'count': len(out), 'items': out}

def indicator_latest(indicator_id):
    if not str(indicator_id).isdigit() or int(indicator_id) < 1:
        raise ValueError('指标 ID 必须为正整数')
    indicator_id = int(indicator_id)
    lookup = indicators()['items']
    match = [x for x in lookup if x['id'] == indicator_id]
    if len(match) != 1:
        raise ValueError('指标不在当前官方主要指标目录中')
    root = _get('getKeyIndicatorValue', {'iKeyIndicatorID': indicator_id, 'vLanguageType': 'SimplifiedChinese'})
    items = []
    for row in root.findall('d:IndicatorData/d:DSECIndicatorWSData', NS):
        fields = ['ReferencePeriod', 'UnitLabel', 'Year', 'PeriodID', 'IndicatorValue', 'RemarkSymbol', 'RemarkDescription']
        items.append({k: row.findtext('d:' + k, namespaces=NS) for k in fields})
    if not items:
        raise ValueError('该指标当前无数据')
    return {'source': '澳门特别行政区政府统计暨普查局', 'api': BASE + 'getKeyIndicatorValue', 'documentation': DOC, 'indicator': match[0], 'items': items, 'note': '最新值可能随官方更新或修订；保留参考期、单位及备注。'}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='cmd', required=True)
    li = sub.add_parser('list')
    li.add_argument('--keyword', default='')
    val = sub.add_parser('latest')
    val.add_argument('id', type=int)
    a = p.parse_args()
    print(json.dumps(indicators(a.keyword) if a.cmd == 'list' else indicator_latest(a.id), ensure_ascii=False, indent=2))
