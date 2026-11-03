"""NASA Exoplanet Archive TAP: default planetary solutions for an exact host."""
import release_runtime
import re
import requests
URL = 'https://exoplanetarchive.ipac.caltech.edu/TAP/sync'
DOC = 'https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html'

def host(hostname, limit=30):
    if not isinstance(hostname, str) or not re.fullmatch('[A-Za-z0-9 ._+\\-]{1,80}', hostname) or (not hostname.strip()):
        raise ValueError('hostname must use letters, digits, spaces, dot, underscore, plus or hyphen')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    fields = 'pl_name,hostname,discoverymethod,disc_year,pl_orbper,pl_orbpererr1,pl_orbpererr2,pl_orbperlim,pl_rade,pl_radeerr1,pl_radeerr2,pl_radelim,pl_bmasse,pl_bmasseerr1,pl_bmasseerr2,pl_bmasselim,pl_bmassprov,pl_controv_flag,pl_refname'
    q = f"select top {limit} {fields} from ps where default_flag=1 and hostname='{hostname.strip()}' order by pl_name"
    r = requests.get(URL, params={'query': q, 'format': 'json'}, timeout=30)
    r.raise_for_status()
    if len(r.content) > 3000000:
        raise ValueError('Unexpected response size')
    data = r.json()
    if not isinstance(data, list) or any((not isinstance(x, dict) or x.get('hostname') != hostname.strip() for x in data)):
        raise ValueError('Unexpected TAP response')
    return {'source_url': r.url, 'documentation': DOC, 'host': hostname.strip(), 'items': data, 'possibly_truncated': len(data) == limit, 'note': 'Default literature solution per confirmed planet, not all published solutions. Orbital period in days, radius Earth radii, best mass Earth masses; inspect uncertainty, limits, mass provenance and controversial flags.'}
