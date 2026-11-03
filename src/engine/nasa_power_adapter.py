"""NASA POWER monthly point observations, with returned source metadata."""
import release_runtime
import argparse, json, math, re
import requests
ROOT = 'https://power.larc.nasa.gov/api/temporal/monthly/'

def _get(path, params=None):
    with requests.get(ROOT + path, params=params, timeout=45, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        chunks = []
        size = 0
        for x in r.iter_content(65536):
            size += len(x)
            if size > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB')
            chunks.append(x)
        return {'source': r.url, 'data': json.loads(b''.join(chunks))}

def configuration():
    return _get('configuration')

def monthly(latitude, longitude, start, end, parameters, community='AG'):
    if not all((math.isfinite(x) for x in (latitude, longitude))) or not -90 <= latitude <= 90 or (not -180 <= longitude <= 180):
        raise ValueError('invalid coordinates')
    if not 1981 <= start <= end <= 2100 or end - start > 20:
        raise ValueError('invalid year range; maximum 21 years')
    if not re.fullmatch('[A-Z0-9_]+(?:,[A-Z0-9_]+){0,9}', parameters):
        raise ValueError('invalid parameter names')
    if community not in ('AG', 'RE', 'SB'):
        raise ValueError('invalid community')
    return _get('point', {'latitude': latitude, 'longitude': longitude, 'start': start, 'end': end, 'parameters': parameters, 'community': community, 'format': 'JSON'})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    s.add_parser('configuration')
    a = s.add_parser('monthly')
    a.add_argument('latitude', type=float)
    a.add_argument('longitude', type=float)
    a.add_argument('start', type=int)
    a.add_argument('end', type=int)
    a.add_argument('parameters')
    a.add_argument('--community', choices=['AG', 'RE', 'SB'], default='AG')
    a = p.parse_args()
    result = configuration() if a.cmd == 'configuration' else monthly(a.latitude, a.longitude, a.start, a.end, a.parameters, a.community)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
