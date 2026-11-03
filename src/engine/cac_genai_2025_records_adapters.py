"""国家网信办 2025 年部分生成式 AI 备案/登记清单公开 PDF。"""
import release_runtime
from pathlib import Path
from contextlib import redirect_stdout
import sys
ROOT = Path(__file__).resolve().parent / '数据' / '生成式AI备案'
BATCHES = {'2025_04-06': {'url': 'https://www.tjcac.gov.cn/wxdt/qg/202509/W020250911379864844334.pdf', 'split': 4, 'registered': (347, 439), 'filed': (160, 233)}, '2025_07-08': {'url': 'https://www.tjcac.gov.cn/wxdt/qg/202601/W020260112388221575456.pdf', 'split': 4, 'registered': (440, 538), 'filed': (237, 263)}, '2025_09-10': {'url': 'https://www.tjcac.gov.cn/wxdt/qg/202511/W020251112373340215382.pdf', 'split': 3, 'registered': (539, 611), 'filed': (264, 306)}, '2025_11-12': {'url': 'https://www.tjcac.gov.cn/wxdt/qg/202601/W020260112388221873525.pdf', 'split': 6, 'registered': (612, 748), 'filed': (307, 435)}}

def cac_genai_2025_batches():
    return [{'batch': k, 'source_url': v['url']} for k, v in BATCHES.items()]

def cac_genai_2025_records(batch, keyword='', kind=None):
    """检索原表单元格；kind 为 registered（国家备案）或 filed（地方登记）。"""
    if batch not in BATCHES or kind not in (None, 'registered', 'filed'):
        raise ValueError('未知批次或类别')
    try:
        import fitz
    except ImportError as exc:
        raise ImportError('需要 PyMuPDF：pip install PyMuPDF') from exc
    meta = BATCHES[batch]
    doc = fitz.open(ROOT / (batch + '.pdf'))
    records = []
    try:
        for i, page in enumerate(doc):
            with redirect_stdout(sys.stderr):
                tables = page.find_tables().tables
            if len(tables) != 1:
                raise ValueError(f'PDF 第 {i + 1} 页表格结构异常')
            for cells in tables[0].extract():
                if not cells or cells[0] == '序号':
                    continue
                if len(cells) != 6 or not (cells[0] or '').strip().isdigit():
                    raise ValueError(f'PDF 第 {i + 1} 页发现未识别行')
                records.append({'batch': batch, 'kind': 'registered' if i < meta['split'] else 'filed', 'pdf_page': i + 1, '序号': cells[0], '属地': cells[1], '大模型名称': cells[2], '备案单位': cells[3], '备案编号': cells[4], '备案时间': cells[5], 'source_url': meta['url']})
    finally:
        doc.close()
    for k in ('registered', 'filed'):
        lo, hi = meta[k]
        actual = [int(x['序号']) for x in records if x['kind'] == k]
        if sorted(actual) != list(range(lo, hi + 1)):
            raise ValueError(f'{batch} {k} 行号缺失或重复，停止解析')
    needle = ''.join(keyword.split()).casefold()
    return [r for r in records if (kind is None or r['kind'] == kind) and needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
