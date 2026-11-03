"""联合国 Monthly Bulletin of Statistics T35 货物贸易总额。"""
import release_runtime
import re
import requests
URL = 'https://comtradeapi.un.org/public/v1/getMBS'

def trade_totals(country, year, frequency='A'):
    country = str(country)
    if not re.fullmatch('\\d{1,3}', country):
        raise ValueError('country 应为联合国统计地区数字代码')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1946 <= year <= 9999):
        raise ValueError('year 应为 1946 之后的年份')
    if frequency not in {'A', 'Q', 'M'}:
        raise ValueError('frequency 仅支持 A、Q、M')
    p = {'series_type': f'T35.{frequency}.V.$', 'year': str(year), 'country_code': country, 'period_type': frequency, 'table_type': 'T35'}
    r = requests.get(URL, params=p, timeout=30)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d, dict) or not isinstance(d.get('data'), list) or d.get('error'):
        raise RuntimeError('联合国 MBS 返回异常')
    rows = d['data']
    if any((str(x.get('country_Code')) != country or x.get('period_Type') != frequency or x.get('year') != year or (x.get('table_Type') != 'T35') for x in rows)):
        raise RuntimeError('联合国 MBS 返回的记录口径不符')
    rows.sort(key=lambda x: (str(x.get('period', '')), str(x.get('trade_Flow', ''))))
    return {'source': '联合国 Monthly Bulletin of Statistics T35 / UN Comtrade 官方公开 API', 'country': country, 'year': year, 'frequency': frequency, 'count': d.get('count'), 'items': rows, 'scope': '各报告经济体对世界货物贸易进出口总额，按年、季或月；金额单位以每行 value_Unit 和 currency_Type 为准，本次样本 M 为百万美元。原始估算状态保留，缺失不代表零。', 'documentation': 'https://comtradeplus-test.azurewebsites.net/en/api-docs'}
