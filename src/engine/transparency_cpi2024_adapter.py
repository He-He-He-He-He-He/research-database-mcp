"""Transparency International CPI 2024 original Strict OOXML table."""
import release_runtime
import argparse, hashlib, io, json, re, zipfile
import xml.etree.ElementTree as ET
import requests
URL = 'https://images.transparencycdn.org/images/CPI2024-Results-and-trends.xlsx'
PAGE = 'https://www.transparency.org/en/cpi/2024'
NS = {'x': 'http://purl.oclc.org/ooxml/spreadsheetml/main'}

def query(keyword='', limit=20, *, offset=0):
    if not isinstance(keyword, str) or len(keyword) > 100 or type(limit) is not int or (not 1 <= limit <= 180) or (type(offset) is not int) or (offset < 0):
        raise ValueError('invalid keyword or limit')
    with requests.get(URL, stream=True, timeout=25) as response:
        response.raise_for_status()
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > 3000000:
                raise ValueError('source too large')
    raw = bytes(data)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in ('xl/sharedStrings.xml', 'xl/worksheets/sheet1.xml'):
            if z.getinfo(name).file_size > 10000000:
                raise ValueError('source XML too large')
        strings = [''.join((t.text or '' for t in node.findall('.//x:t', NS))) for node in ET.fromstring(z.read('xl/sharedStrings.xml'))]
        root = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    rows = []
    for row in root.findall('.//x:sheetData/x:row', NS):
        number = int(row.attrib['r'])
        if number < 3:
            continue
        cells = {}
        for cell in row.findall('x:c', NS):
            col = re.match('[A-Z]+', cell.attrib['r']).group()
            v = cell.find('x:v', NS)
            val = v.text if v is not None else None
            if cell.get('t') == 's' and val is not None:
                val = strings[int(val)]
            cells[col] = val
        if number == 3:
            headers = cells
            continue
        if not cells.get('A') or not cells.get('B'):
            continue
        rows.append({headers[k]: v for k, v in cells.items() if k in headers and headers[k]})
    if len(rows) != 180:
        raise ValueError('unexpected country count; verify source structure')
    matched = [r for r in rows if keyword.casefold() in (r.get('Country / Territory', '') + ' ' + r.get('ISO3', '')).casefold()]
    return {'source': URL, 'source_page': PAGE, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'publication_date': '2025-02-11', 'table': 'CPI 2024 global scores', 'matched_count': len(matched), 'offset': offset, 'returned_count': len(matched[offset:offset + limit]), 'next_offset': offset + limit if offset + limit < len(matched) else None, 'truncated': offset + limit < len(matched), 'records': matched[offset:offset + limit], 'note': 'Nongovernmental composite index of perceived public-sector corruption, not a count of cases. Score scale 0–100; higher means cleaner. Confidence intervals, standardized input sources and missing values are retained as source strings; no values are converted. Current downloadable file may have been modified since release; historical identity is not independently archived. Each request refetches the workbook; updated files may change ordering. Source attribution and CC BY-ND 4.0 terms apply.'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--keyword', default='')
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(query(a.keyword, a.limit, offset=a.offset), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
