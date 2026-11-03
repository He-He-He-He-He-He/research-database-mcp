"""Federal Reserve Z.1 quarterly release tables with accompanying dictionary."""
import release_runtime
import csv
import hashlib
import io
import re
import zipfile
import requests
URL = 'https://www.federalreserve.gov/releases/z1/current/z1_csv_files.zip'

def _archive():
    with requests.get(URL, timeout=50, stream=True, allow_redirects=False) as response:
        if response.is_redirect or not response.ok:
            raise RuntimeError('Federal Reserve data request failed: HTTP ' + str(response.status_code))
        content = bytearray()
        for chunk in response.iter_content(65536):
            content.extend(chunk)
            if len(content) > 15000000:
                raise RuntimeError('Federal Reserve archive exceeds 15 MB')
    return bytes(content)

def _read(z, name):
    try:
        info = z.getinfo(name)
    except KeyError:
        raise ValueError('Requested table not available in current release') from None
    if info.file_size > 5000000:
        raise RuntimeError('Individual archive file exceeds 5 MB')
    return z.read(info).decode('utf-8-sig')

def tables(keyword='', limit=30, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('Invalid keyword')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (limit, offset))) or not 1 <= limit <= 100 or offset < 0:
        raise ValueError('Invalid pagination')
    raw = _archive()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        items = []
        for n in sorted(z.namelist()):
            if not n.startswith('data_dictionary/') or not n.endswith('.txt'):
                continue
            txt = _read(z, n)
            table = n[len('data_dictionary/'):-4]
            first = txt.splitlines()[0] if txt.splitlines() else ''
            if keyword.casefold() in txt.casefold() or keyword.casefold() in table.casefold():
                items.append({'table': table, 'first_dictionary_entry': first})
        return {'source_url': URL, 'archive_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'keyword': keyword, 'matched_total': len(items), 'offset': offset, 'items': items[offset:offset + limit], 'note': '仅搜索当期 Z.1 数据字典中的表或序列描述；各表可能包含多个口径，需查看完整字典。'}

def series(table, code, start_year, end_year):
    if not isinstance(table, str) or not re.fullmatch('[A-Za-z0-9_]{1,60}', table):
        raise ValueError('Invalid table identifier')
    if not isinstance(code, str) or not re.fullmatch('[A-Z0-9]+\\.[AQ]', code):
        raise ValueError('Invalid series identifier')
    if any((isinstance(x, bool) or not isinstance(x, int) for x in (start_year, end_year))) or not 1900 <= start_year <= end_year <= 2200:
        raise ValueError('Invalid years')
    raw = _archive()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        dictionary = _read(z, 'data_dictionary/' + table + '.txt')
        rows = csv.reader(io.StringIO(_read(z, 'csv/' + table + '.csv')))
        header = next(rows, None)
        if not header or header[0] != 'date':
            raise RuntimeError('Unexpected Federal Reserve CSV format')
        columns = [i for i, x in enumerate(header) if x == code]
        if not columns:
            raise ValueError('Series not found in selected table')
        definitions = [line.split('\t') for line in dictionary.splitlines() if line.split('\t')[0] == code]
        if not definitions:
            raise RuntimeError('Series absent from Federal Reserve data dictionary')
        output = []
        for row in rows:
            if len(row) != len(header):
                raise RuntimeError('Unexpected Federal Reserve CSV row')
            m = re.fullmatch('(\\d{4})(?::Q[1-4])?', row[0])
            if not m:
                raise RuntimeError('Unexpected Federal Reserve date')
            if start_year <= int(m.group(1)) <= end_year:
                output.append({'date': row[0], 'values_original': [row[i] for i in columns]})
        return {'source': 'Federal Reserve Z.1 Financial Accounts', 'source_url': URL, 'source_info': 'https://www.federalreserve.gov/releases/z1/', 'sha256': hashlib.sha256(raw).hexdigest(), 'archive_bytes': len(raw), 'table': table, 'series': code, 'column_positions': columns, 'dictionary_entries': definitions, 'returned': len(output), 'items': output, 'note': '当前 Z.1 发布归档；按数据字典判断百万美元、季调、年化、存量或流量。相同序列可能在同表重复出现，按列序保留每个值；ND 等原始标记不是零。各部门、总计与分项可能重叠，不可直接相加。'}
