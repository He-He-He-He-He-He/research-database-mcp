"""IMF DataMapper indicator metadata and locally filtered country/year values."""
import release_runtime
import argparse
import json
import re
import subprocess
import threading
import time
BASE = 'https://www.imf.org/external/datamapper/api/v2/'
_lock = threading.Lock()
_last = 0.0

def _get(path):
    global _last
    with _lock:
        delay = 1 - (time.monotonic() - _last)
        if delay > 0:
            time.sleep(delay)
        _last = time.monotonic()
        result = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', BASE + path], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    if not isinstance(data, dict):
        raise ValueError('unexpected IMF response')
    return data

def search_indicators(query):
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be non-empty')
    data = _get('indicators').get('indicators')
    if not isinstance(data, dict):
        raise ValueError('missing indicators')
    q = query.strip().casefold()
    return {k: v for k, v in data.items() if q in k.casefold() or q in str(v.get('label', '')).casefold()}

def indicator_value(indicator, country, year):
    if not isinstance(indicator, str) or not re.fullmatch('[A-Z0-9_]{1,50}', indicator):
        raise ValueError('invalid indicator')
    if not isinstance(country, str) or not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('invalid country code')
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2100):
        raise ValueError('invalid year')
    data = _get(indicator)
    info = data.get('indicators', {}).get(indicator)
    all_values = data.get('values', {}).get(indicator)
    if not isinstance(info, dict) or not isinstance(all_values, dict):
        raise ValueError('missing indicator data')
    if country not in all_values:
        raise ValueError('country not found in series')
    return {'indicator': indicator, 'metadata': info, 'country': country, 'year': year, 'value': all_values[country].get(str(year)), 'note': 'DataMapper 数据集可能同时包含历史值、估计值和预测值，不能仅凭年份判断属性；请依据 metadata 的数据集版本及 IMF 对应国家元数据核验。缺失值为 null，不是零；部分国家可能使用财年。'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    s = sub.add_parser('search')
    s.add_argument('query')
    v = sub.add_parser('value')
    v.add_argument('indicator')
    v.add_argument('country')
    v.add_argument('year', type=int)
    args = parser.parse_args()
    result = search_indicators(args.query) if args.command == 'search' else indicator_value(args.indicator, args.country, args.year)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
