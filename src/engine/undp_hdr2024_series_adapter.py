"""UNDP HDR 2023/2024 官方综合指数完整时间序列与代码簿（固定报告版本）。"""
import release_runtime
import argparse
import csv
import io
import json
import re
import subprocess
import openpyxl
CSV_URL = 'https://hdr.undp.org/sites/default/files/2023-24_HDR/HDR23-24_Composite_indices_complete_time_series.csv'
META_URL = 'https://hdr.undp.org/sites/default/files/2023-24_HDR/HDR23-24_Composite_indices_metadata.xlsx'
MAX_BYTES = 8000000

def _download(url):
    if url not in (CSV_URL, META_URL):
        raise ValueError('无效来源')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('UNDP 下载失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('数据过大')
    return p.stdout

def indicators(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('无效关键词')
    book = openpyxl.load_workbook(io.BytesIO(_download(META_URL)), read_only=True, data_only=True)
    try:
        sheet = book['country_insights']
        out = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            name, code, years = (list(row) + [None, None, None])[:3]
            if not code or code in ('iso3', 'country', 'hdicode', 'region'):
                continue
            if keyword.casefold() in (str(name) + ' ' + str(code)).casefold():
                out.append({'code': code, 'name': name, 'time_series': years})
    finally:
        book.close()
    return {'source': META_URL, 'release': 'HDR 2023/2024', 'keyword': keyword, 'indicators': out, 'note': '官方代码簿；年份说明可能包含实际数值沿用不同年份，不能简单理解为逐年实测。'}

def countries(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('无效关键词')
    csvdata = csv.DictReader(io.StringIO(_download(CSV_URL).decode('cp1252'), newline=''))
    rows = []
    for r in csvdata:
        if keyword.casefold() in (r['iso3'] + ' ' + r['country']).casefold():
            rows.append({k: r[k] for k in ('iso3', 'country', 'hdicode', 'region')})
    return {'source': CSV_URL, 'release': 'HDR 2023/2024', 'items': rows, 'note': '此报告版本中的国家和地区；数据可能缺失，名单不表示完整联合国会员名单。'}

def data(iso3, indicator, start, end):
    if not isinstance(iso3, str) or not re.fullmatch('[A-Z]{3}', iso3):
        raise ValueError('国家 ISO3 须为三个大写字母')
    if not isinstance(indicator, str) or not re.fullmatch('[a-z0-9_]{1,40}', indicator):
        raise ValueError('指标代码无效')
    if any((isinstance(x, bool) or not isinstance(x, int) or (not 1990 <= x <= 2022) for x in (start, end))) or start > end:
        raise ValueError('年份范围须在 1990–2022 内')
    matches = [x for x in indicators()['indicators'] if x['code'] == indicator]
    if not matches:
        raise ValueError('未找到指标代码，请先查询代码簿')
    reader = csv.DictReader(io.StringIO(_download(CSV_URL).decode('cp1252'), newline=''))
    row = next((r for r in reader if r['iso3'] == iso3), None)
    if row is None:
        raise ValueError('此版本中未找到该 ISO3')
    year_columns = {y: indicator + '_' + str(y) for y in range(start, end + 1)}
    values = [{'year': y, 'value': row[c] if c in row else None} for y, c in year_columns.items()]
    return {'source': CSV_URL, 'metadata_source': META_URL, 'release': 'HDR 2023/2024', 'country': row['country'], 'iso3': iso3, 'indicator_metadata': matches, 'observations': values, 'note': '值保留官方字符串；空字符串或 null 是缺失，不是零。请核对代码簿中的覆盖、估计和时间沿用说明，以及报告方法。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('indicators')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('countries')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('data')
    q.add_argument('iso3')
    q.add_argument('indicator')
    q.add_argument('start', type=int)
    q.add_argument('end', type=int)
    a = p.parse_args()
    x = indicators(a.keyword) if a.cmd == 'indicators' else countries(a.keyword) if a.cmd == 'countries' else data(a.iso3, a.indicator, a.start, a.end)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
