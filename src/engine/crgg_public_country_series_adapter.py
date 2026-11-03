"""国别区域与全球治理平台公开图表序列；原始年份和数列对齐保留。"""
import release_runtime
import re
import requests
BASE = 'https://www.crggcn.com/skwx_crgg/'

def series(country_id, indicator_code):
    country_id = str(country_id)
    if not re.fullmatch('[0-9]{1,10}', country_id):
        raise ValueError('国家编号须为数字')
    if not isinstance(indicator_code, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,79}', indicator_code):
        raise ValueError('指标代码无效')
    with requests.Session() as session:
        r = session.get(BASE + 'nationalData/getParentCode', params={'code': indicator_code}, timeout=20)
        r.raise_for_status()
        parent = r.text.strip()
        if not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,79}', parent):
            raise RuntimeError('站方未返回可识别的图表代码')
        r = session.get(BASE + 'country/countryData', params={'countryId': country_id, 'startYear': '', 'endYear': '', 'code': parent}, timeout=30)
        r.raise_for_status()
        try:
            data = r.json()
        except ValueError:
            raise RuntimeError('站方图表未返回 JSON') from None
    if not isinstance(data, list) or len(data) != 1 or (not isinstance(data[0], dict)) or (str(data[0].get('id')) != country_id):
        raise RuntimeError('站方未返回指定国家的图表')
    x = data[0]
    years = x.get('years')
    names = x.get('code_name')
    if not isinstance(years, list) or any((type(y) is not int for y in years)) or (not isinstance(names, dict)) or (indicator_code not in names):
        raise RuntimeError('年份或指标未匹配')
    all_series = {}
    for code, name in names.items():
        values = x.get(code)
        if not isinstance(code, str) or not isinstance(name, str) or (not isinstance(values, list)) or (len(values) != len(years)) or any((v is not None and (not isinstance(v, (str, int, float))) for v in values)):
            raise RuntimeError('图表数列与年份未对齐')
        all_series[code] = {'name': name, 'values': values}
    return {'source': '国别区域与全球治理平台公开图表', 'institution': '未核验', 'country_id': country_id, 'requested_indicator': indicator_code, 'chart_code': parent, 'years': years, 'series': all_series, 'note': '年份与每个指标数列按位置对应，原始值未转换；原站响应未提供单位、原始发布机构或历史/预测标记，存在未来年份，不可直接当实绩引用。未验证学校机构身份及订购范围。'}
