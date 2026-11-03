"""UN Women and UN Statistics Gender Snapshot 2024 supplementary data workbook."""
import release_runtime
import argparse, hashlib, json, os, tempfile
from pathlib import Path
import openpyxl, requests
URL = 'https://unstats.un.org/sdgs/gender-snapshot/2024/data-sheets.xlsx'
PAGE = 'https://unstats.un.org/sdgs/gender-snapshot/2024/'
SHA = 'f1f56e31826bb8b0fc568ffc85f51023733b610d76153087c632503dbcdd77f8'
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit' / 'UN_GenderSnapshot2024_sheets.xlsx'

def _hash(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda: f.read(1048576), b''):
            h.update(c)
    return h.hexdigest()

def _file():
    if CACHE.is_file() and _hash(CACHE) == SHA:
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(dir=CACHE.parent, prefix='.gender2024-', delete=False) as f:
            tmp = Path(f.name)
            size = 0
            with requests.get(URL, stream=True, timeout=90) as r:
                r.raise_for_status()
                for c in r.iter_content(1048576):
                    size += len(c)
                    if size > 8000000:
                        raise ValueError('source exceeds size limit')
                    f.write(c)
        if _hash(tmp) != SHA:
            raise ValueError('source checksum changed; manual review required')
        os.replace(tmp, CACHE)
        return CACHE
    finally:
        if tmp and tmp.exists():
            tmp.unlink()

def catalog():
    w = openpyxl.load_workbook(_file(), read_only=True, data_only=True)
    try:
        return {'source': URL, 'source_page': PAGE, 'report_launch_date': '2024-09-16', 'http_last_modified_observed': '2024-10-22T14:22:28Z', 'sha256': SHA, 'sheets': w.sheetnames, 'note': 'Report launch predates file server modification; current workbook bytes and availability on launch day are not established.'}
    finally:
        w.close()

def table(sheet):
    if not isinstance(sheet, str) or len(sheet) > 70:
        raise ValueError('invalid sheet')
    w = openpyxl.load_workbook(_file(), read_only=False, data_only=True)
    wf = openpyxl.load_workbook(_file(), read_only=False, data_only=False)
    try:
        if sheet not in w.sheetnames:
            raise ValueError('unknown sheet; use catalog')
        s = w[sheet]
        sf = wf[sheet]
        rows = []
        for row in s.iter_rows():
            cells = []
            for c in row:
                f = sf[c.coordinate]
                if c.value is None and f.value is None:
                    continue
                v = c.value.isoformat() if hasattr(c.value, 'isoformat') else c.value
                item = {'cell': c.coordinate, 'value': v, 'number_format': c.number_format}
                if f.data_type == 'f':
                    item['formula'] = f.value
                cells.append(item)
            if cells:
                rows.append({'row': row[0].row, 'cells': cells})
        return {'source': URL, 'source_page': PAGE, 'report_launch_date': '2024-09-16', 'http_last_modified_observed': '2024-10-22T14:22:28Z', 'sha256': SHA, 'sheet': sheet, 'merged_ranges': [str(x) for x in s.merged_cells.ranges], 'rows': rows, 'note': 'UN Women and UN DESA Gender Snapshot 2024 supplementary data sheets. The current workbook server modification is 22 October 2024, after report launch, and does not prove historic byte identity. Each sheet can contain several distinct tables, model projections or reported estimates with different populations and time periods. Preserve raw values, cell coordinates, formats, formulas, headers and notes; do not interpret an empty cell as zero or infer merged headers. Number format does not replace the source definition. Inspect original workbook and linked references.'}
    finally:
        w.close()
        wf.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['catalog', 'table'])
    p.add_argument('--sheet')
    a = p.parse_args()
    print(json.dumps(catalog() if a.action == 'catalog' else table(a.sheet), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
