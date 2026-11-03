"""Hangzhou July 2017 economic table from the official government gazette PDF."""
import release_runtime
import subprocess
import contextlib
import sys
import fitz
URL = 'https://zfgb.hangzhou.gov.cn/upload/default/bigfile/2025/06/13/20250613_fcf2c38d9bda9135c6ad53901d62a3b1.pdf'
TITLE = '2017年7月份杭州市国民经济主要统计指标'

def table():
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '45', URL], capture_output=True, check=True, timeout=50)
    if not p.stdout.startswith(b'%PDF'):
        raise ValueError('upstream is not PDF')
    document = fitz.open(stream=p.stdout, filetype='pdf')
    candidates = []
    for index, page in enumerate(document):
        text = page.get_text()
        if TITLE in ''.join(text.split()):
            with contextlib.redirect_stdout(sys.stderr):
                found = page.find_tables()
            for tab in found.tables:
                rows = tab.extract()
                if rows and len(rows[0]) == 5 and ('单位' in ''.join((rows[0][1] or '').split())) and any(('社会消费品零售额' in (row[0] or '') for row in rows[1:])):
                    candidates.append({'pdf_page': index + 1, 'rows': rows, 'page_text': text})
    if len(candidates) != 1:
        raise ValueError('matching table not found or ambiguous')
    return {'source': '杭州市统计局，经杭州市人民政府公报发布', 'source_url': URL, 'year': 2017, 'month': 7, 'title': TITLE, **candidates[0]}
