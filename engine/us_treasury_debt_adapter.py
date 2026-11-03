"""美国财政部 Fiscal Data 官方 Debt to the Penny 数据。"""
import release_runtime
from datetime import date
import requests
URL = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny'

def debt_page(start=None, end=None, page=1, page_size=30):
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('page 必须为正整数')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size 必须为 1 至 100')

    def valid(value):
        if not isinstance(value, str):
            raise ValueError('日期应为 YYYY-MM-DD')
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError('日期应为 YYYY-MM-DD') from None
        if parsed.isoformat() != value:
            raise ValueError('日期应为 YYYY-MM-DD')
        return parsed
    st = valid(start) if start is not None else None
    en = valid(end) if end is not None else None
    if st and en and (st > en):
        raise ValueError('开始日期不能晚于结束日期')
    p = {'sort': '-record_date', 'page[number]': page, 'page[size]': page_size}
    filters = []
    if start:
        filters.append('record_date:gte:' + start)
    if end:
        filters.append('record_date:lte:' + end)
    if filters:
        p['filter'] = ','.join(filters)
    r = requests.get(URL, params=p, timeout=25)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('data'), list) or not isinstance(d.get('meta'), dict):
        raise RuntimeError('财政部接口返回异常')
    return {'source': '美国财政部 Fiscal Data: Debt to the Penny', 'unit': '美元；金额保留原始十进制字符串', 'scope': '美国公共债务余额：公众持有债务加政府内部持有；不等于债务上限或年度赤字。通常按工作日发布。', 'page': page, 'page_size': page_size, 'meta': d['meta'], 'items': d['data'], 'documentation': 'https://fiscaldata.treasury.gov/datasets/debt-to-the-penny/'}
