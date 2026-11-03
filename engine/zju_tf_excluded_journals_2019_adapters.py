"""读取浙大图书馆公开的 T&F 2019 移出期刊历史附件。"""
import release_runtime
from pathlib import Path
from openpyxl import load_workbook
FILE = Path(__file__).resolve().parent / '浙大2019TF移出期刊.xlsx'

def zju_tf_excluded_journals_2019(keyword='', page=1, page_size=20):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词须不超过200字')
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or (not 1 <= page_size <= 100):
        raise ValueError('页码须大于零，每页1到100条')
    w = load_workbook(FILE, read_only=True, data_only=True)
    try:
        it = w.worksheets[0].iter_rows(values_only=True)
        headers = [str(x).strip() if x is not None else '' for x in next(it)]
        rows = []
        q = keyword.strip().casefold()
        for row in it:
            if not isinstance(row[0], int) or not row[2]:
                continue
            d = {headers[i]: v for i, v in enumerate(row) if i < len(headers) and headers[i]}
            if not q or any((q in str(v).casefold() for v in d.values() if v is not None)):
                rows.append(d)
    finally:
        w.close()
    return {'source': '浙大图书馆 T&F 2019 移出期刊附件', 'keyword': keyword, 'total': len(rows), 'page': page, 'items': rows[(page - 1) * page_size:page * page_size], 'note': '2019 年历史移出清单，不是现有订购或目前不能访问的证明；具体期刊当前状态以官方为准。'}
