"""Yale 2026 EPI scores, trends, and ranks: original workbook."""
import release_runtime
import io, re
import requests, openpyxl
URL = 'https://www.epi.yale.edu/downloads/epi2026results2026-07-07.xlsx'
DOCS = 'https://www.epi.yale.edu/2026-methodology'
LICENSE = 'https://epi.yale.edu/content-page/16/faqs'
NOTE = '耶鲁大学等研究团队编制的 2026 环境绩效指数，非政府官方统计；评分是综合指标，不是原始监测值。本文件按 CC BY-NC-SA 4.0 仅限非商业用途，使用需署名并遵守相同方式共享。不同版本方法和数据会改变，不可直接把不同版本分数拼成时间序列；部分指标可能涉及插值或历史值延伸，数据年份因指标不同，趋势为采用 2026 方法回算而非历史发布时快照；请核技术附录。'

def economy(code, session=None):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z]{3}', code):
        raise ValueError('请输入三字母经济体代码，如 EGY')
    with (session or requests).get(URL, timeout=35, stream=True, headers={'User-Agent': 'PersonalResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        b = bytearray()
        for c in r.iter_content(65536):
            b.extend(c)
            if len(b) > 10 * 1024 * 1024:
                raise ValueError('EPI 工作簿超过 10 MiB')
        url = r.url
    wb = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    try:
        ws = wb['data']
        rows = ws.iter_rows(values_only=True)
        columns = list(next(rows))
        matches = [list(row) for row in rows if row and isinstance(row[0], str) and (row[0].upper() == code.upper())]
        readme = [list(row) for row in wb['README'].iter_rows(values_only=True)]
    finally:
        wb.close()
    return {'source': 'Yale Environmental Performance Index 2026', 'source_url': url, 'methodology': DOCS, 'license_url': LICENSE, 'license': 'CC BY-NC-SA 4.0; non-commercial only', 'note': NOTE, 'code': code.upper(), 'columns': columns, 'rows': matches, 'readme': readme}
