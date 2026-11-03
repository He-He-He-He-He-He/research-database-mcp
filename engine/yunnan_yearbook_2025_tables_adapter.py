"""Read tables from the official 2025 Yunnan Statistical Yearbook ZIP via HTTPS range requests."""
import release_runtime
import io
import re
import zipfile
import requests
import openpyxl
URL = 'https://stats.yn.gov.cn/zwgk/zfxxgk/fdzdgknr/tjsj/tjnj/202605/P020260723540390408353.zip'
PAGE = 'https://stats.yn.gov.cn/zwgk/zfxxgk/fdzdgknr/tjsj/tjnj/202605/t20260507_3052633.html'

class RangeFile(io.RawIOBase):

    def __init__(self):
        self.session = requests.Session()
        r = self.session.get(URL, headers={'Range': 'bytes=0-0', 'Accept-Encoding': 'identity'}, timeout=30)
        r.raise_for_status()
        m = re.fullmatch('bytes 0-0/(\\d+)', r.headers.get('Content-Range', ''))
        if r.status_code != 206 or not m or len(r.content) != 1:
            raise ValueError('official server does not support validated ranges')
        self.size = int(m.group(1))
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        new = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset if whence == 2 else -1
        if new < 0:
            raise ValueError('invalid seek')
        self.pos = new
        return new

    def read(self, size=-1):
        if size is None or size < 0:
            size = self.size - self.pos
        size = min(size, max(0, self.size - self.pos))
        if not size:
            return b''
        if size > 8000000:
            raise ValueError('refusing oversized range read')
        start = self.pos
        end = start + size - 1
        r = self.session.get(URL, headers={'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'}, timeout=30)
        r.raise_for_status()
        if r.status_code != 206 or r.headers.get('Content-Range') != f'bytes {start}-{end}/{self.size}' or len(r.content) != size:
            raise ValueError('invalid ranged response')
        self.pos += size
        return r.content

def catalog(keyword=''):
    with zipfile.ZipFile(RangeFile()) as archive:
        return [{'path': i.filename, 'size': i.file_size} for i in archive.infolist() if i.filename.lower().endswith('.xlsx') and keyword in i.filename]

def table(path):
    with zipfile.ZipFile(RangeFile()) as archive:
        allowed = {i.filename: i for i in archive.infolist() if i.filename.lower().endswith('.xlsx') and i.file_size <= 8000000}
        if path not in allowed:
            raise ValueError('table not found in official archive')
        data = archive.read(allowed[path])
    book = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    sheets = []
    for s in book.worksheets:
        rows = []
        for raw in s.iter_rows(values_only=True):
            row = list(raw)
            while row and row[-1] is None:
                row.pop()
            rows.append(row)
        while rows and (not rows[-1]):
            rows.pop()
        sheets.append({'name': s.title, 'rows': rows, 'merged_cells': [str(x) for x in s.merged_cells.ranges]})
    return {'source': '云南省统计局《云南统计年鉴2025》', 'source_url': URL, 'official_page': PAGE, 'path': path, 'sheets': sheets}
