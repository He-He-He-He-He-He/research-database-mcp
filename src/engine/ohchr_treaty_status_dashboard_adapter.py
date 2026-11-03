"""OHCHR public dashboard data for the status of 18 human-rights instruments."""
import release_runtime
import concurrent.futures, re
import requests
BASE = 'https://indicators.ohchr.org/webapi/dashboarddata/'
CATALOG = 'https://indicators.ohchr.org/'
NOTE = '联合国人权高专办 18 项人权文书状态看板的公开数据，保留原字段、状态代码、声明和日期，不将签署等同批准或加入。源数据中的 1753-01-01 或 01/01/1753 是异常占位值，不能当作真实签署、生效或退出日期。该接口只列出返回的记录，不以缺行推断国家未采取行动；当前结果不是历史时点快照。批准与条约生效不同，保留、声明及后续退出可能改变适用范围；法律结论须核对联合国条约保存机关原始记录。'

def _get(path, session=None):
    with (session or requests).get(BASE + path, headers={'Accept': 'application/json', 'User-Agent': 'PersonalResearchToolkit/1.0'}, timeout=45, stream=True) as r:
        r.raise_for_status()
        b = bytearray()
        for chunk in r.iter_content(65536):
            b.extend(chunk)
            if len(b) > 20 * 1024 * 1024:
                raise ValueError('OHCHR 响应超过 20 MiB')
    import json
    try:
        d = json.loads(b)
    except ValueError as exc:
        raise ValueError('OHCHR 未返回 JSON') from exc
    if not isinstance(d, list):
        raise ValueError('OHCHR 返回格式异常')
    return d

def country(code, session=None):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z]{3}', code):
        raise ValueError('请输入三字母国家代码，如 EGY')
    paths = ['GetCountries', 'GetRatifications', 'GetCountryRatifications']
    if session is None:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            countries, treaties, records = list(pool.map(_get, paths))
    else:
        countries, treaties, records = [_get(x, session) for x in paths]
    found = [x for x in countries if str(x.get('AreaId', '')).upper() == code.upper()]
    if len(found) != 1:
        raise ValueError('国家代码未找到或并非唯一；请核对看板代码')
    matches = [x for x in records if x.get('CountryId') == found[0].get('Id')]
    tids = {x.get('RatificationId') for x in matches}
    defs = [x for x in treaties if x.get('Id') in tids]
    return {'source': 'OHCHR Status of Ratification Interactive Dashboard', 'source_urls': [BASE + x for x in paths], 'dashboard': CATALOG, 'note': NOTE, 'country': found[0], 'returned_record_count': len(matches), 'treaty_definitions': defs, 'records': matches}
