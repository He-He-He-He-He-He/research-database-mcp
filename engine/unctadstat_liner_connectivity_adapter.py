"""UNCTADstat quarterly liner shipping connectivity (LSCI)."""
import release_runtime
import re
import unctadstat_datacentre_trade_adapter as dc
REPORT = 'US.LSCI'
NOTE = 'Quarterly country liner shipping connectivity index from UNCTAD, based on MDS Transmodal shipping schedules. The current series was rescaled in 2024 to global country average Q1 2023=100; historical values can be revised. From 2006–2022 one observation per quarter is used; from 2023 some components are monthly averaged. Index (M6047), year-on-year growth (M4023), previous-quarter growth (M4024), and quarterly rank (M8004) have different meanings and units; do not add. The index is not cargo throughput, direct trade value, shipping cost or CBD-specific access. Source and footnotes must be reviewed; empty is not zero.'

def query(economy, year, quarter):
    if not isinstance(economy, str) or not re.fullmatch('\\d{1,4}', economy):
        raise ValueError('economy must be UNCTAD numeric code')
    if type(year) is not int or not 2006 <= year <= 2100:
        raise ValueError('year must be 2006..2100')
    if type(quarter) is not int or quarter not in (1, 2, 3, 4):
        raise ValueError('quarter must be 1..4')
    hits = [x for x in dc._reports() if x.get('name') == REPORT]
    if len(hits) != 1 or type(hits[0].get('version')) is not int:
        raise ValueError('cannot resolve report version')
    v = hits[0]['version']
    _, meta = dc._get('/api/datacenter/reports/' + REPORT + '/info/' + str(v))
    q = f'{year}Q0{quarter}'
    url, r = dc._get('/datamart-api/' + REPORT + '/' + str(v) + '/Facts', {'$filter': f"Quarter/Code eq '{q}' and Economy/Code eq '{economy}'", '$count': 'true', '$top': 5, 'culture': 'en'})
    if not isinstance(r, dict) or type(r.get('@odata.count')) is not int or (not isinstance(r.get('value'), list)) or (r['@odata.count'] != len(r['value'])) or (len(r['value']) > 1):
        raise ValueError('unexpected or incomplete response')
    for row in r['value']:
        if row.get('Quarter', {}).get('Code') != q or row.get('Economy', {}).get('Code') != economy:
            raise ValueError('out-of-filter record')
    if not isinstance(meta, dict) or meta.get('name') != REPORT or meta.get('version') != v:
        raise ValueError('unexpected report metadata')
    return {'source': url, 'report': REPORT, 'version': v, 'report_last_updated': hits[0].get('lastUpdatedDate'), 'total': r['@odata.count'], 'rows': r['value'], 'report_metadata': meta, 'note': NOTE}
