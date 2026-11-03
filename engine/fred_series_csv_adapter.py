"""FRED official graph CSV exports for one public series per request."""
import release_runtime
import argparse, csv, datetime, io, json, re, subprocess
from urllib.parse import urlencode
ROOT = 'https://fred.stlouisfed.org/'

def observations(series, start, end, limit=100):
    if not re.fullmatch('[A-Z0-9_]{1,40}', series):
        raise ValueError('invalid FRED series ID')
    try:
        s = datetime.date.fromisoformat(start)
        e = datetime.date.fromisoformat(end)
    except ValueError:
        raise ValueError('dates must be YYYY-MM-DD') from None
    if s > e or not 1 <= limit <= 1000:
        raise ValueError('invalid range or limit')
    source = ROOT + 'graph/fredgraph.csv?' + urlencode({'id': series, 'cosd': start, 'coed': end})
    process = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '35', '--max-filesize', str(4 * 1024 * 1024), source], capture_output=True, timeout=40)
    if process.returncode:
        raise RuntimeError('FRED request failed: ' + process.stderr.decode('utf-8', 'replace')[:200])
    if len(process.stdout) > 4 * 1024 * 1024:
        raise ValueError('response exceeds 4 MiB')
    f = csv.DictReader(io.StringIO(process.stdout.decode('utf-8-sig')))
    if f.fieldnames != ['observation_date', series]:
        raise ValueError('unexpected CSV; check series ID or service response')
    data = []
    total = 0
    for row in f:
        try:
            date = datetime.date.fromisoformat(row['observation_date'])
        except (TypeError, ValueError):
            raise ValueError('invalid observation date') from None
        if not s <= date <= e:
            continue
        total += 1
        if len(data) < limit:
            data.append({'date': str(date), 'value': row[series] if row[series] not in ('', '.', 'NA') else None})
    return {'source': source, 'series_page': ROOT + 'series/' + series, 'series': series, 'total_rows': total, 'returned_rows': len(data), 'truncated': len(data) < total, 'observations': data, 'note': 'CSV values are strings; series definitions, units, frequency, seasonal adjustment, revisions and license must be checked on series page. If truncated, narrow or split the date range and account for possible source revisions between requests.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('series')
    p.add_argument('start')
    p.add_argument('end')
    p.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(observations(a.series, a.start, a.end, a.limit), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
