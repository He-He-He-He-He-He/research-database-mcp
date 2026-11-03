"""国研网中国月度 HS 顶层商品进出口指数：学校 IP、单月、原始值。"""
import release_runtime
import json
import requests
AUTH = 'https://user.drcnet.com.cn/userapi/loginController/initLoginP'
BASE = 'https://trade.drcnet.com.cn/prod-api/f'
INDICATORS = 'IE02GH,IE02GT,IE02SH,IE02ST,IE02ZH,IE02ZT'
EXPORT_INDICATORS = 'IE03GH,IE03GT,IE03SH,IE03ST,IE03ZH,IE03ZT'

def _auth(session):
    r = session.get(AUTH, params={'flag': 'initp'}, timeout=20)
    r.raise_for_status()
    raw = r.text.strip()
    if raw.startswith('(') and raw.endswith(')'):
        raw = raw[1:-1]
    try:
        auth = json.loads(raw)
    except ValueError:
        raise RuntimeError('未识别学校登录响应') from None
    if auth.get('UserName') != '浙江大学图书馆' or auth.get('IsAdvIP') is not True or auth.get('Logined') != 1:
        raise RuntimeError('未确认浙江大学图书馆校园 IP 授权')

def _categories(session, parent=''):
    r = session.get(BASE + '/selectBox/unAuth/getChinaMonthTradeGoods', params={'digit': '4', 'parentId': parent, 'dimensionType': 'HS', 'level': 1 if parent else 0, 'productId': '0'}, headers={'api-version': 'V1'}, timeout=20)
    r.raise_for_status()
    body = r.json()
    if body.get('code') != 200 or not isinstance(body.get('data'), list):
        raise RuntimeError('未识别商品分类')
    if any((not isinstance(x, dict) or not x.get('childProductId') or (not x.get('childProductName')) for x in body['data'])):
        raise RuntimeError('商品分类字段异常')
    return body['data']

def categories(parent=''):
    if not isinstance(parent, str) or len(parent) > 30:
        raise ValueError('上级分类编号无效')
    with requests.Session() as session:
        _auth(session)
        root = _categories(session)
        if parent and (not any((x['childProductId'] == parent for x in root))):
            raise ValueError('上级编号不在原站 HS 顶层分类内')
        items = _categories(session, parent) if parent else root
    return {'source': '国研网国际贸易研究及决策支持系统', 'institution': '浙江大学图书馆（校园 IP）', 'dimension': 'HS', 'parent': parent or None, 'items': [{'id': x.get('showProductId') or x['childProductId'], 'tree_id': x['childProductId'], 'name': x['childProductName']} for x in items], 'note': '原站顶层分类或指定顶层分类的下一级选项；检索编号 id 与展开树的 tree_id 可能不同，具体数据使用权限以原站为准。'}

def monthly(year, month, product='T1', flow='import', parent=''):
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100) or isinstance(month, bool) or (not isinstance(month, int)) or (not 1 <= month <= 12):
        raise ValueError('请输入有效年份和月份')
    if not isinstance(product, str) or not product or len(product) > 30 or (not isinstance(parent, str)) or (len(parent) > 30) or (flow not in ('import', 'export')):
        raise ValueError('商品编号或流向无效')
    with requests.Session() as session:
        _auth(session)
        root = _categories(session)
        if parent and (not any((x['childProductId'] == parent for x in root))):
            raise ValueError('上级编号不在原站 HS 顶层分类内')
        options = _categories(session, parent) if parent else root
        matches = [x for x in options if (x.get('showProductId') or x.get('childProductId')) == product]
        if len(matches) != 1:
            raise ValueError('商品编号不在原站指定 HS 分类内')
        r = session.get(BASE + '/common/yearData', headers={'api-version': 'V2'}, timeout=20)
        r.raise_for_status()
        dates = r.json()
        if dates.get('code') != 200 or not isinstance(dates.get('data', {}).get('tradeIndexChinaMonth'), list):
            raise RuntimeError('未识别可选月份')
        allowed = dates['data']['tradeIndexChinaMonth']
        if not any((str(x.get('year')) == str(year) and str(month) in [str(z) for z in x.get('months', [])] for x in allowed)):
            raise ValueError('该月不在站方提供的中国月度指数时间范围内')
        indicators = INDICATORS if flow == 'import' else EXPORT_INDICATORS
        payload = {'year': str(year), 'endYear': str(year), 'startMonth': str(month), 'endMonth': str(month), 'ioreId': '1' if flow == 'import' else '0', 'dimensionType': '1', 'productId': product, 'indicatorId': indicators, 'pageNum': 1, 'pageSize': 15}
        r = session.post(BASE + '/table/unAuth/chinaGoodsTradeIndicator', params={'productId': '0'}, json=payload, headers={'api-version': 'V1'}, timeout=30)
        r.raise_for_status()
        body = r.json()
    d = body.get('data') if isinstance(body, dict) else None
    if body.get('code') != 200 or not isinstance(d, dict) or (not isinstance(d.get('records'), list)):
        raise RuntimeError('国研网指数响应异常')
    rows = d['records']
    expected = set(indicators.split(','))
    flow_name = '进口' if flow == 'import' else '出口'
    if len(rows) != 6 or {x.get('indicatorId') for x in rows} != expected or any((x.get('productId') != product or x.get('ioreName') != flow_name or x.get('timeId') != f'{year}年{month:02d}月' for x in rows)):
        raise RuntimeError('指标、商品、流向或月份与请求不符')
    return {'source': '国研网国际贸易研究及决策支持系统', 'institution': '浙江大学图书馆（校园 IP）', 'scope': '中国货物贸易：HS 顶层类或其下一级，单月指数', 'parent': parent or None, 'product': product, 'product_name': matches[0].get('childProductName'), 'flow': flow_name, 'year': year, 'month': month, 'upstream_pagination': {k: d.get(k) for k in ('total', 'size', 'current')}, 'records': rows, 'note': '保留站方指标名称、基期、单位和原值；价格、数量、价值及同比与环比不可混同。上游 total 可能为0但 records 非空，不将 total 作为记录数；数据编制方和修订口径应在原站核实。'}
