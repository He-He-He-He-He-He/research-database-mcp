"""UNCTADstat annual bilateral creative goods trade (Comtrade-derived)."""
import release_runtime
import re
from unctadstat_datacentre_trade_adapter import _get, _reports, ROOT, PAGE
REPORT = 'US.CreativeGoodsValue'

def trade(economy, partner, year, limit=20, offset=0):
    for name, value in [('economy', economy), ('partner', partner)]:
        if not isinstance(value, str) or not re.fullmatch('[0-9]{1,4}', value):
            raise ValueError(name + ' must be UNCTAD code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1900 <= year <= 2100):
        raise ValueError('invalid year')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('invalid pagination')
    hits = [r for r in _reports() if r.get('name') == REPORT]
    if len(hits) != 1 or not isinstance(hits[0].get('version'), int):
        raise ValueError('cannot resolve report version')
    version = hits[0]['version']
    _, meta = _get('/api/datacenter/reports/' + REPORT + '/info/' + str(version))
    params = {'$filter': f"Year eq {year} and Economy/Code eq '{economy}' and Partner/Code eq '{partner}'", '$count': 'true', '$top': limit, '$skip': offset, 'culture': 'en'}
    url, result = _get('/datamart-api/' + REPORT + '/' + str(version) + '/Facts', params)
    if not isinstance(result, dict) or not isinstance(result.get('value'), list) or (not isinstance(result.get('@odata.count'), int)):
        raise ValueError('unexpected facts response')
    for r in result['value']:
        if r.get('Year') != year or r.get('Economy', {}).get('Code') != economy or r.get('Partner', {}).get('Code') != partner:
            raise ValueError('out-of-filter data')
    return {'source': url, 'page': PAGE, 'version': version, 'report_last_updated': hits[0].get('lastUpdatedDate'), 'total': result['@odata.count'], 'offset': offset, 'rows': result['value'], 'report_metadata': meta, 'note': 'UNCTAD creative goods trade analytical classification based on UN Comtrade, not independent from it. M0100 is current US dollars; M5011, M5019, M5058 are percentages with different denominators. Product hierarchy and World partner totals overlap; HS versions differ across countries and time. Retain raw missing codes and footnotes.'}
