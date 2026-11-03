"""检索浙江大学图书馆公开的 Brill 2022 订购书单快照。"""
import release_runtime
from pathlib import Path
from datetime import date, datetime
from openpyxl import load_workbook
FILE = Path(__file__).resolve().parent / '浙大Brill电子书2022书单.xlsx'

def zju_brill_books_2022(keyword='', page=1, page_size=20):
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
            d = {headers[i]: v.isoformat() if isinstance(v, (date, datetime)) else v for i, v in enumerate(row) if i < len(headers) and headers[i]}
            if d.get('书名（主标题）') and (not q or any((q in str(v).casefold() for v in d.values() if v is not None))):
                rows.append(d)
    finally:
        w.close()
    return {'source': '浙大图书馆 Brill 2022 订购书单快照', 'keyword': keyword, 'total': len(rows), 'page': page, 'items': rows[(page - 1) * page_size:page * page_size], 'note': '馆方历史书单本地筛选，不代表实时或完整订购目录；原表含 HTTP 链接，逐项权限未验证。'}
