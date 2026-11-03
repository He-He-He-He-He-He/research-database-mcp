"""World Bank IEG project evaluation records via Finances One public API."""
import release_runtime
import requests
API = 'https://datacatalogapi.worldbank.org/dexapps/fone/api/apiservice'
PAGE = 'https://financesone.worldbank.org/d/DS00053'

def _page(skip):
    r = requests.get(API, params={'datasetId': 'DS00053', 'resourceId': 'RS00055', 'type': 'json', 'top': 1000, 'skip': skip}, timeout=40)
    r.raise_for_status()
    v = r.json()
    if not isinstance(v, dict) or not isinstance(v.get('count'), int) or (not isinstance(v.get('data'), list)):
        raise ValueError('unexpected response')
    return v

def search(country, limit=20, offset=0):
    if not isinstance(country, str) or not country.strip() or len(country) > 100:
        raise ValueError('invalid country')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    rows = []
    count = None
    for skip in range(0, 100000, 1000):
        r = _page(skip)
        count = r['count'] if count is None else count
        if r['count'] != count:
            raise ValueError('dataset changed while paging')
        batch = r['data']
        if not batch and len(rows) < count:
            raise ValueError('incomplete page')
        rows.extend(batch)
        if len(rows) >= count:
            break
    else:
        raise ValueError('dataset exceeds page limit')
    if len(rows) != count:
        raise ValueError('total count mismatch')
    chosen = [r for r in rows if isinstance(r, dict) and str(r.get('country', '')).casefold() == country.casefold()]
    return {'source': API, 'catalog': PAGE, 'dataset_count': count, 'country': country, 'matched': len(chosen), 'offset': offset, 'limit': limit, 'rows': chosen[offset:offset + limit], 'note': 'IEG evaluations concern evaluated World Bank projects, not all projects or all-country performance. Preserve original ordinal ratings, evaluation type, fiscal years and as-of date; ratings are not numerical scores. Exact local country filter can omit regional projects. API ignores country parameter, so all pages are read and checked before filtering.'}
