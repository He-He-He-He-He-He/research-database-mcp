"""Public monthly green certificate cancellation statistics from NEA."""
import release_runtime
import requests
URL = 'https://gec.nea.gov.cn/api/admin/loginData/cancel'
TYPE_NAMES = {1: '绿色电力消费', 2: 'CCER核证减排量', 3: '唯一绿证账户注销', 4: '超出有效期'}

def cancellations(year, month):
    if type(year) is not int or not 2025 <= year <= 2100 or type(month) is not int or (not 1 <= month <= 12):
        raise ValueError('year must be 2025 or later and month 1–12')
    r = requests.get(URL, params={'year': year, 'month': month}, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect:
        raise ValueError('unexpected redirect')
    obj = r.json()
    if obj.get('code') != 200 or not isinstance(obj.get('data'), list):
        raise ValueError('unexpected upstream response')
    rows = []
    for item in obj['data']:
        if item.get('year') != year or item.get('month') != month or item.get('type') not in TYPE_NAMES:
            raise ValueError('unexpected record or type')
        rows.append({**item, 'type_name': TYPE_NAMES[item['type']]})
    return {'source': '国家能源局国家绿证核发交易系统公开首页', 'source_url': r.url, 'year': year, 'month': month, 'rows': rows, 'note': '重复类型记录原样保留，不自动合并；空列表表示上游未提供记录，不等于零。'}
