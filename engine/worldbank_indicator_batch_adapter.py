"""World Bank Indicators API V2, bounded multiple economies and series."""
import release_runtime
import re, requests
BASE = 'https://api.worldbank.org/v2/country/'

def query(source, countries, indicators, start, end):
    if not isinstance(source, str) or not re.fullmatch('\\d{1,4}', source):
        raise ValueError('source must be numeric ID')
    if not isinstance(countries, list) or not 1 <= len(countries) <= 10 or any((not isinstance(c, str) or not re.fullmatch('[A-Z0-9]{3}', c) for c in countries)) or (len(set(countries)) != len(countries)):
        raise ValueError('supply 1–10 distinct World Bank economy codes')
    if not isinstance(indicators, list) or not 1 <= len(indicators) <= 10 or any((not isinstance(i, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,64}', i) for i in indicators)) or (len(set(indicators)) != len(indicators)):
        raise ValueError('supply 1–10 distinct indicator codes')
    if any((type(x) is not int for x in (start, end))) or not 1900 <= start <= end <= 2100 or end - start > 50:
        raise ValueError('invalid range, at most 51 years')
    url = BASE + ';'.join(countries) + '/indicator/' + ';'.join(indicators)
    params = {'source': source, 'date': f'{start}:{end}', 'format': 'json', 'per_page': 500}
    rows = []
    total = None
    pages = None
    updated = None
    seen = set()
    urls = []
    for page in range(1, 21):
        with requests.get(url, params={**params, 'page': page}, timeout=(10, 25), stream=True, allow_redirects=False) as r:
            r.raise_for_status()
            urls.append(r.url)
            body = bytearray()
            for b in r.iter_content(65536):
                body.extend(b)
                if len(body) > 8000000:
                    raise ValueError('response exceeds 8 MB')
        try:
            j = __import__('json').loads(body)
        except ValueError:
            raise RuntimeError('World Bank returned non-JSON or error response') from None
        if not isinstance(j, list) or len(j) != 2 or (not isinstance(j[0], dict)) or (not isinstance(j[1], list)):
            raise RuntimeError('World Bank returned error or unexpected response')
        meta, items = j
        actual = meta.get('page')
        pg = meta.get('pages')
        n = meta.get('total')
        if type(actual) is not int or actual != page or type(pg) is not int or (not 1 <= pg <= 20) or (type(n) is not int) or (n < 0) or (len(items) > 500):
            raise RuntimeError('invalid or excessive pagination')
        if total is None:
            total = n
            pages = pg
            updated = meta.get('lastupdated')
        if n != total or pg != pages or meta.get('lastupdated') != updated:
            raise RuntimeError('dataset changed during pagination; retry')
        for x in items:
            code = x.get('countryiso3code')
            ind = (x.get('indicator') or {}).get('id')
            year = x.get('date')
            if code not in countries or ind not in indicators or (not isinstance(year, str)) or (not re.fullmatch('\\d{4}', year)) or (not start <= int(year) <= end):
                raise RuntimeError('response outside requested dimensions or annual period')
            key = (code, ind, year)
            if key in seen:
                raise RuntimeError('duplicate observation identity across pages')
            seen.add(key)
            rows.append(x)
        if page == pages:
            break
    else:
        raise RuntimeError('more than 20 pages; narrow query')
    if len(rows) != total:
        raise RuntimeError('source count differs from collected rows')
    return {'source_url': url, 'request': params, 'page_urls': urls, 'source_id': source, 'last_updated': updated, 'count': len(rows), 'observations': rows, 'note': '来源按所选数据库提供年度原始数值、空值、单位及状态；不同指标单位与统计口径不可混同。分页核对总数及重复，但多页并非原子快照；指标定义及预测状态需结合来源元数据。'}
