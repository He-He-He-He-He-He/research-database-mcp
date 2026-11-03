"""IFC advisory services project listings via WBG Finances One."""
import release_runtime
import re, requests
URL = 'https://datacatalogapi.worldbank.org/dexapps/fone/api/apiservice'
CATALOG = 'https://financesone.worldbank.org/ifc%20advisory%20services%20projects/DS00071'
NOTE = 'IFC advisory services projects, not investment or IBRD/IDA lending projects. Estimated total budget is in USD for all project-funded activities; it is not actual disbursement or an investment amount. World Bank country codes may differ from ISO. Server country filtering is not relied upon; bounded pages are retrieved and filtered locally. Preserve original statuses, dates and null values.'

def query(country, limit=50, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z0-9]{2,3}', country):
        raise ValueError('country must be a 2–3 character World Bank code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 200 or (not 0 <= offset <= 10000):
        raise ValueError('invalid pagination')
    rows = []
    total = None
    for skip in range(0, 100000, 1000):
        p = {'datasetId': 'DS00071', 'resourceId': 'RS00072', 'type': 'json', 'top': 1000, 'skip': skip}
        r = requests.get(URL, params=p, timeout=40)
        r.raise_for_status()
        j = r.json()
        if not isinstance(j, dict) or not isinstance(j.get('count'), int) or (not isinstance(j.get('data'), list)):
            raise ValueError('unexpected response')
        if total is None:
            total = j['count']
        elif total != j['count']:
            raise ValueError('dataset changed during pagination; retry')
        page = j['data']
        rows.extend(page)
        if len(rows) >= total:
            break
        if not page or len(page) > 1000:
            raise ValueError('incomplete pagination')
    else:
        raise ValueError('dataset exceeds pagination limit')
    if len(rows) != total:
        raise ValueError('record count mismatch')
    matches = [x for x in rows if isinstance(x.get('wb_country_code'), str) and x['wb_country_code'].upper() == country.upper()]
    return {'source': URL, 'catalog': CATALOG, 'dataset_total': total, 'wb_country_code': country.upper(), 'matched': len(matches), 'offset': offset, 'records': matches[offset:offset + limit], 'note': NOTE}
