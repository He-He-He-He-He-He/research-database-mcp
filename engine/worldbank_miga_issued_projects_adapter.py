"""MIGA issued project guarantees via World Bank Finances One API."""
import release_runtime
import re, requests
URL = 'https://datacatalogapi.worldbank.org/dexapps/fone/api/apiservice'
CATALOG = 'https://financesone.worldbank.org/miga-issued-projects/DS00988'
NOTE = 'Issued MIGA guarantee projects, not all proposed MIGA projects or all foreign investments. Gross issued amount is source USD amount of guarantee issuance, not project investment, cash disbursement or an outstanding balance. Project IDs can recur across fiscal years and amounts may overlap, so do not sum without checking original records. The dataset page currently contains unrelated trust-fund description text; use API field labels and MIGA project links, verify source definitions. Server ignored country filter during testing: country filtering is performed locally after complete bounded pagination; blank amounts remain null.'

def query(country, limit=50, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z]{2}', country):
        raise ValueError('country must be two-letter host-country code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 200 or (not 0 <= offset <= 10000):
        raise ValueError('invalid pagination')
    rows = []
    total = None
    for skip in range(0, 100000, 1000):
        p = {'datasetId': 'DS00988', 'resourceId': 'RS00918', 'type': 'json', 'top': 1000, 'skip': skip}
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
        raise ValueError('dataset exceeds bounded pagination')
    if len(rows) != total:
        raise ValueError('record count mismatch')
    matches = [x for x in rows if isinstance(x.get('host_country_code'), str) and x['host_country_code'].upper() == country.upper()]
    return {'source': URL, 'catalog': CATALOG, 'dataset_total': total, 'host_country_code': country.upper(), 'matched': len(matches), 'offset': offset, 'records': matches[offset:offset + limit], 'note': NOTE}
