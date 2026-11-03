"""尼泊尔央行官方外币买入卖出牌价，按日期分页。"""
import release_runtime
import argparse
from datetime import date
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://www.nrb.org.np/api/forex/v1/rates'

def rates(start, end, page=1, per_page=30, currency=''):
    try:
        a = date.fromisoformat(start)
        b = date.fromisoformat(end)
    except (ValueError, TypeError):
        raise ValueError('日期须为 YYYY-MM-DD')
    if a > b or (b - a).days > 365:
        raise ValueError('日期次序错误或范围超过 366 日')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 10000) or isinstance(per_page, bool) or (not isinstance(per_page, int)) or (not 1 <= per_page <= 100):
        raise ValueError('分页参数无效')
    if not isinstance(currency, str) or not re.fullmatch('(?:[A-Z]{3})?', currency):
        raise ValueError('币种须为大写 ISO3')
    url = BASE + '?' + urlencode({'from': start, 'to': end, 'page': page, 'per_page': per_page})
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', '5000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('尼泊尔央行请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > 5000000:
        raise ValueError('响应超过大小限制')
    value = json.loads(p.stdout)
    payload = value.get('data', {}).get('payload')
    if value.get('status', {}).get('code') != 200 or not isinstance(payload, list) or (not isinstance(value.get('pagination'), dict)):
        raise ValueError('上游返回失败或格式异常')
    rows = []
    for day in payload:
        if not isinstance(day, dict) or not isinstance(day.get('rates'), list):
            raise ValueError('牌价结构异常')
        row = dict(day)
        if currency:
            row['rates'] = [x for x in day['rates'] if x.get('currency', {}).get('iso3') == currency]
        rows.append(row)
    return {'source': url, 'currency_filter': currency, 'data': rows, 'pagination': value['pagination'], 'note': '每个买入/卖出数值是指定 currency.unit 外币对应的尼泊尔卢比，保留原始字符串及发布时间；当地银行实际汇率可能不同。分页总数按日期计，非币种记录数。'}

def currencies(day):
    result = rates(day, day, 1, 1)
    if not result['data']:
        return {'source': result['source'], 'date': day, 'currencies': [], 'note': '该日无返回记录，不代表其他日期无数据。'}
    return {'source': result['source'], 'date': day, 'currencies': [r['currency'] for r in result['data'][0]['rates']], 'note': '只反映指定日期的货币清单；某些货币以 100 等单位报价。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('rates')
    q.add_argument('start')
    q.add_argument('end')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--per-page', type=int, default=30)
    q.add_argument('--currency', default='')
    q = s.add_parser('currencies')
    q.add_argument('day')
    a = p.parse_args()
    v = currencies(a.day) if a.cmd == 'currencies' else rates(a.start, a.end, a.page, a.per_page, a.currency)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
