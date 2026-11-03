"""Sri Lanka Department of Census and Statistics NADA survey metadata catalogue."""
import release_runtime
import json
import re
from urllib.parse import quote
import requests
BASE = 'https://nada.statistics.gov.lk/index.php/api/catalog/'

def _get(path, params=None):
    with requests.get(BASE + path, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        body = r.raw.read(5000001, decode_content=True)
    if len(body) > 5000000:
        raise ValueError('response exceeds size limit')
    data = json.loads(body)
    if not isinstance(data, dict):
        raise ValueError('unexpected response')
    return data

def search(keyword='', *, page=1, limit=20):
    if not isinstance(keyword, str) or len(keyword) > 150 or any((type(x) is not int for x in (page, limit))) or (not 1 <= page <= 1000) or (not 1 <= limit <= 50):
        raise ValueError('invalid keyword or pagination')
    result = _get('search', {'sk': keyword, 'ps': limit, 'page': page}).get('result')
    if not isinstance(result, dict) or not isinstance(result.get('rows'), list):
        raise ValueError('unexpected survey catalog response')
    return {'source': 'Sri Lanka Department of Census and Statistics NADA catalogue', 'source_url': BASE + 'search', 'result': result, 'note': 'Catalog search indexes metadata beyond titles; matched terms may occur in descriptions. Open metadata is not proof of microdata access. Verify titles and collection dates independently: observation, metadata creation and publication dates are distinct. Creation date is not necessarily original publication date.'}

def metadata(idno):
    if not isinstance(idno, str) or not re.fullmatch('[A-Za-z0-9_. -]{1,200}', idno):
        raise ValueError('invalid source survey ID')
    response = _get(quote(idno, safe=''))
    item = response.get('dataset')
    if response.get('status') != 'success' or not isinstance(item, dict) or item.get('idno') != idno:
        raise ValueError('unexpected or unmatched survey metadata')
    return {'source': 'Sri Lanka Department of Census and Statistics NADA catalogue', 'source_url': BASE + quote(idno, safe=''), 'dataset': item, 'note': 'Preserve original title, years, metadata and access terms; compare the original survey dates and documentation. Current catalog entries do not establish historical availability.'}
