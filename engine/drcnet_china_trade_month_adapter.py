"""国研网国际贸易系统中国月度默认选项的单月记录。"""
import release_runtime
import requests
from drcnet_trade_china_import_index_adapter import BASE, _auth

def monthly(year, month, flow='import'):
    if type(year) is not int or not 2000 <= year <= 2100 or type(month) is not int or (not 1 <= month <= 12):
        raise ValueError('年份或月份无效')
    if flow not in ('import', 'export'):
        raise ValueError('流向须为 import 或 export')
    body = {'year': str(year), 'endYear': str(year), 'startMonth': str(month), 'endMonth': str(month), 'ioreId': '1' if flow == 'import' else '0', 'moneyItype': '2', 'hsId': '100000', 'regionId': '0', 'stateId': '0', 'trademodeId': '0', 'pageNum': 1, 'pageSize': 10}
    with requests.Session() as s:
        _auth(s)
        r = s.post(BASE + '/table/unAuth/chinaTradeMonth', params={'productId': '0'}, json=body, headers={'api-version': 'V1'}, timeout=30)
        r.raise_for_status()
        try:
            j = r.json()
        except ValueError:
            raise RuntimeError('国研网未返回 JSON') from None
    data = j.get('data') if isinstance(j, dict) and j.get('code') == 200 else None
    if not isinstance(data, list) or len(data) != 1 or (not isinstance(data[0], dict)) or (not isinstance(data[0].get('event'), dict)):
        raise RuntimeError('站方未返回唯一的单月记录')
    row = data[0]['event']
    expected_flow = '进口' if flow == 'import' else '出口'
    if row.get('dateTime') != f'{year}年{month}月' or row.get('ioreName') != expected_flow or any((str(row.get(k)) != v for k, v in [('hsId', '100000'), ('regionId', '0'), ('stateId', '0'), ('trademodeId', '0')])):
        raise RuntimeError('站方记录的月份、流向或分类不匹配')
    return {'source': '国研网国际贸易研究及决策支持系统', 'institution': '浙江大学图书馆（校园 IP）', 'year': year, 'month': month, 'flow': expected_flow, 'money_magnitude_unit': '未知', 'selection': {'hsId': '100000', 'regionId': '0', 'stateId': '0', 'trademodeId': '0', 'moneyItype': '2'}, 'record': row, 'note': '原站中国月度界面默认商品、全国主体、总值伙伴及贸易方式的一条记录；商品名称以源返回为准，不自行断言统计范围。保留原始字段及空值；金额币制选择美元，原始金额数量级单位和编制来源须核原站及海关。'}
