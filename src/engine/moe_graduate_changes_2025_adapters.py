"""查询教育部 2025 年发布的学科专业调整原表（本地 HTML 快照）。"""
import release_runtime
from pathlib import Path
from moe_education_statistics_adapters import _LeafTables
HTML_PATH = Path(__file__).with_name('教育部学科专业调整对应关系表2025.html')
SOURCE_URL = 'https://www.moe.gov.cn/srcsite/A22/s7065/202506/t20250611_1193766.html'

def _expand(rows, width):
    pending = {}
    result = []
    for row in rows:
        values = [None] * width
        next_pending = {}
        for col, (text, remaining) in pending.items():
            values[col] = text
            if remaining > 1:
                next_pending[col] = (text, remaining - 1)
        pos = 0
        for cell in row:
            while pos < width and values[pos] is not None:
                pos += 1
            colspan, rowspan = (int(cell['colspan']), int(cell['rowspan']))
            for col in range(pos, pos + colspan):
                if col >= width or values[col] is not None:
                    raise ValueError('原表合并单元格结构异常')
                values[col] = cell['text']
                if rowspan > 1:
                    next_pending[col] = (cell['text'], rowspan - 1)
            pos += colspan
        if any((x is None for x in values)):
            raise ValueError('原表存在未识别的空列')
        pending = next_pending
        result.append(values)
    return result

def search_graduate_changes_2025(keyword='', table='all'):
    """查询新旧调整关系，table 为 all、discipline 或 engineering。"""
    if table not in ('all', 'discipline', 'engineering'):
        raise ValueError('table 应为 all、discipline 或 engineering')
    parser = _LeafTables()
    parser.feed(HTML_PATH.read_text(encoding='utf-8'))
    if len(parser.tables) != 3:
        raise ValueError('原始网页表格数量异常')
    output = []
    specs = [('discipline', 1, 2, 6), ('engineering', 2, 1, 4)]
    for name, idx, head, width in specs:
        if table not in ('all', name):
            continue
        expanded = _expand(parser.tables[idx][head:], width)
        for number, (values, raw) in enumerate(zip(expanded, parser.tables[idx][head:]), 1):
            if keyword and (not any((keyword in value for value in values))):
                continue
            output.append({'table': name, 'row': number, 'values': values, 'original_cells': raw, 'source_url': SOURCE_URL, 'published_year': 2025})
    return output
