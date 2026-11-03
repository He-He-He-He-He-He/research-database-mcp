"""本地检索浙大图书馆公开的 ASCE 历史电子书书单。"""
import release_runtime
from pathlib import Path
from datetime import date, datetime
from openpyxl import load_workbook
FILE = Path(__file__).resolve().parent / '浙大ASCE2019电子书书单.xlsx'

def zju_asce_books_2019(keyword='', page=1, page_size=20):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词须不超过200字')
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or (not 1 <= page_size <= 100):
        raise ValueError('页码须大于零，每页1到100条')
    w = load_workbook(FILE, read_only=True, data_only=True)
    try:
        it = w.worksheets[0].iter_rows(values_only=True)
        next(it)
        headers = [str(x).strip() if x is not None else '' for x in next(it)]
        rows = []
        q = keyword.strip().casefold()
        for row in it:
            if not isinstance(row[0], int) or not row[1]:
                continue
            d = {headers[i]: v.isoformat() if isinstance(v, (date, datetime)) else v for i, v in enumerate(row) if i < len(headers) and headers[i]}
            if not q or any((q in str(v).casefold() for v in d.values() if v is not None)):
                rows.append(d)
    finally:
        w.close()
    return {'source': '浙大图书馆 ASCE 电子书历史书单', 'keyword': keyword, 'total': len(rows), 'page': page, 'items': rows[(page - 1) * page_size:page * page_size], 'note': '历史书单本地筛选，不代表完整或当前订购目录；书籍链接及全文权限未逐项验证。'}
