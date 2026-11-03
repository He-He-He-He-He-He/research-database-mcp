"""Read official Yunnan 2020 population census XLSX archive via bsdtar."""
import release_runtime
import io, os, subprocess, tempfile
import requests
from openpyxl import load_workbook
URL = 'https://stats.yn.gov.cn/zwgk/zfxxgk/fdzdgknr/tjsj/tjnj/202607/P020260716686337458968.rar'
PAGE = 'https://stats.yn.gov.cn/zwgk/zfxxgk/fdzdgknr/tjsj/tjnj/202607/t20260716_3205140.html'

class _Archive:

    def __enter__(self):
        r = requests.get(URL, timeout=90)
        r.raise_for_status()
        if len(r.content) > 50000000:
            raise ValueError('Unexpected archive size')
        f = tempfile.NamedTemporaryFile(suffix='.rar', delete=False)
        try:
            f.write(r.content)
            self.path = f.name
        finally:
            f.close()
        return self

    def __exit__(self, *args):
        os.unlink(self.path)

    def list(self):
        p = release_runtime.run(['bsdtar', '-tf', self.path], capture_output=True, check=True, timeout=60)
        return [x for x in p.stdout.decode('utf-8').splitlines() if x.startswith('excel/') and x.lower().endswith('.xlsx')]

def catalog(keyword=''):
    with _Archive() as a:
        names = a.list()
    return {'source': '云南省统计局', 'book': '云南省人口普查年鉴2020', 'source_page': PAGE, 'archive_url': URL, 'items': [{'id': n, 'title': n.removeprefix('excel/').removesuffix('.xlsx')} for n in names if keyword in n]}

def table(table_id):
    if not isinstance(table_id, str) or any((c in table_id for c in '*?[]')) or '\n' in table_id:
        raise ValueError('invalid table ID')
    with _Archive() as a:
        names = a.list()
        if names.count(table_id) != 1:
            raise ValueError('unknown or ambiguous table ID')
        p = release_runtime.run(['bsdtar', '-xOf', a.path, table_id], capture_output=True, check=True, timeout=60)
    if len(p.stdout) > 30000000 or not p.stdout.startswith(b'PK\x03\x04'):
        raise ValueError('invalid or oversized XLSX')
    w = load_workbook(io.BytesIO(p.stdout), data_only=True)
    sheets = [{'name': s.title, 'rows': [[c.value for c in row] for row in s.iter_rows()], 'merged_cells': [str(r) for r in s.merged_cells.ranges]} for s in w.worksheets]
    return {'source': '云南省统计局', 'book': '云南省人口普查年鉴2020', 'source_page': PAGE, 'archive_url': URL, 'id': table_id, 'sheets': sheets, 'merged_cells_convention': 'Excel A1 notation'}
