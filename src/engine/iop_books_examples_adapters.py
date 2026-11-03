"""Two verified public Crossref examples from IOP series named by ZJU library."""
import release_runtime
from urllib.parse import quote
import requests
_ROWS = [('Time and Time Again', '10.1088/978-0-7503-1194-6', 'IOP Expanding Physics', 'https://researchers.mq.edu.au/en/publications/time-and-time-again-determination-of-longitude-at-sea-in-the-17th/'), ('Fluids in Porous Media', '10.1088/978-1-6817-4297-7', 'IOP Concise Physics', 'https://research.tue.nl/en/publications/fluids-in-porous-media-transport-and-phase-changes/')]

def lookup(keyword):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('keyword must be non-empty')
    rows = [x for x in _ROWS if keyword.casefold().strip() in (x[0] + ' ' + x[1] + ' ' + x[2]).casefold()]
    items = []
    for title, doi, series, series_source in rows:
        r = requests.get('https://api.crossref.org/works/' + quote(doi, safe='/'), timeout=30)
        r.raise_for_status()
        metadata = r.json().get('message', {})
        if metadata.get('DOI', '').casefold() != doi.casefold():
            raise RuntimeError('Unexpected Crossref DOI')
        items.append({'series': series, 'series_source': series_source, 'metadata': metadata})
    return {'source': 'Crossref public metadata', 'keyword': keyword, 'items': items, 'library_info': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1453', 'note': 'Only two independently identified examples of the series named by the library; institutional entitlements and full text are not verified.'}
