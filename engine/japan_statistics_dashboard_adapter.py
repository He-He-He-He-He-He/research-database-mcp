"""Japan Statistics Dashboard: indicator discovery and bounded data queries."""
import release_runtime
import argparse, json, re
import requests
BASE = 'https://dashboard.e-stat.go.jp/api/1.0/Json/'
MAX_BYTES = 10 * 1024 * 1024

def _get(action, params):
    with requests.get(BASE + action, params=params, timeout=45, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        pieces = []
        size = 0
        for block in r.iter_content(65536):
            size += len(block)
            if size > MAX_BYTES:
                raise ValueError('Response exceeds 10 MiB; narrow the query')
            pieces.append(block)
        data = json.loads(b''.join(pieces))
        root = next(iter(data.values()))
        if root.get('RESULT', {}).get('status') != '0':
            raise ValueError(str(root.get('RESULT')))
        return {'source': r.url, 'result': data, 'attribution': 'This service uses the API feature of Statistics Dashboard, but the contents of this service are not guaranteed by the Statistics Bureau of Japan.'}

def search(keyword, lang='EN'):
    if not keyword or len(keyword) > 120:
        raise ValueError('keyword must be 1–120 characters')
    if lang not in ('EN', 'JP'):
        raise ValueError('lang must be EN or JP')
    return _get('getIndicatorInfo', {'Lang': lang, 'SearchIndicatorWord': keyword})

def data(indicator, cycle='3', regional_rank='2', seasonal='1', lang='EN'):
    if not re.fullmatch('\\d{19}', indicator):
        raise ValueError('19-digit indicator code required')
    if cycle not in ('1', '2', '3', '4') or regional_rank not in ('1', '2', '3', '4') or seasonal not in ('1', '2') or (lang not in ('EN', 'JP')):
        raise ValueError('invalid dimension')
    return _get('getData', {'Lang': lang, 'IndicatorCode': indicator, 'Cycle': cycle, 'RegionalRank': regional_rank, 'IsSeasonalAdjustment': seasonal, 'MetaGetFlg': 'Y', 'SectionHeaderFlg': '1'})

def main():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--lang', default='EN')
    q = s.add_parser('data')
    q.add_argument('indicator')
    q.add_argument('--cycle', default='3')
    q.add_argument('--regional-rank', default='2')
    q.add_argument('--seasonal', default='1')
    q.add_argument('--lang', default='EN')
    a = p.parse_args()
    result = search(a.keyword, a.lang) if a.cmd == 'search' else data(a.indicator, a.cycle, a.regional_rank, a.seasonal, a.lang)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
