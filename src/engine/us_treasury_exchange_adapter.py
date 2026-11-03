"""美国财政部季度报告汇率，不是即时交易汇率。"""
import release_runtime
import re
import requests
URL = 'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/rates_of_exchange'

def exchange_page(country, page=1, page_size=20):
    if not isinstance(country, str) or not re.fullmatch("[A-Za-z][A-Za-z .'-]{0,79}", country):
        raise ValueError('country 须为官方英文国家名称')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('page 必须为正整数')
    if isinstance(page_size, bool) or not isinstance(page_size, int) or (not 1 <= page_size <= 100):
        raise ValueError('page_size 必须为 1 至 100')
    p = {'filter': 'country:eq:' + country, 'sort': '-record_date', 'page[number]': page, 'page[size]': page_size}
    r = requests.get(URL, params=p, timeout=25)
    r.raise_for_status()
    d = r.json()
    if not isinstance(d.get('data'), list) or not isinstance(d.get('meta'), dict):
        raise RuntimeError('财政部接口返回异常')
    return {'source': '美国财政部 Treasury Reporting Rates of Exchange', 'country': country, 'scope': '财政报告使用的季度汇率，可能有期间修订；每 1 美元对应的当地货币单位，不是实时或交易报价。', 'page': page, 'page_size': page_size, 'meta': d['meta'], 'items': d['data'], 'documentation': 'https://fiscaldata.treasury.gov/datasets/treasury-reporting-rates-exchange/'}
