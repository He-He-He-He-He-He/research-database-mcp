"""UN Peace and Security Data Hub active peacekeeping uniformed personnel fatality rate."""
import release_runtime
import argparse, json, requests
BASE = 'https://api.psdata.un.org/public/'
DATASET = 'DPPADPO-FATALITYRATEACTIVEPKO'

def query(start=2010, end=2026):
    if not isinstance(start, int) or not isinstance(end, int) or (not 2010 <= start <= end <= 2100):
        raise ValueError('invalid years')
    url = BASE + 'data/' + DATASET + '/json'
    rows = []
    for page in range(1, 51):
        r = requests.get(url, params={'page_num': page, 'per_page': 100}, timeout=40)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list):
            raise ValueError('unexpected response')
        for x in data:
            if not isinstance(x, dict) or not isinstance(x.get('year'), int) or x.get('half_year') not in ('H1', 'H2') or ('fatality_rate' not in x):
                raise ValueError('unexpected row schema')
            if start <= x['year'] <= end:
                rows.append(x)
        if len(data) < 100:
            break
    else:
        raise ValueError('pagination exceeds safe limit')
    return {'source': url, 'metadata_url': BASE + 'metadata/' + DATASET, 'provider': 'UN Peace and Security Data Hub', 'unit': 'fatalities per 1000 average uniformed personnel per half-year', 'records': rows, 'note': 'Only currently active missions; selection changes when mission status changes. Semiannual, not annual, rates.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('start', type=int)
    p.add_argument('end', type=int)
    a = p.parse_args()
    print(json.dumps(query(a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
