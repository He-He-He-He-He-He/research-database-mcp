"""World Bank IDA credits, grants and guarantees latest snapshot (Finances One)."""
import release_runtime
import re
import requests
API = 'https://datacatalogapi.worldbank.org/dexapps/fone/api/apiservice'
PAGE = 'https://financesone.worldbank.org/d/DS00001'

def _page(skip):
    r = requests.get(API, params={'datasetId': 'DS00001', 'resourceId': 'RS00001', 'type': 'json', 'top': 1000, 'skip': skip}, timeout=40)
    r.raise_for_status()
    v = r.json()
    if not isinstance(v, dict) or not isinstance(v.get('count'), int) or (not isinstance(v.get('data'), list)):
        raise ValueError('unexpected response')
    return v

def search(country, limit=20, offset=0):
    if not isinstance(country, str) or not re.fullmatch('[A-Za-z0-9]{2,3}', country):
        raise ValueError('country must be World Bank country code')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    rows = []
    count = None
    for skip in range(0, 100000, 1000):
        v = _page(skip)
        count = v['count'] if count is None else count
        if v['count'] != count:
            raise ValueError('dataset changed while paging')
        if not v['data'] and len(rows) < count:
            raise ValueError('incomplete page')
        rows.extend(v['data'])
        if len(rows) >= count:
            break
    else:
        raise ValueError('dataset exceeds page limit')
    if len(rows) != count:
        raise ValueError('total count mismatch')
    chosen = [r for r in rows if isinstance(r, dict) and str(r.get('country_code', '')).upper() == country.upper()]
    return {'source': API, 'catalog': PAGE, 'dataset_count': count, 'country_code': country.upper(), 'matched': len(chosen), 'offset': offset, 'limit': limit, 'rows': chosen[offset:offset + limit], 'note': 'Latest available IDA credits, grants and guarantees snapshot, not all World Bank lending. USD amounts use historical rates; currency_of_commitment is a separate field. Original principal, cumulative disbursement, undisbursed and outstanding balances are distinct and not additive. End-of-period denotes snapshot date. Country filter is local after all pages are checked; verify official source details.'}
