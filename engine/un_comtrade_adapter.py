"""联合国 Comtrade 官方公开预览 API，无需密钥，非全量下载。"""
import release_runtime
import re
import requests
BASE = 'https://comtradeapi.un.org/public/v1'

def _code(value, pattern, label):
    text = str(value)
    if not re.fullmatch(pattern, text):
        raise ValueError(f'{label} 格式无效')
    return text

def _get(path, params):
    r = requests.get(BASE + path, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict) or not isinstance(data.get('data'), list) or data.get('error'):
        raise RuntimeError('UN Comtrade 返回异常')
    return data

def trade_preview(reporter, period, partner=0, commodity='TOTAL', flow='X'):
    reporter = _code(reporter, '\\d{1,3}', 'reporter')
    partner = _code(partner, '\\d{1,3}', 'partner')
    period = _code(period, '\\d{4}(?:\\d{2})?', 'period')
    if len(period) == 6 and (not 1 <= int(period[4:]) <= 12):
        raise ValueError('月份必须为 01 至 12')
    commodity = _code(commodity, '[A-Za-z0-9]{1,10}', 'commodity').upper()
    flow = _code(flow, '[A-Za-z]{1,3}', 'flow').upper()
    if flow not in {'M', 'X', 'RX', 'RM', 'MIP', 'XIP', 'MOP', 'XOP', 'MIF', 'XIF', 'DX', 'FM'}:
        raise ValueError('不支持的贸易流代码')
    freq = 'A' if len(period) == 4 else 'M'
    p = {'reporterCode': reporter, 'period': period, 'partnerCode': partner, 'cmdCode': commodity, 'flowCode': flow}
    d = _get(f'/preview/C/{freq}/HS', p)
    return {'source': 'UN Comtrade 官方公共预览 API', 'query': p, 'count': d.get('count'), 'items': d['data'], 'scope': '单期单商品、最多 500 行；预览结果不是完整下载。请核对原始报告、计价与修订。'}

def world_share(reporter, year):
    reporter = _code(reporter, '\\d{1,3}', 'reporter')
    year = _code(year, '\\d{4}', 'year')
    d = _get('/getWorldShare/C/A', {'reporterCode': reporter, 'period': year})
    return {'source': 'UN Comtrade 官方公共 API', 'reporter': reporter, 'year': year, 'count': d.get('count'), 'items': d['data'], 'scope': '货物年度世界份额接口，可能包含估计值；worldShare 是比例而非百分数，需核对上游定义。'}
