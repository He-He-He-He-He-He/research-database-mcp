"""INEC Ecuador 2024 population-estimates revision, read selected sheets via HTTP ranges."""
import release_runtime
import io, re, zipfile, xml.etree.ElementTree as ET
import requests
URL = 'https://www.ecuadorencifras.gob.ec/documentos/web-inec/Poblacion_y_Demografia/Proyecciones_Poblacionales/censo_2022/revision_2024_areas/Tabulados_Estimacion_Proyeccion_v2.xlsx'
PAGE = 'https://www.ecuadorencifras.gob.ec/proyecciones-poblacionales/'
MAIN = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'

class _RangeFile(io.RawIOBase):

    def __init__(self):
        self.session = requests.Session()
        r = self.session.get(URL, headers={'Range': 'bytes=0-0', 'Accept-Encoding': 'identity'}, timeout=30)
        r.raise_for_status()
        m = re.fullmatch('bytes 0-0/(\\d+)', r.headers.get('Content-Range', ''))
        if r.status_code != 206 or not m or len(r.content) != 1 or (not r.headers.get('ETag')):
            raise RuntimeError('No validated range support or ETag')
        self.size = int(m.group(1))
        self.etag = r.headers['ETag']
        self.pos = 0
        if not 1 <= self.size <= 100000000:
            raise RuntimeError('Unexpected workbook size')

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        new = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset if whence == 2 else -1
        if new < 0:
            raise ValueError('negative seek')
        self.pos = new
        return new

    def read(self, size=-1):
        if size is None or size < 0:
            size = self.size - self.pos
        size = min(size, max(0, self.size - self.pos))
        if not size:
            return b''
        if size > 4000000:
            raise RuntimeError('Range exceeds bound')
        start = self.pos
        end = start + size - 1
        r = self.session.get(URL, headers={'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity', 'If-Range': self.etag}, timeout=30)
        r.raise_for_status()
        if r.status_code != 206 or r.headers.get('Content-Range') != f'bytes {start}-{end}/{self.size}' or r.headers.get('ETag') != self.etag or (len(r.content) != size):
            raise RuntimeError('Workbook changed or invalid byte range')
        self.pos += size
        return r.content

    def close(self):
        self.session.close()
        super().close()

def _read_entry(z, path, max_bytes):
    i = z.getinfo(path)
    if i.file_size > max_bytes or i.compress_size > 4000000:
        raise RuntimeError('Unexpected worksheet size')
    data = z.read(i)
    if b'<!DOCTYPE' in data.upper():
        raise RuntimeError('Unsafe XML document')
    return ET.fromstring(data)

def _col(n):
    out = ''
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out

def search(year, age='', table='1.1', offset=0, limit=10):
    if isinstance(year, bool) or not isinstance(year, int) or (not 1950 <= year <= 2050):
        raise ValueError('year must be 1950–2050')
    if table not in ('1.1', '1.2') or not isinstance(age, str) or len(age) > 100:
        raise ValueError('invalid table or age')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('invalid pagination')
    with _RangeFile() as remote, zipfile.ZipFile(remote) as z:
        book = _read_entry(z, 'xl/workbook.xml', 200000)
        relationships = _read_entry(z, 'xl/_rels/workbook.xml.rels', 200000)
        ids = [x.attrib.get(REL) for x in book.iter(MAIN + 'sheet') if x.attrib.get('name') == table]
        if len(ids) != 1:
            raise RuntimeError('Requested sheet not found uniquely')
        targets = [x.attrib.get('Target', '') for x in relationships if x.attrib.get('Id') == ids[0]]
        if len(targets) != 1 or not re.fullmatch('worksheets/sheet\\d+\\.xml', targets[0]):
            raise RuntimeError('Unexpected worksheet relationship')
        shared = _read_entry(z, 'xl/sharedStrings.xml', 2000000)
        strings = [''.join((t.text or '' for t in x.iter(MAIN + 't'))) for x in shared.findall(MAIN + 'si')]
        sheet = _read_entry(z, 'xl/' + targets[0], 4000000)
        rows = {}
        for row in sheet.iter(MAIN + 'row'):
            number = int(row.attrib['r'])
            cells = {}
            for c in row.findall(MAIN + 'c'):
                ref = c.attrib.get('r', '')
                m = re.fullmatch('([A-Z]+)\\d+', ref)
                if not m:
                    continue
                v = c.find(MAIN + 'v')
                raw = v.text if v is not None and v.text is not None else None
                if raw is not None and c.attrib.get('t') == 's':
                    raw = strings[int(raw)]
                cells[m.group(1)] = raw
            rows[number] = cells
        h = rows.get(14, {})
        yearcols = [key for key, val in h.items() if val == str(year)]
        if len(yearcols) != 1:
            raise RuntimeError('Year header missing or ambiguous')

        def tonum(s):
            n = 0
            for ch in s:
                n = n * 26 + ord(ch) - 64
            return n
        idx = tonum(yearcols[0])
        columns = [_col(idx + i) for i in range(3)]
        if [rows.get(15, {}).get(c) for c in columns] != ['Hombre', 'Mujer', 'Total']:
            raise RuntimeError('Sex header mismatch')
        items = []
        for n in sorted(rows):
            if n < 16:
                continue
            row = rows[n]
            label = row.get('B')
            if not label or not any((row.get(c) is not None for c in columns)) or age.casefold() not in label.casefold():
                continue
            items.append({'row': n, 'age_raw': label, 'values_raw': {k: row.get(c) for k, c in zip(('Hombre', 'Mujer', 'Total'), columns)}})
        return {'source': 'Ecuador INEC Estimaciones y Proyecciones, revisión 2024', 'source_page': PAGE, 'workbook_url': URL, 'sheet': table, 'year': year, 'source_columns': columns, 'unit': 'persons', 'population_reference': '30 June', 'status': 'estimate' if year <= 2022 else 'projection', 'matches': len(items), 'offset': offset, 'items': items[offset:offset + limit], 'note': 'National table only; 2023–2050 are projections, not observed census counts; 1950–2022 estimates. Table 1.1 is single-year ages, 1.2 five-year ages; totals overlap component groups. Values are cached XML strings, no rounding or conversion. Server must support validated byte ranges and stable ETag; selected worksheet only, not whole 56 MB workbook.'}
