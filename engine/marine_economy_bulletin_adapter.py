"""自然资源部全国海洋经济统计公报抽样原始 PDF。"""
import release_runtime
import contextlib, io, hashlib, subprocess
import fitz
REPORTS = {2022: ('https://m.mnr.gov.cn/gk/tzgg/202304/P020230414430782331822.pdf', '自然资源部原站'), 2024: ('https://www.gov.cn/lianbo/bumen/202502/P020250224776531656783.pdf', '中国政府网转载自然资源部公报'), 2025: ('https://www.hunan.gov.cn/zqt/zcsd/202603/33934144/files/dc3787f5538b4d93ad2a08427a2812bc.pdf', '湖南省政府转载自然资源部公报')}

def catalog():
    return {'source': '自然资源部中国海洋经济统计公报', 'items': [{'year': y, 'url': u, 'hosting': h} for y, (u, h) in REPORTS.items()], 'note': '固定收录 2022、2024、2025 三份，不是全部历史；年度表通常含上一年对比。'}

def report(year, keyword=''):
    if isinstance(year, bool) or not isinstance(year, int) or year not in REPORTS:
        raise ValueError('目前仅收录 2022、2024、2025')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词最多100字')
    u, host = REPORTS[year]
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '25', '--max-filesize', '15000000', u], capture_output=True, timeout=30)
    if r.returncode or len(r.stdout) > 15000000 or (not r.stdout.startswith(b'%PDF-')):
        raise ValueError('响应不是可识别 PDF、超过限制或来源不可用')
    d = fitz.open(stream=r.stdout, filetype='pdf')
    if len(d) > 50:
        raise ValueError('PDF 页数过多')
    pages = []
    expanded = []
    for p in d:
        text = p.get_text()
        tables = []
        with contextlib.redirect_stdout(io.StringIO()):
            for t in p.find_tables().tables:
                tables.append(t.extract())
        for t in tables:
            for row in t:
                if len(row) != 5 or not all((isinstance(v, str) for v in row)):
                    continue
                cols = [v.splitlines() for v in row]
                if len(cols[0]) < 5 or len({len(x) for x in cols}) != 1:
                    continue
                for vals in zip(*cols):
                    if keyword and keyword not in vals[0]:
                        continue
                    expanded.append({'item': vals[0], 'current_total': vals[1], 'current_growth': vals[2], 'previous_total': vals[3], 'previous_growth': vals[4], 'page': p.number + 1})
        if not keyword or keyword in text:
            pages.append({'page': p.number + 1, 'text': text, 'tables': tables})
    return {'source': '自然资源部中国海洋经济统计公报', 'year': year, 'source_url': u, 'hosting': host, 'sha256': hashlib.sha256(r.stdout).hexdigest(), 'pages': pages, 'aligned_rows': expanded, 'note': '仅当 PDF 表格 5 列行数完全一致时展开对应行；自动抽取、图表及统计口径需对照原 PDF，原表总量和增速单位及可比价口径不可混淆。'}
