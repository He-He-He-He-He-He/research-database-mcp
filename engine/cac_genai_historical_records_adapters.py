"""网信办生成式 AI 备案历史表及 2025 年 4—6 月另一转载版本。"""
import release_runtime
from pathlib import Path
from contextlib import redirect_stdout
import sys
ROOT = Path(__file__).resolve().parent / '数据' / '生成式AI备案'
BATCHES = {'2024_04': ('2024_04.pdf', 'https://www.tjcac.gov.cn/wxdt/qg/202511/W020251112373334243305.pdf', 5, (1, 117), None), '2024_08': ('2024_08.pdf', 'https://www.tjcac.gov.cn/wxdt/qg/202504/W020250408621884294610.pdf', 3, (118, 188), (1, 26)), '2024_11': ('2024_11.pdf', 'https://www.tjcac.gov.cn/wxdt/qg/202511/W020251112373336231827.pdf', 3, (189, 252), (27, 57)), '2025_01': ('2025_01.pdf', 'https://www.tjcac.gov.cn/wxdt/qg/202504/W020250408621884424647.pdf', 3, (253, 302), (58, 105)), '2025_03': ('2025_03_武汉网安协会转载.pdf', 'https://www.whcsa.org.cn/upload/default/20250715/b3123fb604f45d59d9a69ef80d7fcdad.pdf', 3, (303, 346), (106, 159)), '2025_04-06_alt': ('2025_04-06_202601转载版.pdf', 'https://www.tjcac.gov.cn/wxdt/qg/202601/W020260112388221433548.pdf', 3, (347, 439), (160, 236))}

def cac_genai_historical_batches():
    return [{'batch': k, 'source_url': v[1]} for k, v in BATCHES.items()]

def cac_genai_historical_records(batch, keyword='', kind=None):
    if batch not in BATCHES or kind not in (None, 'registered', 'filed'):
        raise ValueError('未知批次或类别')
    try:
        import fitz
    except ImportError as exc:
        raise ImportError('需要 PyMuPDF：pip install PyMuPDF') from exc
    filename, source, split, registered, filed = BATCHES[batch]
    doc = fitz.open(ROOT / filename)
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
                label = 'registered' if i < split else 'filed'
                keys = ('应用/功能名称', '登记单位', '上线编号', '登记时间') if batch == '2025_03' and label == 'filed' else ('模型名称', '备案单位', '备案编号', '备案时间')
                row = {'batch': batch, 'kind': label, 'pdf_page': i + 1, '序号': cells[0], '属地': cells[1], 'source_url': source, 'source_warning': '此版第 436 行编号在原 PDF 中被截断' if batch == '2025_04-06_alt' and cells[0] == '436' else ''}
                row.update(dict(zip(keys, cells[2:])))
                records.append(row)
    finally:
        doc.close()
    for k, bounds in (('registered', registered), ('filed', filed)):
        actual = sorted((int(r['序号']) for r in records if r['kind'] == k))
        if actual != (list(range(bounds[0], bounds[1] + 1)) if bounds else []):
            raise ValueError(f'{batch} {k} 序号不完整')
    needle = ''.join(keyword.split()).casefold()
    return [r for r in records if (kind is None or r['kind'] == kind) and needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
