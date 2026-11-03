"""Green Climate Fund public portfolio page embedded data, filtered locally."""
import release_runtime
import json
import re
import requests
from bs4 import BeautifulSoup
URL = 'https://data.greenclimate.fund/public/data/projects'
DOC = 'https://data.greenclimate.fund/public'

def projects(country='', keyword='', status='', offset=0, limit=20):
    if country and (not re.fullmatch('[A-Za-z]{3}', country)):
        raise ValueError('country must be a three-letter ISO code')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('invalid offset')
    if not isinstance(limit, int) or isinstance(limit, bool) or (not 1 <= limit <= 100):
        raise ValueError('invalid limit')
    r = requests.get(URL, timeout=45)
    r.raise_for_status()
    s = BeautifulSoup(r.text, 'html.parser')
    node = s.find('script', id='__NEXT_DATA__')
    if node is None:
        raise ValueError('public page data not found')
    j = json.loads(node.string or node.get_text())
    result = j.get('props', {}).get('pageProps', {}).get('data', {})
    rows = result.get('data')
    if result.get('result') is not True or not isinstance(rows, list):
        raise ValueError('unexpected portfolio page format')

    def matches(row):
        if country and (not any((str(c.get('ISO3') or '').upper() == country.upper() for c in row.get('Countries') or []))):
            return False
        if keyword and keyword.strip().casefold() not in str(row.get('ProjectName') or '').casefold():
            return False
        if status and str(row.get('Type') or '').casefold() != status.strip().casefold():
            return False
        return True
    found = [row for row in rows if matches(row)]
    return {'source': URL, 'about': DOC, 'page_data_count': len(rows), 'total_matches': len(found), 'offset': offset, 'limit': limit, 'rows': found[offset:offset + limit], 'notes': ['This reads data embedded in the publicly accessible portfolio page; it is not the separate registered developer API.', 'TotalGCFBudgetUSD, TotalCoBudgetUSD and TotalBudgetUSD are distinct project-level funding amounts in USD and overlap; they are not amounts disbursed.', 'A project may list several countries; the full project value is not automatically allocated to each country. Type includes approved or cancelled records.', 'BMDate is board meeting date; ProjectLastModifiedOn is an update timestamp. Other indicators including lifetime CO2 and beneficiaries require their own definition and should not be treated automatically as realized impacts.', 'The page may change its data structure and freshness; empty or zero values retain original meaning and do not prove absence.']}
