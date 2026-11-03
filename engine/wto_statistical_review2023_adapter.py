"""WTO World Trade Statistical Review 2023 statistical annex workbooks."""
import release_runtime
import argparse, hashlib, io, json, re, sys, zipfile
from pathlib import Path
import requests
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
URL = 'https://www.wto.org/english/res_e/booksp_e/wtsr_2023_ch5.zip'
PAGE = 'https://www.wto.org/english/res_e/publications_e/wtsr_2023_e.htm'

def query(file='', language='English', start=1, end=100):
    if file and (not re.fullmatch('a\\d{2}[a-z]?\\.xls', file)):
        raise ValueError('invalid table filename')
    if language not in ('English', 'French', 'Spanish') or any((type(x) is not int for x in (start, end))) or (not 1 <= start <= end <= 10000) or (end - start > 199):
        raise ValueError('invalid language or range')
    with requests.get(URL, stream=True, timeout=45) as r:
        r.raise_for_status()
        modified = r.headers.get('Last-Modified')
        raw = r.raw.read(5000001, decode_content=True)
    if len(raw) > 5000000:
        raise ValueError('archive too large')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist() if re.fullmatch('a\\d{2}[a-z]?\\.xls', n)]
        if len(names) != 70:
            raise ValueError('unexpected archive contents')
        meta = {'source': URL, 'report_page': PAGE, 'edition': '2023', 'http_last_modified': modified, 'archive_sha256': hashlib.sha256(raw).hexdigest(), 'available_tables': names, 'note': 'WTO historical 2023 review statistical appendix; many tables describe 2022 rather than 2023. Preserve original units, headings, merged cells, missing symbols and footnotes. Values are underlying workbook data and may be rounded for display. Dates and hash do not alone prove immutable archive history; consult WTO usage terms.'}
        if not file:
            return meta
        if file not in names:
            raise ValueError('unknown table filename')
        info = z.getinfo(file)
        if info.file_size > 5000000:
            raise ValueError('workbook too large')
        content = z.read(file)
    w = xlrd.open_workbook(file_contents=content, formatting_info=True)
    if language not in w.sheet_names():
        raise ValueError('language unavailable')
    s = w.sheet_by_name(language)
    rows = []
    for i in range(start - 1, min(end, s.nrows)):
        cells = []
        for j, c in enumerate(s.row(i)):
            if c.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                continue
            value = xlrd.error_text_from_code.get(c.value, str(c.value)) if c.ctype == xlrd.XL_CELL_ERROR else c.value
            cells.append({'column': j + 1, 'value': value, 'cell_type': c.ctype})
        if cells:
            rows.append({'row': i + 1, 'cells': cells})
    meta.update({'file': file, 'zip_member_timestamp': info.date_time, 'workbook_sha256': hashlib.sha256(content).hexdigest(), 'language': language, 'row_range': [start, end], 'sheet_rows': s.nrows, 'sheet_columns': s.ncols, 'merged_ranges_zero_based_exclusive': [list(v) for v in s.merged_cells], 'rows': rows})
    return meta

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--file', default='')
    p.add_argument('--language', choices=['English', 'French', 'Spanish'], default='English')
    p.add_argument('--start', type=int, default=1)
    p.add_argument('--end', type=int, default=100)
    a = p.parse_args()
    print(json.dumps(query(a.file, a.language, a.start, a.end), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
