"""检索浙大图书馆公开的两份历史出版社书单快照。"""
import release_runtime
from pathlib import Path
from datetime import datetime, date
from openpyxl import load_workbook
ROOT = Path(__file__).resolve().parent
FILES = {'princeton_2018': '浙大2018Princeton书单.xlsx', 'harvard_2019': '浙大2019Harvard书单.xlsx'}

def zju_degruyter_booklists(collection, keyword='', page=1, page_size=20):
    if collection not in FILES:
        raise ValueError('collection 须为 princeton_2018 或 harvard_2019')
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词须不超过200字')
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or (not 1 <= page_size <= 100):
        raise ValueError('页码须大于零，每页1到100条')
    w = load_workbook(ROOT / FILES[collection], read_only=True, data_only=True)
    try:
        s = w.worksheets[0]
        it = s.iter_rows(values_only=True)
        raw = next(it)
        headers = [str(x).strip() if x is not None else '' for x in raw]
        rows = []
        q = keyword.strip().casefold()
        for row in it:
            d = {headers[i]: v.isoformat() if isinstance(v, (date, datetime)) else v for i, v in enumerate(row) if i < len(headers) and headers[i]}
            if d.get('Title') and (not q or any((q in str(v).casefold() for v in d.values() if v is not None))):
                rows.append(d)
    finally:
        w.close()
    return {'source': '浙大图书馆馆藏历史书单本地快照', 'collection': collection, 'keyword': keyword, 'total': len(rows), 'page': page, 'items': rows[(page - 1) * page_size:page * page_size], 'note': '馆方历史新增书单；检索匹配行非当前完整订购清单，电子书逐项权限及 DOI 链接未验证。'}
