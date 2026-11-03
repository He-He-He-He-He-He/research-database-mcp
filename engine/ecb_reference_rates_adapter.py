"""ECB 公开 API 的每日欧元参考汇率。"""
import release_runtime
import argparse, csv, io, json, re, subprocess
from datetime import date
from urllib.parse import urlencode

def rates(currency='CNY', start='', end='', last=10):
    if not isinstance(currency, str) or not re.fullmatch('[A-Z]{3}', currency):
        raise ValueError('currency 必须为大写三字母货币代码')
    for d in (start, end):
        if d:
            try:
                date.fromisoformat(d)
            except ValueError as e:
                raise ValueError('日期应为 YYYY-MM-DD') from e
    if start and end and (start > end):
        raise ValueError('开始日期不得晚于结束日期')
    if not 1 <= int(last) <= 1000:
        raise ValueError('last 应为 1–1000')
    params = {'format': 'csvdata', 'lastNObservations': int(last)}
    if start:
        params['startPeriod'] = start
    if end:
        params['endPeriod'] = end
    url = 'https://data-api.ecb.europa.eu/service/data/EXR/D.' + currency + '.EUR.SP00.A?' + urlencode(params)
    p = release_runtime.run(['curl', '--silent', '--show-error', '--fail', '--location', '--max-time', '25', url], capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError('ECB 数据请求失败（货币代码可能无序列）: ' + p.stderr.strip())
    reader = csv.DictReader(io.StringIO(p.stdout))
    if not reader.fieldnames or not {'TIME_PERIOD', 'OBS_VALUE', 'OBS_STATUS', 'UNIT', 'CURRENCY_DENOM'}.issubset(reader.fieldnames):
        raise RuntimeError('ECB 响应结构异常')
    rows = list(reader)
    if any((r['CURRENCY_DENOM'] != 'EUR' or r['UNIT'] != currency for r in rows)):
        raise RuntimeError('ECB 响应货币不一致')
    items = [{'date': r['TIME_PERIOD'], 'value': float(r['OBS_VALUE']) if r['OBS_VALUE'] else None, 'raw_value': r['OBS_VALUE'], 'status': r['OBS_STATUS'], 'confidentiality': r.get('OBS_CONF'), 'comment': r.get('OBS_COM')} for r in rows]
    return {'source': 'European Central Bank, EXR', 'source_url': url, 'documentation': 'https://data.ecb.europa.eu/help/api/data-examples', 'currency': currency, 'denominator': 'EUR', 'unit': currency + ' per 1 EUR', 'frequency': 'daily', 'scope': '欧洲央行参考汇率，通常工作日公布，并非实时或交易报价；日期范围中最多返回最近 last 个观测。原始观测数值字符串和状态予以保留。', 'count': len(items), 'items': items}
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('currency', nargs='?', default='CNY')
    p.add_argument('--start', default='')
    p.add_argument('--end', default='')
    p.add_argument('--last', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(rates(a.currency, a.start, a.end, a.last), ensure_ascii=False, indent=2))
