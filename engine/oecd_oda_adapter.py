"""OECD DAC1 官方发展援助净拨付额（现价美元）。"""
import release_runtime
import csv, io, re
import requests
BASE = 'https://sdmx.oecd.org/public/rest/data/OECD.DCD.FSD,DSD_DAC1@DF_DAC1,1.7/'

def oda_net_disbursements(donor, start='2000', end=None):
    if not isinstance(donor, str) or not re.fullmatch('[A-Z0-9_]{2,15}', donor):
        raise ValueError('donor 应为 OECD 供资者代码')
    for v in (start, end):
        if v is not None and (not isinstance(v, str) or not re.fullmatch('\\d{4}', v)):
            raise ValueError('年份须为四位数字字符串')
    if start and end and (start > end):
        raise ValueError('开始年份不能晚于结束年份')
    p = {'format': 'csvfile'}
    if start:
        p['startPeriod'] = start
    if end:
        p['endPeriod'] = end
    r = requests.get(BASE + f'{donor}._Z.1010..1140.USD.V', params=p, timeout=30)
    if r.status_code == 204:
        rows = []
    else:
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        required = {'DONOR', 'MEASURE', 'FLOW_TYPE', 'UNIT_MEASURE', 'PRICE_BASE', 'UNIT_MULT', 'TIME_PERIOD', 'OBS_VALUE'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise RuntimeError('OECD CSV 列结构异常')
        rows = list(reader)
        if any((x['DONOR'] != donor or x['MEASURE'] != '1010' or x['FLOW_TYPE'] != '1140' or (x['UNIT_MEASURE'] != 'USD') or (x['PRICE_BASE'] != 'V') or (x['UNIT_MULT'] != '6') for x in rows)):
            raise RuntimeError('OECD 数据口径不符')
        rows.sort(key=lambda x: x['TIME_PERIOD'], reverse=True)
    return {'source': 'OECD DAC1 官方 SDMX 数据', 'source_url': r.url, 'donor': donor, 'start': start, 'end': end, 'scope': '官方发展援助 ODA 净拨付额，现价百万美元；非拨款等值、承诺额或通胀调整金额；按供资者统计。', 'items': rows, 'documentation': 'https://data-explorer.oecd.org/vis?df[ag]=OECD.DCD.FSD&df[id]=DSD_DAC1%40DF_DAC1&df[vs]=1.7'}
