"""INFORM humanitarian risk public API, hosted by European Commission JRC."""
import release_runtime
import argparse, json, re
import requests
ROOT = 'https://drmkc.jrc.ec.europa.eu/inform-index/API/InformAPI/'

def _get(path, params=None):
    with requests.get(ROOT + path, params=params, timeout=35, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for c in r.iter_content(65536):
            size += len(c)
            if size > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            chunks.append(c)
        return {'source': r.url, 'data': json.loads(b''.join(chunks))}

def workflows(year):
    if not isinstance(year, int) or not 1900 <= year <= 2100:
        raise ValueError('invalid year')
    return _get('Workflows/GetByYear/' + str(year))

def indicator(code):
    if not re.fullmatch('[A-Za-z0-9_.-]{1,80}', code):
        raise ValueError('invalid indicator')
    return _get('Indicators/Index/' + code)

def scores(workflow, country, indicators):
    if not isinstance(workflow, int) or workflow < 1 or (not re.fullmatch('[A-Z]{3}', country)):
        raise ValueError('invalid workflow or ISO3 country')
    if not re.fullmatch('[A-Za-z0-9_.-]+(?:,[A-Za-z0-9_.-]+){0,19}', indicators) or len(indicators) > 400:
        raise ValueError('invalid indicator list')
    return _get('Countries/Scores/', {'WorkflowId': workflow, 'Iso3': country, 'IndicatorId': indicators})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    a = s.add_parser('workflows')
    a.add_argument('year', type=int)
    a = s.add_parser('indicator')
    a.add_argument('code')
    a = s.add_parser('scores')
    a.add_argument('workflow', type=int)
    a.add_argument('country')
    a.add_argument('indicators')
    a = p.parse_args()
    result = workflows(a.year) if a.cmd == 'workflows' else indicator(a.code) if a.cmd == 'indicator' else scores(a.workflow, a.country, a.indicators)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
