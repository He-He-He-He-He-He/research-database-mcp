"""FAO/WHO Codex Alimentarius current standards directory."""
import release_runtime
from urllib.parse import urljoin, urlparse
import requests
PAGE = 'https://codex.fao.org/codex-texts/find-a-codex-text'
API = PAGE + '/LoadFilter/'
NOTES = ['Codex standards and related texts are voluntary; domestic legal effect depends on applicable national legislation or regulation.', 'LastModified is a source-reported year of latest modification, not the original adoption date or a complete revision history.', 'This is the current directory and current linked texts; it does not establish what a text said or whether it was available at an earlier cutoff.', 'Language links may be absent. Committee codes and type numbers are retained as supplied by the source.']

def search(keyword='', limit=20, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 100) or (type(offset) is not int) or (offset < 0):
        raise ValueError('Invalid keyword or pagination')
    p = {'searchModel': {'ItemsPerPage': 0, 'Popularity': None, 'Region': '', 'CategoryIds': []}}
    r = requests.post(API, json=p, timeout=60)
    r.raise_for_status()
    j = r.json()
    if not isinstance(j, dict) or not isinstance(j.get('Standards'), list) or type(j.get('TotalCount')) is not int or (len(j['Standards']) != j['TotalCount']):
        raise ValueError('Incomplete Codex directory')
    rows = []
    for item in j['Standards']:
        if not isinstance(item, dict) or not isinstance(item.get('Reference'), str) or (not isinstance(item.get('Title'), str)):
            raise ValueError('Unexpected Codex record')
        links = {}
        for lang, link in (item.get('Links') or {}).items():
            if link is None:
                links[lang] = None
                continue
            u = urljoin(PAGE, link)
            p = urlparse(u)
            if p.scheme != 'https' or p.hostname != 'codex.fao.org' or (not p.path.startswith('/restapi/searchstandard/')):
                raise ValueError('Unexpected Codex document URL')
            links[lang] = u
        row = {**item, 'Links': links}
        if keyword.casefold() in ' '.join((str(item.get(k) or '') for k in ('Reference', 'Title', 'Committee'))).casefold():
            rows.append(row)
    return {'source': API, 'page': PAGE, 'source_total': j['TotalCount'], 'total_matching': len(rows), 'offset': offset, 'notes': NOTES, 'records': rows[offset:offset + limit]}
