"""美国劳工统计局无需注册的公共 API v1 单序列（最近三年）。"""
import release_runtime
import re
import requests
BASE = 'https://api.bls.gov/publicAPI/v1/timeseries/data/'
KNOWN = {'CUUR0000SA0': {'description': 'CPI-U 美国城市平均、全部项目、未季调', 'unit': '指数（1982–1984 年均值=100）', 'method_url': 'https://www.bls.gov/cpi/factsheets/cpi-series-ids.htm'}, 'LNS14000000': {'description': '美国失业率，季节调整', 'unit': '百分数', 'method_url': 'https://www.bls.gov/web/empsit/cps_charts.pdf'}}

def series_recent(series_id):
    if not isinstance(series_id, str) or not re.fullmatch('[A-Za-z0-9]{5,40}', series_id):
        raise ValueError('series_id 必须为 5 至 40 位英文字母或数字')
    series_id = series_id.upper()
    r = requests.get(BASE + series_id, timeout=20)
    r.raise_for_status()
    d = r.json()
    if d.get('status') != 'REQUEST_SUCCEEDED':
        raise RuntimeError('BLS 查询失败：' + '; '.join(d.get('message', [])))
    series = d.get('Results', {}).get('series', [])
    if not isinstance(series, list) or len(series) != 1 or series[0].get('seriesID') != series_id:
        raise RuntimeError('BLS 未返回预期序列')
    return {'source': '美国劳工统计局 BLS 公共 API v1', 'series_id': series_id, 'metadata': KNOWN.get(series_id), 'items': series[0].get('data', []), 'scope': '单序列最近约三年；v1 不返回系列描述，未知编码的定义和单位须自行核对。未注册共享限额为每日 25 次。'}
