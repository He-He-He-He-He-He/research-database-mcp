"""2026 年 3—4 月生成式 AI 清单：第三方转载，尚未与原件逐项核验。"""
import release_runtime
from pathlib import Path
from contextlib import redirect_stdout
import sys
ROOT = Path(__file__).resolve().parent / '数据' / '生成式AI备案'
FILES = {'registered': ('2026_03-04_备案_第三方转载.pdf', 'https://www.bei-an.com.cn/Upload/ueditor/php/upload/file/20260713/1783913027769670.pdf', 797, 868), 'filed': ('2026_03-04_登记_第三方转载.pdf', 'https://www.bei-an.com.cn/Upload/ueditor/php/upload/file/20260713/1783913027629794.pdf', 482, 530)}

def cac_genai_2026_mar_apr_records(kind=None, keyword=''):
    if kind not in (None, 'registered', 'filed'):
        raise ValueError('类别须为 registered 或 filed')
    try:
        import fitz
    except ImportError as exc:
        raise ImportError('需要 PyMuPDF：pip install PyMuPDF') from exc
    records = []
    for category, (name, url, first, last) in FILES.items():
        doc = fitz.open(ROOT / name)
        batch = []
        try:
            for i, page in enumerate(doc):
                with redirect_stdout(sys.stderr):
                    tables = page.find_tables().tables
                if not tables and category == 'registered' and (i == 3) and (len(page.get_text().strip()) < 20):
                    continue
                if len(tables) != 1:
                    raise ValueError(f'{category} 第 {i + 1} 页表格结构异常')
                for cells in tables[0].extract():
                    if not cells or cells[0] == '序号':
                        continue
                    if len(cells) != 6 or not (cells[0] or '').strip().isdigit():
                        raise ValueError(f'{category} 第 {i + 1} 页未识别行')
                    batch.append({'period': '2026_03-04', 'kind': category, 'pdf_page': i + 1, '序号': cells[0], '属地': cells[1], '大模型名称': cells[2], '备案单位': cells[3], '备案编号': cells[4], '备案时间': cells[5], 'source_url': url, 'provenance': '商业网站转载，未与国家网信办原 PDF 逐条或哈希核验'})
        finally:
            doc.close()
        if sorted((int(r['序号']) for r in batch)) != list(range(first, last + 1)):
            raise ValueError(f'{category} 表格序号缺失或重复')
        records.extend(batch)
    needle = ''.join(keyword.split()).casefold()
    return [r for r in records if (kind is None or r['kind'] == kind) and needle in ''.join((str(v or '') for v in r.values())).replace('\n', '').replace(' ', '').casefold()]
