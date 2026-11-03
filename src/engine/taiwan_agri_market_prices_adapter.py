"""台湾地区农业部门公开的农产品批发市场交易行情。"""
import release_runtime
import requests
URL = 'https://data.moa.gov.tw/Service/OpenData/FromM/FarmTransData.aspx'

def prices(offset=0, limit=50):
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 500):
        raise ValueError('offset 须非负，limit 须为 1 至 500')
    p = {'IsTransData': '1', 'UnitId': '037', '$top': limit, '$skip': offset}
    r = requests.get(URL, params=p, timeout=30, allow_redirects=False)
    r.raise_for_status()
    if r.is_redirect:
        raise RuntimeError('官网请求重定向')
    try:
        rows = r.json()
    except ValueError as e:
        raise RuntimeError('官网返回非 JSON') from e
    if not isinstance(rows, list) or len(rows) > limit or (not all((isinstance(x, dict) and '交易日期' in x and ('市場名稱' in x) for x in rows))):
        raise RuntimeError('官网行情结构异常')
    return {'source': '台湾地区农业部门农产品交易行情', 'source_url': 'https://data.gov.tw/dataset/8066', 'offset': offset, 'limit': limit, 'count_on_page': len(rows), 'items': rows, 'note': '日期为民国纪年，平均价等价格单位按官网标示为元/公斤，交易量公斤；为上游当前发布的批发交易记录，不代表零售价格或历史全量。只支持分页，不宣称服务端关键词或日期筛选。'}
