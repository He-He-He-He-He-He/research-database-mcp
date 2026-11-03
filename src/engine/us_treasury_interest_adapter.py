"""美国财政部未偿证券平均利率官方月度数据。"""
import release_runtime
from datetime import date
import requests
URL = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates'

def interest_page(record_date=None, page=1, page_size=30):
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('page 必须为正整数')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size 必须为 1 至 100')
    p = {'sort': '-record_date,src_line_nbr', 'page[number]': page, 'page[size]': page_size}
    if record_date is not None:
        if not isinstance(record_date, str):
            raise ValueError('record_date 应为 YYYY-MM-DD')
        try:
            parsed = date.fromisoformat(record_date)
        except ValueError:
            raise ValueError('record_date 应为 YYYY-MM-DD') from None
        if parsed.isoformat() != record_date:
            raise ValueError('record_date 应为 YYYY-MM-DD')
        p['filter'] = 'record_date:eq:' + record_date
    r = requests.get(URL, params=p, timeout=25)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('data'), list) or not isinstance(d.get('meta'), dict):
        raise RuntimeError('财政部接口返回异常')
    return {'source': '美国财政部 Fiscal Data：未偿证券平均利率', 'scope': '每月按证券类型报告平均利率，百分数；不是市场即时报价或新发行债券收益率。数值保留原始字符串。', 'record_date': record_date, 'page': page, 'page_size': page_size, 'meta': d['meta'], 'items': d['data'], 'documentation': 'https://fiscaldata.treasury.gov/datasets/average-interest-rates-treasury-securities/'}
