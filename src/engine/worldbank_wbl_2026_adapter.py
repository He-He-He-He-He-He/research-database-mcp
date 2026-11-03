"""World Bank WBL 2026 official workbook, economy scores and topic data."""
import release_runtime
import io, re
import requests, openpyxl
URL = 'https://wbl.worldbank.org/content/dam/sites/wbl/documents/2026/WBL26_FINAL_ALL.xlsx'
CATALOG = 'https://wbl.worldbank.org/en/data/download-data'
SHEETS = {'scores': 'WBL Economy Scores', 'safety': '1. Safety', 'mobility': '2. Mobility', 'work': '3. Work', 'pay': '4. Pay', 'marriage': '5. Marriage', 'parenthood': '6. Parenthood', 'childcare': '7. Childcare', 'entrepreneurship': '8. Entrepreneurship', 'assets': '9. Assets', 'pension': '10. Pension'}
NOTE = '世界银行 Women, Business and the Law 2026 数据：法律框架、支持框架、执法感知为不同维度；执法感知来自法律专家意见，不等于实际执法统计或妇女亲身经历。总体分数 2024/2025 按 2026 方法重新计算，不能视为当年已发布版本或历史时点快照。报告年份与法律及基础数据日期不同，2026 数据截至 2025-10-01；专题表仅含 2026。保留原始多行表头、缺失值及原始数据；评分不替代法律原文。'

def economy(code, sheet='scores', session=None):
    if not isinstance(code, str) or not re.fullmatch('[A-Za-z]{3}', code):
        raise ValueError('请输入 3 位经济体代码，如 EGY')
    if sheet not in SHEETS:
        raise ValueError('未知表名，可选：' + ', '.join(SHEETS))
    with (session or requests).get(URL, timeout=40, stream=True, headers={'User-Agent': 'PersonalResearchToolkit/1.0'}) as r:
        r.raise_for_status()
        b = bytearray()
        for c in r.iter_content(65536):
            b.extend(c)
            if len(b) > 10 * 1024 * 1024:
                raise ValueError('官方工作簿超过 10 MiB')
        url = r.url
    wb = openpyxl.load_workbook(io.BytesIO(b), read_only=True, data_only=True)
    try:
        ws = wb[SHEETS[sheet]]
        nheaders = 4 if sheet == 'scores' else 3
        raw = list(ws.iter_rows(values_only=True))
        headers = [list(x) for x in raw[:nheaders]]
        rows = [list(x) for x in raw[nheaders:] if len(x) > 2 and isinstance(x[2], str) and (x[2].upper() == code.upper())]
        about = [list(row) for row in wb['About'].iter_rows(values_only=True)]
    finally:
        wb.close()
    return {'source': 'World Bank Women, Business and the Law 2026', 'source_url': url, 'catalog': CATALOG, 'sheet': SHEETS[sheet], 'code': code.upper(), 'note': NOTE, 'raw_header_rows': headers, 'rows': rows, 'about': about}
