"""Public pre-login national green electricity certificate statistics."""
import release_runtime
import requests
BASE = 'https://gec.nea.gov.cn/api/admin/loginData/'
KINDS = {'monthly_issue': ('list', True), 'monthly_trades': ('transferNumList', True), 'monthly_trade_prices': ('transferPriceList', True), 'monthly_price_index': ('priceMonth', True), 'annual_issue': ('list', False)}

def statistics(kind, year, month=None):
    if kind not in KINDS:
        raise ValueError('unknown statistics kind')
    if type(year) is not int or not 2025 <= year <= 2100:
        raise ValueError('year must be 2025 or later')
    endpoint, needs_month = KINDS[kind]
    if needs_month and (type(month) is not int or not 1 <= month <= 12):
        raise ValueError('month must be 1–12')
    if not needs_month and month is not None:
        raise ValueError('annual_issue takes no month')
    params = {'year': year, 'dataType': 1 if needs_month else 3}
    if needs_month:
        params['month'] = month
    r = requests.get(BASE + endpoint, params=params, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect:
        raise ValueError('unexpected redirect')
    obj = r.json()
    if obj.get('code') != 200 or not isinstance(obj.get('data'), (dict, list)):
        raise RuntimeError('official data unavailable: ' + str(obj.get('msg')))
    data = obj['data']
    if isinstance(data, dict) and 'year' in data and (data['year'] != year):
        raise ValueError('upstream year differs from requested year')
    if needs_month and isinstance(data, dict) and ('month' in data) and (data['month'] != month):
        raise ValueError('upstream month differs from requested month')
    return {'source': '国家能源局国家绿证核发交易系统公开首页', 'source_url': r.url, 'kind': kind, 'year': year, 'month': month, 'data': data, 'note': '原始字段原样返回。年度核发的实际覆盖月份以 remark 为准，不假定全年；价格与数量、当月与当年累计不可混同。' + ('2025年12月核发样本的能源分类值之和与全国值不一致，原因待核，勿自动归一化。' if kind == 'monthly_issue' and year == 2025 and (month == 12) else '')}
