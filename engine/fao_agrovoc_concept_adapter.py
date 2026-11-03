"""Read one FAO AGROVOC concept and its links from the official JSON-LD API."""
import release_runtime
import argparse
import json
import re
import requests
BASE = 'http://aims.fao.org/aos/agrovoc/'
URL = 'https://agrovoc.fao.org/browse/rest/v1/data/'
LANGS = {'en', 'zh', 'ar', 'fr', 'ru', 'es'}

def concept(identifier):
    if not isinstance(identifier, str) or not re.fullmatch('c_[a-zA-Z0-9]+', identifier):
        raise ValueError('expected AGROVOC concept identifier such as c_33995')
    uri = BASE + identifier
    r = requests.get(URL, params={'uri': uri}, headers={'Accept': 'application/ld+json'}, timeout=25)
    r.raise_for_status()
    data = r.json()
    matches = [n for n in data.get('graph', []) if n.get('uri') == uri and n.get('type') == 'skos:Concept']
    if len(matches) != 1:
        raise ValueError('concept not found or unexpected response')
    node = matches[0]

    def array(x):
        return x if isinstance(x, list) else [x] if isinstance(x, dict) else []
    labels = {k: [x for x in array(node.get(k)) if x.get('lang') in LANGS] for k in ('prefLabel', 'altLabel')}
    links = {k: [x['uri'] for x in array(node.get(k)) if isinstance(x.get('uri'), str)] for k in ('broader', 'narrower', 'related', 'exactMatch', 'closeMatch')}
    return {'source': 'FAO AGROVOC', 'uri': uri, 'labels': labels, 'relations': links, 'modified': node.get('dct:modified')}
if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('identifier')
    print(json.dumps(concept(p.parse_args().identifier), ensure_ascii=False, indent=2))
