"""SEC EDGAR companyconcept data for an exact XBRL taxonomy concept."""
import release_runtime
import re
import requests
DOC = 'https://www.sec.gov/search-filings/edgar-application-programming-interfaces'

def company_concept(cik, taxonomy, concept, user_agent, unit, limit=20):
    if not isinstance(cik, str) or not re.fullmatch('[0-9]{1,10}', cik) or int(cik) == 0:
        raise ValueError('cik must be 1–10 digits')
    if taxonomy not in ('us-gaap', 'ifrs-full', 'dei', 'srt'):
        raise ValueError('unsupported taxonomy')
    if not isinstance(concept, str) or not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,99}', concept):
        raise ValueError('invalid concept')
    if not isinstance(unit, str) or not re.fullmatch('[A-Za-z0-9/_-]{1,40}', unit):
        raise ValueError('invalid unit')
    if not isinstance(user_agent, str) or len(user_agent) > 200 or (not re.search('[^\\s@]+@[^\\s@]+\\.[^\\s@]+', user_agent)) or ('\n' in user_agent) or ('\r' in user_agent):
        raise ValueError('user_agent must identify client and contact email per SEC policy')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('limit must be 1–100')
    url = f'https://data.sec.gov/api/xbrl/companyconcept/CIK{cik.zfill(10)}/{taxonomy}/{concept}.json'
    r = requests.get(url, headers={'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate'}, timeout=40)
    r.raise_for_status()
    if len(r.content) > 10000000:
        raise ValueError('Unexpected response size')
    d = r.json()
    units = d.get('units')
    if not isinstance(units, dict) or any((not isinstance(v, list) for v in units.values())):
        raise ValueError('Unexpected response shape')
    rows = units.get(unit, [])
    return {'source_url': r.url, 'documentation': DOC, 'cik': d.get('cik'), 'entity_name': d.get('entityName'), 'taxonomy': d.get('taxonomy'), 'tag': d.get('tag'), 'label': d.get('label'), 'description': d.get('description'), 'unit': unit, 'available_units': list(units), 'source_count_in_unit': len(rows), 'items': rows[-limit:], 'note': 'Last source-order facts, not deduplicated or selected annual series; restatements and multiple reporting periods can coexist. Inspect form, filed, start, end, frame and accession.'}
