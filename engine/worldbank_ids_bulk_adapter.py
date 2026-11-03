"""World Bank IDS: read published bulk ZIP, series definitions and data."""
import release_runtime
import argparse, csv, io, json, os, re, zipfile, requests
URL = 'https://datacatalogfiles.worldbank.org/ddh-published/0038015/DR0096042/IDS_CSV_long.zip'

def download(path):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 384)
    try:
        with os.fdopen(fd, 'wb') as f, requests.get(URL, timeout=90, stream=True) as r:
            r.raise_for_status()
            n = 0
            for b in r.iter_content(65536):
                n += len(b)
                if n > 30000000:
                    raise ValueError('download exceeds 30 MB')
                f.write(b)
        with zipfile.ZipFile(path) as z:
            validate(z)
        return {'source': URL, 'file': os.path.abspath(path), 'bytes': n}
    except BaseException:
        os.unlink(path)
        raise

def validate(z):
    for name in ('IDS_CSV_long.csv', 'IDS_SeriesMetaData.csv', 'IDS_FootNoteMetaData.csv'):
        if name not in z.namelist() or z.getinfo(name).file_size > 80000000:
            raise ValueError('invalid IDS ZIP')

def readcsv(z, name):
    data = z.read(name)
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = data.decode('cp1252')
    return csv.DictReader(io.StringIO(text, newline=''))

def search_indicators(path, keyword, limit=50, offset=0):
    if not keyword or not isinstance(keyword, str):
        raise ValueError('keyword required')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 500) or isinstance(offset, bool) or (not isinstance(offset, int)) or (not 0 <= offset <= 100000):
        raise ValueError('invalid limit or offset')
    with zipfile.ZipFile(path) as z:
        validate(z)
        hits = [x for x in readcsv(z, 'IDS_SeriesMetaData.csv') if keyword.casefold() in (x['Code'] + ' ' + x['Indicator Name']).casefold()]
    selected = hits[offset:offset + limit]
    return {'source': os.path.abspath(path), 'reference_source': URL, 'matched_count': len(hits), 'limit': limit, 'offset': offset, 'next_offset': offset + len(selected) if offset + len(selected) < len(hits) else None, 'truncated': offset + len(selected) < len(hits), 'records': selected, 'note': '对所给本地 ZIP 的指标清单筛选并截取；同一文件位置稳定，替换文件后顺序可能变化。本地文件来源及版本未核验；参考地址不证明文件身份，不代表实时数据。'}

def observations(path, country, indicator, start, end):
    if not re.fullmatch('[A-Z]{3}', country):
        raise ValueError('country must be 3-character code')
    if not re.fullmatch('[A-Z0-9.]{3,60}', indicator):
        raise ValueError('invalid indicator code')
    if isinstance(start, bool) or isinstance(end, bool) or (not 1900 <= start <= end <= 2100):
        raise ValueError('invalid year range')
    col = indicator.replace('.', '')
    out = []
    footnotes = []
    with zipfile.ZipFile(path) as z:
        validate(z)
        meta = [x for x in readcsv(z, 'IDS_SeriesMetaData.csv') if x['Code'] == indicator]
        reader = readcsv(z, 'IDS_CSV_long.csv')
        if col not in (reader.fieldnames or []):
            raise ValueError('indicator has no data column')
        for row in reader:
            if row['CountryCode'].strip() != country or not row['Year'].isdigit() or (not start <= int(row['Year']) <= end):
                continue
            out.append({'country': row['Country'], 'country_code': country, 'counterpart': row['CounterpartAreaName'], 'counterpart_code': row['CounterpartAreaCode'], 'year': int(row['Year']), 'value': row[col] or None})
        for x in readcsv(z, 'IDS_FootNoteMetaData.csv'):
            if x['Country Code'].strip().endswith('(' + country + ')') and x['Series Code'].strip().endswith('(' + indicator + ')') and any((x['Time Code'].startswith(str(y) + ' ') for y in range(start, end + 1))):
                footnotes.append(x)
    return {'source': os.path.abspath(path), 'reference_source': URL, 'provider': None, 'series_metadata': meta, 'observations': out, 'footnotes': footnotes, 'note': 'World counterpart only. Values remain strings; empty is missing, not zero. Local archive provenance and version are unverified.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    d = s.add_parser('download')
    d.add_argument('path')
    i = s.add_parser('indicators')
    i.add_argument('path')
    i.add_argument('keyword')
    i.add_argument('--limit', type=int, default=50)
    i.add_argument('--offset', type=int, default=0)
    v = s.add_parser('data')
    v.add_argument('path')
    v.add_argument('country')
    v.add_argument('indicator')
    v.add_argument('start', type=int)
    v.add_argument('end', type=int)
    a = p.parse_args()
    result = download(a.path) if a.cmd == 'download' else search_indicators(a.path, a.keyword, a.limit, a.offset) if a.cmd == 'indicators' else observations(a.path, a.country, a.indicator, a.start, a.end)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
