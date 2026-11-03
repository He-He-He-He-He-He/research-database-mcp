"""UNCTADstat port liner shipping connectivity index (quarterly)."""
import release_runtime
import re
import unctadstat_datacentre_trade_adapter as dc
REPORT = 'US.PLSCI'
NOTE = 'UNCTAD port liner shipping connectivity index based on MDS Transmodal scheduled container liner services. Port index uses average global PORT connectivity in Q1 2023 = 100 after the 2024 rescaling, not the country index base. It is not traffic volume, vessel calls, cost, shipping times or proof of CBD connectivity. Data are periodically revised; a current reading cannot establish what was published at a past date. Keep missing/footnote fields and check metadata.'

def _version():
    hits = [x for x in dc._reports() if x.get('name') == REPORT]
    if len(hits) != 1 or type(hits[0].get('version')) is not int:
        raise ValueError('cannot resolve report version')
    return hits[0]

def ports(keyword, limit=20, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 80:
        raise ValueError('keyword required')
    if type(limit) is not int or not 1 <= limit <= 100 or type(offset) is not int or (offset < 0):
        raise ValueError('invalid pagination')
    r = _version()
    v = r['version']
    term = keyword.strip().replace("'", "''")
    url, data = dc._get(f'/datamart-api/{REPORT}/{v}/Ports', {'$filter': f"contains(Label,'{term}')", '$count': 'true', '$top': limit, '$skip': offset, 'culture': 'en'})
    if not isinstance(data, dict) or type(data.get('@odata.count')) is not int or (not isinstance(data.get('value'), list)) or (len(data['value']) > limit) or (offset + len(data['value']) > max(offset, data['@odata.count'])):
        raise ValueError('invalid port catalogue')
    if any((not isinstance(x, dict) or not x.get('Code') or keyword.strip().casefold() not in str(x.get('Label', '')).casefold() for x in data['value'])):
        raise ValueError('port filter not honored')
    return {'source': url, 'version': v, 'total': data['@odata.count'], 'offset': offset, 'items': data['value'], 'note': NOTE}

def query(port, year, quarter):
    if not isinstance(port, str) or not re.fullmatch('[A-Z0-9]{5}', port):
        raise ValueError('port code must be 5 uppercase letters/digits')
    if type(year) is not int or not 2006 <= year <= 2100:
        raise ValueError('invalid year')
    if type(quarter) is not int or quarter not in (1, 2, 3, 4):
        raise ValueError('quarter must be 1..4')
    r = _version()
    v = r['version']
    q = f'{year}Q0{quarter}'
    _, meta = dc._get(f'/api/datacenter/reports/{REPORT}/info/{v}')
    url, data = dc._get(f'/datamart-api/{REPORT}/{v}/Facts', {'$filter': f"Quarter/Code eq '{q}' and Port/Code eq '{port}'", '$count': 'true', '$top': 5, 'culture': 'en'})
    if not isinstance(meta, dict) or meta.get('name') != REPORT or meta.get('version') != v:
        raise ValueError('unexpected metadata')
    if not isinstance(data, dict) or type(data.get('@odata.count')) is not int or (not isinstance(data.get('value'), list)) or (data['@odata.count'] != len(data['value'])) or (len(data['value']) > 1):
        raise ValueError('invalid or incomplete result')
    for row in data['value']:
        if row.get('Port', {}).get('Code') != port or row.get('Quarter', {}).get('Code') != q:
            raise ValueError('out-of-filter row')
    return {'source': url, 'report': REPORT, 'version': v, 'report_last_updated': r.get('lastUpdatedDate'), 'total': data['@odata.count'], 'items': data['value'], 'metadata': meta, 'note': NOTE}
