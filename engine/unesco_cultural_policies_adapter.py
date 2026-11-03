"""UNESCO 2005 Convention parties' cultural policies and measures."""
import release_runtime
import re
import requests
BASE = 'https://data.unesco.org/api/explore/v2.1/catalog/datasets/dce002'
FIELDS = 'uuid,title_en,date,countries,country_title_en,goal,sdg,area_monitoring,cultural_domain,agency_implementation,main_feature,results,financial_ressources,evaluation,cso,createdat,updatedat,publishedat,document,website'
NOTES = ['These entries are submitted through periodic reports by Parties to the UNESCO 2005 Convention; claims, results and opinions are those of submitters, not independently verified outcomes or UNESCO endorsements.', 'The source date is a report-related field and may be year-only; it does not by itself establish adoption, legal effect, or present implementation status.', 'Publication and update timestamps refer to the current platform and do not establish availability at an earlier cutoff. Policies, funding and responsible agencies can change.', 'Search matches source English titles, using UNESCO full-text search. Raw reported budgets and units are not converted. Dataset metadata states CC BY-SA 4.0; underlying documents may have separate terms.']

def _get(url, **kwargs):
    r = requests.get(url, timeout=45, **kwargs)
    r.raise_for_status()
    return r.json()

def search(keyword='', country='', limit=10, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 80 or (keyword and (not re.fullmatch('[A-Za-z0-9 \\-]+', keyword))) or (not isinstance(country, str)) or (country and (not re.fullmatch('[A-Za-z]{2}', country))) or (type(limit) is not int) or (not 1 <= limit <= 100) or (type(offset) is not int) or (not 0 <= offset <= 9900):
        raise ValueError('Invalid search parameters')
    m = _get(BASE)
    meta = m.get('metas', {}).get('default', {})
    p = {'select': FIELDS, 'limit': limit, 'offset': offset, 'order_by': 'uuid'}
    clauses = []
    if country:
        clauses.append("countries = '" + country.upper() + "'")
    if keyword:
        clauses.append("search(title_en, '" + keyword + "')")
    if clauses:
        p['where'] = ' AND '.join(clauses)
    j = _get(BASE + '/records', params=p)
    if not isinstance(j, dict) or type(j.get('total_count')) is not int or (not isinstance(j.get('results'), list)) or (len(j['results']) > limit):
        raise ValueError('Unexpected UNESCO result')
    if country and any((r.get('countries') != country.upper() for r in j['results'])):
        raise ValueError('Record outside requested country')
    return {'source': BASE + '/records', 'page': 'https://data.unesco.org/explore/dataset/dce002/', 'metadata': {'title': meta.get('title'), 'description': meta.get('description'), 'license': meta.get('license'), 'data_processed': meta.get('data_processed')}, 'query': {'keyword': keyword, 'country': country.upper(), 'limit': limit, 'offset': offset}, 'total_matching': j['total_count'], 'notes': NOTES, 'records': j['results']}
