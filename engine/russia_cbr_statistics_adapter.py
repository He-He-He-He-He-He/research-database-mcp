"""Bank of Russia official statistical data REST API."""
import release_runtime
import argparse, json
import requests
BASE = 'https://www.cbr.ru/dataservice'

def get(path, params=None):
    s = requests.Session()
    s.trust_env = False
    with s.get(BASE + path, params=params, timeout=40, stream=True) as r:
        r.raise_for_status()
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > 10000000:
                raise ValueError('Response exceeds 10 MB; narrow years')
        return (json.loads(buf), r.url)

def idcheck(value):
    if not 1 <= value <= 100000000:
        raise ValueError('Invalid identifier')
    return value

def publications():
    j, url = get('/publications')
    return {'source': url, 'items': j}

def datasets(publication):
    j, url = get('/datasets', {'publicationId': idcheck(publication)})
    return {'source': url, 'items': j}

def metadata(indicator):
    indicator = idcheck(indicator)
    description, u = get('/DatasetDescription', {'datasetId': indicator})
    measures, m = get('/measures', {'datasetId': indicator})
    return {'description_source': u, 'description': description, 'measures_source': m, 'measures': measures}

def years(indicator, measure=-1):
    idcheck(indicator)
    if measure != -1:
        idcheck(measure)
    j, url = get('/years', {'datasetId': indicator, 'measureId': measure})
    return {'source': url, 'years': j}

def data(publication, indicator, start, end, measure=-1):
    idcheck(publication)
    idcheck(indicator)
    if measure != -1:
        idcheck(measure)
    if not 1900 <= start <= end <= 2100 or end - start > 10:
        raise ValueError('Limit years to 11')
    p = {'publicationId': publication, 'datasetId': indicator, 'measureId': measure, 'y1': start, 'y2': end}
    j, url = get('/data', p)
    if not isinstance(j, dict) or 'RawData' not in j:
        raise ValueError('Unexpected data response')
    return {'source': url, 'data': j, 'note': 'Join colId to headerData.id and unit_id to units.id; do not infer a total or unit without those labels. Source provides methodology separately.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    s.add_parser('publications')
    d = s.add_parser('datasets')
    d.add_argument('publication', type=int)
    m = s.add_parser('metadata')
    m.add_argument('indicator', type=int)
    y = s.add_parser('years')
    y.add_argument('indicator', type=int)
    y.add_argument('--measure', type=int, default=-1)
    d = s.add_parser('data')
    d.add_argument('publication', type=int)
    d.add_argument('indicator', type=int)
    d.add_argument('--start', type=int, required=True)
    d.add_argument('--end', type=int, required=True)
    d.add_argument('--measure', type=int, default=-1)
    a = p.parse_args()
    res = publications() if a.command == 'publications' else datasets(a.publication) if a.command == 'datasets' else metadata(a.indicator) if a.command == 'metadata' else years(a.indicator, a.measure) if a.command == 'years' else data(a.publication, a.indicator, a.start, a.end, a.measure)
    print(json.dumps(res, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
