"""Public EU Publications Office CELLAR legal-record discovery and details."""
import release_runtime
import argparse
import datetime
import json
import re
import subprocess
import threading
import time
from urllib.parse import urlencode
BASE = 'https://publications.europa.eu/webapi/rdf/sparql'
PREFIX = 'PREFIX cdm: <http://publications.europa.eu/ontology/cdm#> PREFIX owl: <http://www.w3.org/2002/07/owl#> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> '
_lock = threading.Lock()
_last = 0.0

def _query(query):
    global _last
    url = BASE + '?' + urlencode({'query': PREFIX + query, 'format': 'application/sparql-results+json'})
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', url], capture_output=True, text=True, check=True)
    data = json.loads(r.stdout)
    bindings = data.get('results', {}).get('bindings')
    if not isinstance(bindings, list):
        raise ValueError('unexpected CELLAR response')
    return bindings

def documents_on(date, limit=10):
    try:
        if not isinstance(date, str) or datetime.date.fromisoformat(date).isoformat() != date:
            raise ValueError
    except ValueError:
        raise ValueError('date must be YYYY-MM-DD') from None
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit must be 1–50')
    return _query('SELECT DISTINCT ?id WHERE { ?w cdm:work_date_document "' + date + '"^^xsd:date ; cdm:resource_legal_id_celex ?id . } LIMIT ' + str(limit))

def legal_record(celex):
    if not isinstance(celex, str) or not re.fullmatch('[A-Z0-9/()_-]{5,40}', celex):
        raise ValueError('invalid CELEX identifier')
    iri = 'http://publications.europa.eu/resource/celex/' + celex
    return _query('SELECT DISTINCT ?title ?date WHERE { ?w owl:sameAs <' + iri + '> . ?e cdm:expression_belongs_to_work ?w ; cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/ENG> ; cdm:expression_title ?title . OPTIONAL { ?w cdm:work_date_document ?date } } LIMIT 10')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('date')
    s.add_argument('date')
    s.add_argument('--limit', type=int, default=10)
    d = sub.add_parser('detail')
    d.add_argument('celex')
    a = p.parse_args()
    result = documents_on(a.date, a.limit) if a.command == 'date' else legal_record(a.celex)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
