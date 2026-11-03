"""South African Reserve Bank public statistical releases and time series."""
import release_runtime
import argparse, datetime, json, re
import requests
BASE = 'https://custom.resbank.co.za/SarbWebApi/WebIndicators'
SECTIONS = {'real': 'GetRealSectorData', 'business': 'GetBusinessCyclesData', 'fiscal': 'GetFiscalSectorData', 'financial': 'GetFinancialSectorData', 'external': 'GetExternalSectorData', 'population': 'GetPopulationData', 'notes': 'GetFootNotes'}

def get(path):
    s = requests.Session()
    s.trust_env = False
    with s.get(BASE + path, timeout=35, stream=True) as r:
        r.raise_for_status()
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf.extend(chunk)
            if len(buf) > 8000000:
                raise ValueError('Response exceeds 8 MB')
        return (json.loads(buf), r.url)

def section(name, keyword='', limit=100):
    if name not in SECTIONS:
        raise ValueError('Unknown section')
    if not 1 <= limit <= 1000:
        raise ValueError('limit 1–1000')
    rows, url = get('/EconFinDataForSA/' + SECTIONS[name])
    if not isinstance(rows, list):
        raise ValueError('Unexpected response')
    rows = [x for x in rows if keyword.casefold() in json.dumps(x, ensure_ascii=False).casefold()]
    return {'source': url, 'matches': len(rows), 'returned': min(len(rows), limit), 'truncated': len(rows) > limit, 'rows': rows[:limit], 'note': 'PublishingAgency identifies the reporting source. Verify unit labels and footnotes; some population values conflict with the source unit label.'}

def releases():
    rows, url = get('/ReleaseOfSelectedData')
    return {'source': url, 'rows': rows}

def monthly(code, limit=100):
    if not re.fullmatch('[A-Z0-9]{2,20}', code) or not 1 <= limit <= 1000:
        raise ValueError('Invalid code or limit')
    available = releases()['rows']
    if not any((x.get('DataType') == code for x in available)):
        raise ValueError('Code absent from current release list')
    rows, url = get('/ReleaseOfSelectedData/MonthlyIndicators/' + code)
    if not isinstance(rows, list):
        raise ValueError('Unexpected response')
    return {'source': url, 'total': len(rows), 'returned': min(len(rows), limit), 'truncated': len(rows) > limit, 'rows': rows[:limit]}

def series(code, start, end):
    if not re.fullmatch('[A-Z0-9]{3,30}', code):
        raise ValueError('Invalid series code')
    s = datetime.date.fromisoformat(start)
    e = datetime.date.fromisoformat(end)
    if not s <= e or (e - s).days > 3653:
        raise ValueError('Invalid range; maximum 10 years')
    rows, url = get('/Shared/GetTimeseriesObservations/' + code + '/' + start + '/' + end)
    return {'source': url, 'rows': rows, 'note': 'Time-series endpoint omits unit and sometimes context; first inspect the section/release and notes for this code.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='command', required=True)
    a = s.add_parser('section')
    a.add_argument('name', choices=SECTIONS)
    a.add_argument('--keyword', default='')
    a.add_argument('--limit', type=int, default=100)
    s.add_parser('releases')
    a = s.add_parser('monthly')
    a.add_argument('code')
    a.add_argument('--limit', type=int, default=100)
    a = s.add_parser('series')
    a.add_argument('code')
    a.add_argument('--start', required=True)
    a.add_argument('--end', required=True)
    a = p.parse_args()
    res = section(a.name, a.keyword, a.limit) if a.command == 'section' else releases() if a.command == 'releases' else monthly(a.code, a.limit) if a.command == 'monthly' else series(a.code, a.start, a.end)
    print(json.dumps(res, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
