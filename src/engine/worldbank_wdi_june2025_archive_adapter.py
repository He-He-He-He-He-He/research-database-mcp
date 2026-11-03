"""World Bank WDI June 5 2025 archive, with definitions and source footnotes."""
import release_runtime
import argparse, hashlib, io, json, os, re, tempfile, zipfile
from pathlib import Path
import requests, openpyxl
URL = 'https://databankfiles.worldbank.org/public/ddpext_download/Archive/WDI_excel_2025_06_05.zip'
PAGE = 'https://datatopics.worldbank.org/world-development-indicators/wdi-archives.html'
SHA = '61d2b6fd3c7fc37ea207ed61ddcc3e94ef37a9e56ce1b16d519e631b5698146c'
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit' / 'WDI_excel_2025_06_05.zip'

def _hash(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda: f.read(1048576), b''):
            h.update(c)
    return h.hexdigest()

def _archive():
    if CACHE.is_file() and _hash(CACHE) == SHA:
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=CACHE.parent, prefix='.wdi-', delete=False) as f:
            temp = Path(f.name)
            n = 0
            with requests.get(URL, stream=True, timeout=90) as r:
                r.raise_for_status()
                for c in r.iter_content(1048576):
                    n += len(c)
                    if n > 90000000:
                        raise ValueError('archive too large')
                    f.write(c)
        if _hash(temp) != SHA:
            raise ValueError('source archive checksum changed; manual review required')
        os.replace(temp, CACHE)
        return CACHE
    finally:
        if temp and temp.exists():
            temp.unlink()

def query(country, indicator, start=2020, end=2024):
    if not isinstance(country, str) or not re.fullmatch('[A-Z0-9]{3}', country):
        raise ValueError('country must be three-letter source code')
    if not isinstance(indicator, str) or not re.fullmatch('[A-Z0-9.]{3,40}', indicator):
        raise ValueError('invalid indicator code')
    if any((type(v) is not int for v in (start, end))) or not 1960 <= start <= end <= 2028:
        raise ValueError('invalid years')
    path = _archive()
    with zipfile.ZipFile(path) as z:
        info = z.getinfo('WDIEXCEL.xlsx')
        if info.file_size > 100000000:
            raise ValueError('workbook too large')
        workbook_bytes = z.read(info)
    w = openpyxl.load_workbook(io.BytesIO(workbook_bytes), read_only=True, data_only=True)
    try:
        it = w['Data'].values
        h = next(it)
        record = None
        for row in it:
            if row[1] == country and row[3] == indicator:
                record = {'country_name': row[0], 'country_code': row[1], 'indicator_name': row[2], 'indicator_code': row[3], 'values': {str(h[i]): row[i] for i in range(4, len(h)) if str(h[i]).isdigit() and start <= int(h[i]) <= end}}
                break
        series = None
        for row in w['Series'].values:
            if row[0] == indicator:
                series = list(row)
                break
        country_notes = [list(row) for row in w['country-series'].values if row[0] == country and row[1] == indicator]
        series_notes = [list(row) for row in w['series-time'].values if row[0] == indicator and str(row[1]).removeprefix('YR').isdigit() and (start <= int(str(row[1]).removeprefix('YR')) <= end)]
        footnotes = [list(row) for row in w['footnote'].values if row[0] == country and row[1] == indicator and str(row[2]).removeprefix('YR').isdigit() and (start <= int(str(row[2]).removeprefix('YR')) <= end)]
        return {'source': URL, 'archive_index': PAGE, 'archive_label': '2025-06-05', 'zip_member_timestamp': list(info.date_time), 'observed_http_last_modified': 'Tue, 28 Oct 2025 20:29:35 GMT', 'archive_sha256': SHA, 'found': record is not None, 'record': record, 'series_header': list(next(w['Series'].values)), 'series_metadata': series, 'country_series_notes': country_notes, 'series_time_notes': series_notes, 'country_year_footnotes': footnotes, 'note': 'World Bank archive labelled 2025-06-05; ZIP member timestamp is 2025-06-05 but server Last-Modified observed 2025-10-28, so exact pre-cutoff availability and immutable identity are not independently established. Historical archive values may differ from the current API. Preserve country/series/year footnotes, units and indicator definitions; blank values are missing. Each indicator has its own data year and source, and may be model estimates. The compressed archive is cached locally (~80 MB) and checksum pinned.'}
    finally:
        w.close()

def query_many(countries, indicators, start=2020, end=2024):
    if not isinstance(countries, list) or not isinstance(indicators, list) or (not countries) or (not indicators) or (len(countries) * len(indicators) > 25):
        raise ValueError('choose at most 25 country-indicator combinations')
    if len(set(countries)) != len(countries) or len(set(indicators)) != len(indicators):
        raise ValueError('duplicate country or indicator')
    if any((not isinstance(c, str) or not re.fullmatch('[A-Z0-9]{3}', c) for c in countries)):
        raise ValueError('invalid country code')
    if any((not isinstance(i, str) or not re.fullmatch('[A-Z0-9.]{3,40}', i) for i in indicators)):
        raise ValueError('invalid indicator code')
    if any((type(v) is not int for v in (start, end))) or not 1960 <= start <= end <= 2028:
        raise ValueError('invalid years')
    path = _archive()
    with zipfile.ZipFile(path) as z:
        info = z.getinfo('WDIEXCEL.xlsx')
        if info.file_size > 100000000:
            raise ValueError('workbook too large')
        workbook_bytes = z.read(info)
    w = openpyxl.load_workbook(io.BytesIO(workbook_bytes), read_only=True, data_only=True)
    try:
        keys = {(c, i) for c in countries for i in indicators}
        result = {k: {'country_code': k[0], 'indicator_code': k[1], 'found': False, 'record': None, 'country_series_notes': [], 'series_time_notes': [], 'country_year_footnotes': []} for k in keys}
        it = w['Data'].values
        header = next(it)
        for row in it:
            key = (row[1], row[3])
            if key not in result:
                continue
            result[key]['found'] = True
            result[key]['record'] = {'country_name': row[0], 'country_code': row[1], 'indicator_name': row[2], 'indicator_code': row[3], 'values': {str(header[i]): row[i] for i in range(4, len(header)) if str(header[i]).isdigit() and start <= int(header[i]) <= end}}
        it = w['Series'].values
        series_header = list(next(it))
        series = {}
        for row in it:
            if row[0] in indicators:
                series[row[0]] = list(row)
        for row in w['country-series'].values:
            key = (row[0], row[1])
            if key in result:
                result[key]['country_series_notes'].append(list(row))
        notes = {i: [] for i in indicators}
        for row in w['series-time'].values:
            y = str(row[1]).removeprefix('YR')
            if row[0] in notes and y.isdigit() and (start <= int(y) <= end):
                notes[row[0]].append(list(row))
        for row in w['footnote'].values:
            key = (row[0], row[1])
            y = str(row[2]).removeprefix('YR')
            if key in result and y.isdigit() and (start <= int(y) <= end):
                result[key]['country_year_footnotes'].append(list(row))
        output = []
        for c in countries:
            for i in indicators:
                item = result[c, i]
                item['series_metadata'] = series.get(i)
                item['series_time_notes'] = notes[i]
                output.append(item)
        return {'source': URL, 'archive_index': PAGE, 'archive_label': '2025-06-05', 'zip_member_timestamp': list(info.date_time), 'observed_http_last_modified': 'Tue, 28 Oct 2025 20:29:35 GMT', 'archive_sha256': SHA, 'series_header': series_header, 'records': output, 'note': 'Archive label and ZIP member timestamp are June 2025 but server Last-Modified observed October 2025; exact historical availability is not independently established. Values are per-series archive observations or estimates; blanks are missing. Preserve indicator definitions, units and footnotes, and distinguish fiscal/calendar years. This batch scans the cached archive once.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    p.add_argument('indicator')
    p.add_argument('--start', type=int, default=2020)
    p.add_argument('--end', type=int, default=2024)
    a = p.parse_args()
    print(json.dumps(query(a.country, a.indicator, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
