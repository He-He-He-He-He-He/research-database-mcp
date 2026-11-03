"""Getty Vocabularies SPARQL exact English preferred-label identification."""
import release_runtime
import json
import requests
URL = 'https://vocab.getty.edu/sparql'

def exact_english_label(label, limit=10):
    if not isinstance(label, str) or not label.strip() or len(label) > 100 or any((ord(c) < 32 for c in label)):
        raise ValueError('label must be 1–100 printable characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20):
        raise ValueError('limit must be 1–20')
    literal = json.dumps(label.strip(), ensure_ascii=True)
    query = 'PREFIX gvp: <http://vocab.getty.edu/ontology#> PREFIX xl: <http://www.w3.org/2008/05/skos-xl#> SELECT DISTINCT ?s WHERE { ?s gvp:prefLabelGVP/xl:literalForm ' + literal + '@en } LIMIT ' + str(limit)
    r = requests.get(URL, params={'query': query, 'format': 'json'}, headers={'Accept': 'application/sparql-results+json'}, timeout=30)
    r.raise_for_status()
    if len(r.content) > 1000000:
        raise ValueError('Unexpected response size')
    payload = r.json()
    bindings = payload.get('results', {}).get('bindings')
    if not isinstance(bindings, list) or any(('s' not in x or x['s'].get('type') != 'uri' for x in bindings)):
        raise ValueError('Unexpected SPARQL response')
    return {'source_url': URL, 'documentation': 'https://www.getty.edu/research-conservation/tools-databases/vocabularies/data-services/', 'label': label.strip(), 'language': 'en', 'items': [x['s']['value'] for x in bindings], 'possibly_truncated': len(bindings) == limit, 'note': 'Exact Getty preferred label only, case and language sensitive; no matches does not exclude alternative labels. Results can cover AAT, TGN or ULAN. Attribution required under ODC-By 1.0.'}
