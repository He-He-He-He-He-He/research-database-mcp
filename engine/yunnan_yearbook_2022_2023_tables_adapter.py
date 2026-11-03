"""Read tables from the official 2022–2023 Yunnan Statistical Yearbook ZIP via HTTPS range requests."""
import release_runtime
import io
import re
import zipfile
import requests
import sys
from pathlib import Path
try:
    import xlrd
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
    import xlrd
BASE = 'https://stats.yn.gov.cn/zwgk/zfxxgk/fdzdgknr/tjsj/tjnj/'
URLS = {2022: BASE + '202607/P020260723390113972418.zip', 2023: BASE + '202403/P020260723391207147356.zip'}
PAGES = {2022: BASE + '202607/t20260716_3205138.html', 2023: BASE + '202403/t20240329_1202875.html'}

def _url(year):
    if isinstance(year, bool) or year not in URLS:
        raise ValueError('available editions: 2022, 2023')
    return URLS[year]

class RangeFile(io.RawIOBase):

    def __init__(self, url):
        self.url = url
        self.session = requests.Session()
        r = self.session.get(self.url, headers={'Range': 'bytes=0-0', 'Accept-Encoding': 'identity'}, timeout=30)
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
        r = self.session.get(self.url, headers={'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'}, timeout=30)
        r.raise_for_status()
        if r.status_code != 206 or r.headers.get('Content-Range') != f'bytes {start}-{end}/{self.size}' or len(r.content) != size:
            raise ValueError('invalid ranged response')
        self.pos += size
        return r.content

def catalog(year, keyword=''):
    with zipfile.ZipFile(RangeFile(_url(year))) as archive:
        return [{'path': i.filename, 'size': i.file_size} for i in archive.infolist() if i.filename.lower().endswith('.xls') and keyword in i.filename]

def table(year, path):
    with zipfile.ZipFile(RangeFile(_url(year))) as archive:
        allowed = {i.filename: i for i in archive.infolist() if i.filename.lower().endswith('.xls') and i.file_size <= 8000000}
        if path not in allowed:
            raise ValueError('table not found in official archive')
        data = archive.read(allowed[path])
    book = xlrd.open_workbook(file_contents=data, formatting_info=True)
    sheets = [{'name': s.name, 'rows': [s.row_values(i) for i in range(s.nrows)], 'merged_cells': s.merged_cells} for s in book.sheets()]
    return {'source': f'云南省统计局《云南统计年鉴{year}》', 'source_url': _url(year), 'official_page': PAGES[year], 'path': path, 'sheets': sheets}
