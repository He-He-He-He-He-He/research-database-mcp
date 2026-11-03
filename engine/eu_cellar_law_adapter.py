"""EU Publications Office CELLAR legal metadata by exact CELEX ID."""
import release_runtime
import argparse, json, re
import requests
URL = 'https://publications.europa.eu/webapi/rdf/sparql'
PREFIX = 'PREFIX cdm: <http://publications.europa.eu/ontology/cdm#> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> '

def _get(q):
    with requests.get(URL, params={'query': q, 'format': 'application/sparql-results+json'}, timeout=35, stream=True, headers={'Accept': 'application/sparql-results+json', 'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        n = 0
        for c in r.iter_content(65536):
            n += len(c)
            if n > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            parts.append(c)
        d = json.loads(b''.join(parts))
    if not isinstance(d.get('results', {}).get('bindings'), list):
        raise ValueError('unexpected SPARQL response')
    return d['results']['bindings']

def lookup(celex, language='ENG'):
    if not re.fullmatch('[0-9A-Z]{8,30}', celex) or not re.fullmatch('[A-Z]{3}', language):
        raise ValueError('invalid CELEX or language code')
    selector = '?s cdm:resource_legal_id_celex "' + celex + '"^^xsd:string . '
    meta = _get(PREFIX + 'SELECT ?s ?p ?o WHERE { ' + selector + '?s ?p ?o } LIMIT 200')
    titles = _get(PREFIX + 'SELECT ?title WHERE { ' + selector + '?e cdm:expression_belongs_to_work ?s ; cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/' + language + '> ; cdm:expression_title ?title } LIMIT 10')
    return {'source': URL, 'celex': celex, 'language': language, 'titles': titles, 'metadata': meta, 'metadata_limit': 200, 'official_landing': 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:' + celex, 'note': 'Metadata can include multiple dates and versions; check legal status and authoritative text. Output is bounded.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('celex')
    p.add_argument('--language', default='ENG')
    a = p.parse_args()
    print(json.dumps(lookup(a.celex, a.language), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
