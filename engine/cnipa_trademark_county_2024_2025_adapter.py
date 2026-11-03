"""CNIPA county trademark PDFs, conservative extraction of complete county rows."""
import release_runtime
import hashlib, re
import requests, fitz
SOURCES = {'2024Q4': ('https://sbj.cnipa.gov.cn/sbj/sbsj/202501/W020250103577772107350.pdf', '申请/注册：2023-12-16至2024-12-15；有效量：截至2024-12-15'), '2025Q1': ('https://sbj.cnipa.gov.cn/sbj/sbsj/202504/W020250408360267536128.pdf', '申请/注册：2024-12-16至2025-03-15；有效量：截至2025-03-15'), '2025Q3': ('https://sbj.cnipa.gov.cn/sbj/sbsj/202510/W020251016423834571089.pdf', '申请/注册：2024-12-16至2025-09-15；有效量：截至2025-09-15')}

def catalog():
    return [{'period': k, 'url': v[0], 'coverage': v[1]} for k, v in SOURCES.items()]

def search(period, keyword, limit=100):
    if not isinstance(period, str) or period not in SOURCES:
        raise ValueError('period must be 2024Q4, 2025Q1, or 2025Q3')
    if not isinstance(keyword, str) or not keyword or len(keyword) > 40:
        raise ValueError('keyword required')
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError('limit 1–1000')
    url, note = SOURCES[period]
    with requests.get(url, stream=True, timeout=(10, 40), allow_redirects=False) as r:
        r.raise_for_status()
        if r.is_redirect:
            raise ValueError('unexpected redirect')
        data = bytearray()
        for c in r.iter_content(65536):
            data.extend(c)
            if len(data) > 10000000:
                raise ValueError('PDF too large')
    raw = bytes(data)
    if not raw.startswith(b'%PDF-'):
        raise ValueError('expected PDF')
    rows = []
    incomplete = 0
    with fitz.open(stream=raw, filetype='pdf') as doc:
        if len(doc) != 83:
            raise ValueError('unexpected report page count')
        for n, p in enumerate(doc):
            words = p.get_text('words')
            anchors = [w for w in words if 230 <= w[0] < 350 and re.search('[\\u4e00-\\u9fff]', w[4]) and (w[4] != '县')]
            for a in anchors:
                line = [w for w in words if abs(w[1] - a[1]) < 3]
                buckets = [[w[4] for w in line if lo <= w[0] < hi] for lo, hi in [(0, 105), (105, 230), (230, 350), (350, 440), (440, 500), (500, 590)]]
                if not all((len(v) == 1 for v in buckets)):
                    incomplete += 1
                    continue
                cells = [v[0] for v in buckets]
                if not all((re.fullmatch('\\d+', v) for v in cells[3:])):
                    incomplete += 1
                    continue
                if keyword not in ''.join(cells[:3]):
                    continue
                rows.append({'省': cells[0], '市': cells[1], '县': cells[2], '申请件数': cells[3], '注册件数': cells[4], '有效注册量': cells[5], 'pdf_page': n + 1})
    return {'source': '国家知识产权局商标局', 'period': period, 'source_url': url, 'source_sha256': hashlib.sha256(raw).hexdigest(), 'source_period_note': note, 'rows': rows[:limit], 'total_matches': len(rows), 'incomplete_rows_skipped': incomplete, 'note': '仅返回省、市、县及3个数值均能在同一坐标行识别的记录；复杂换行、汇总行等可能被跳过，结果不是完整地区清单。申请/注册为累计期间，有效注册为时点存量；必要时查看PDF原表。'}
