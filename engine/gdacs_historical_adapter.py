"""GDACS historical events search API, bounded annual windows."""
import release_runtime
import argparse, datetime, json
import requests
URL = 'https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH'

def search(event_types, fromdate, todate, alert_levels, limit=20):
    events = event_types.split(',')
    levels = alert_levels.lower().split(',')
    if not events or len(set(events)) != len(events) or any((e not in {'EQ', 'TC', 'FL', 'VO'} for e in events)):
        raise ValueError('supported event types: EQ, TC, FL, VO')
    if not levels or len(set(levels)) != len(levels) or any((x not in {'red', 'orange', 'green'} for x in levels)):
        raise ValueError('unsupported alert level')
    try:
        start = datetime.date.fromisoformat(fromdate)
        end = datetime.date.fromisoformat(todate)
    except ValueError:
        raise ValueError('dates must be YYYY-MM-DD') from None
    if start > end or (end - start).days > 366 or (not 1 <= limit <= 100):
        raise ValueError('invalid time window or limit')
    with requests.get(URL, params={'eventlist': ';'.join(events), 'fromdate': fromdate, 'todate': todate, 'alertlevel': ';'.join(levels)}, timeout=40, stream=True, headers={'User-Agent': 'ResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        parts = []
        size = 0
        for x in r.iter_content(65536):
            size += len(x)
            if size > 8 * 1024 * 1024:
                raise ValueError('response exceeds 8 MiB; narrow date range')
            parts.append(x)
        data = json.loads(b''.join(parts))
        source = r.url
    if data.get('type') != 'FeatureCollection' or not isinstance(data.get('features'), list):
        raise ValueError('unexpected GeoJSON')
    return {'source': source, 'source_attribution': 'Global Disaster Alert and Coordination System, GDACS', 'source_returned': len(data['features']), 'returned': min(limit, len(data['features'])), 'features': data['features'][:limit], 'note': 'source_returned is the returned collection size, not a verified complete historical total; events and alerts may be revised.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('event_types')
    p.add_argument('fromdate')
    p.add_argument('todate')
    p.add_argument('--levels', default='red')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.event_types, a.fromdate, a.todate, a.levels, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
