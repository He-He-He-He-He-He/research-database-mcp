"""Three independently identified ACM Books Collection 1 records, not a complete list."""
import release_runtime
import requests
from urllib.parse import quote
_ROWS = [('Shared-Memory Parallelism Can Be Simple, Fast, and Scalable', '10.1145/3018787', 'https://books.google.com/books?id=8zVSMQAACAAJ'), ('Frontiers of Multimedia Research', '10.1145/3122865', 'https://books.google.com/books/about/Frontiers_of_Multimedia_Research.html?id=PEiGswEACAAJ'), ('The Handbook of Multimodal-Multisensor Interfaces: Language Processing, Software, Commercialization, and Emerging Directions - Volume 3', '10.1145/3233795', 'https://books.google.com/books?id=kAABxwEACAAJ')]

def lookup(keyword):
    if not isinstance(keyword, str) or not keyword.strip():
        raise ValueError('keyword must be non-empty')
    matches = [x for x in _ROWS if keyword.casefold().strip() in (x[0] + ' ' + x[1]).casefold()]
    records = []
    for title, doi, collection_source in matches:
        r = requests.get('https://api.crossref.org/works/' + quote(doi, safe='/'), timeout=30)
        r.raise_for_status()
        d = r.json().get('message', {})
        if d.get('DOI', '').casefold() != doi.casefold():
            raise RuntimeError('Crossref DOI mismatch')
        records.append({'doi': doi, 'collection_source': collection_source, 'metadata': d})
    return {'source': 'Crossref public metadata', 'keyword': keyword, 'items': records, 'library_info': 'https://libdb.zju.edu.cn/s/lib/libtb/show/1375', 'note': 'Only three individually identified Collection 1 examples, not the complete 25-book set; library institutional authentication and full-text access were not tested.'}
