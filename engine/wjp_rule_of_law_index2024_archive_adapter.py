"""World Justice Project Rule of Law Index 2024 historical data workbook."""
import release_runtime
import argparse, hashlib, json, os, re, tempfile
from pathlib import Path
import openpyxl, requests
URL = 'https://worldjusticeproject.org/rule-of-law-index/downloads/2024_wjp_rule_of_law_index_HISTORICAL_DATA_FILE.xlsx'
PAGE = 'https://worldjusticeproject.org/rule-of-law-index/'
SHA = '811e98e8074dad740dfc9c6a690b494c12680e88b4f5daab5d108c97376649be'
CACHE = release_runtime.home() / '.cache' / 'zju-research-toolkit' / 'WJP_Rule_of_Law_Index_2024_Historical.xlsx'

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
        with tempfile.NamedTemporaryFile(dir=CACHE.parent, prefix='.wjp2024-', delete=False) as f:
            tmp = Path(f.name)
            size = 0
            with requests.get(URL, stream=True, timeout=60) as r:
                r.raise_for_status()
                for c in r.iter_content(1048576):
                    size += len(c)
                    if size > 10000000:
                        raise ValueError('file exceeds size limit')
                    f.write(c)
        if _hash(tmp) != SHA:
            raise ValueError('source checksum changed; manual review required')
        os.replace(tmp, CACHE)
        return CACHE
    finally:
        if tmp and tmp.exists():
            tmp.unlink()

def query(code):
    if not isinstance(code, str) or not re.fullmatch('[A-Z]{3}', code):
        raise ValueError('use exact uppercase three-letter source code')
    w = openpyxl.load_workbook(_file(), read_only=True, data_only=True)
    try:
        s = w['WJP ROL Index 2024 Scores']
        rows = list(s.iter_rows(values_only=True))
        matches = [i for i, v in enumerate(rows[1]) if v == code]
        if len(matches) > 1:
            raise ValueError('ambiguous country code')
        values = []
        if matches:
            col = matches[0]
            values = [{'excel_row': i + 1, 'label': r[0], 'value': r[col]} for i, r in enumerate(rows) if r[0] is not None]
        hs = w['Historical Data']
        it = hs.iter_rows(values_only=True)
        h = next(it)
        history = []
        for n, r in enumerate(it, 2):
            if r[3] == code:
                history.append({'excel_row': n, 'fields': [{'column': i + 1, 'label': k, 'value': r[i]} for i, k in enumerate(h)]})
        return {'source': URL, 'source_page': PAGE, 'file_edition': '2024', 'http_last_modified_observed': '2026-11-02T08:13:07Z', 'sha256': SHA, 'country_code': code, 'found': bool(matches), 'scores_2024': values, 'historical_rows': history, 'note': 'World Justice Project is an independent non-governmental organization. Its index aggregates household and expert experience/perception surveys, not official law or objective case totals; country coverage, instruments, comparability, uncertainty and source-year methodology require review. File labelled 2024 but current server modification timestamp was observed on 2026-11-02; this cannot establish availability or identical bytes at a historical cutoff. Missing is not zero. Preserve raw scores and original dimensions; no reclassification. Check terms and the methodological report before reuse.'}
    finally:
        w.close()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('country')
    a = p.parse_args()
    print(json.dumps(query(a.country), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
