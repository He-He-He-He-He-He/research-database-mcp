"""国别区域与全球治理平台未登录数据检索；保留原始数值及分类。"""
import release_runtime
import requests
URL = 'https://www.crggcn.com/skwx_crgg/countryDataSearch/list'

def search(query, country, page=1, limit=10):
    for label, value in (('关键词', query), ('国家', country)):
        if not isinstance(value, str) or not value.strip() or len(value) > 100 or any((c in value for c in '\r\n')):
            raise ValueError(label + '须为 1–100 字单行文本')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000):
        raise ValueError('页码须为 1–1000')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页须为 1–10 条')
    query = query.strip()
    country = country.strip()
    response = requests.post(URL, data={'q': query, 'countryName': country, 'pi': str(page - 1), 'ps': str(limit)}, timeout=30)
    response.raise_for_status()
    try:
        body = response.json()
    except ValueError:
        raise RuntimeError('数据检索未返回 JSON') from None
    if not isinstance(body, dict) or type(body.get('total')) is not int or body['total'] < 0 or (not isinstance(body.get('hits'), list)) or (len(body['hits']) > limit):
        raise RuntimeError('数据搜索响应异常')
    rows = []
    for hit in body['hits']:
        item = hit.get('source') if isinstance(hit, dict) else None
        if not isinstance(item, dict) or hit.get('type') != 'CountryData' or (not isinstance(hit.get('id'), str)) or (item.get('searchTitle') != country) or (not isinstance(item.get('enSummary'), str)) or (type(item.get('year')) is not int) or (not isinstance(item.get('Value'), str)):
            raise RuntimeError('数据记录国家或字段不一致')
        rows.append({'id': hit['id'], 'country': item['searchTitle'], 'country_id': item.get('countryID'), 'indicator': item['enSummary'], 'indicator_code': item.get('classifyCode'), 'year': item['year'], 'value': item['Value'], 'published': item.get('publishDate')})
    return {'source': '国别区域与全球治理平台公开数据搜索', 'institution': '未核验', 'query': query, 'country': country, 'page': page, 'page_size': limit, 'source_total': body['total'], 'items': rows, 'note': '未登录检索；原站总数是否按国家筛选未核实，不能当作该国记录数。结果可能混合指标与预测年份；响应未提供单位、原始发布机构或预测标记，需核查原始来源。值保留字符串；不代表机构订购数据权限。'}
