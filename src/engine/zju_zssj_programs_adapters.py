"""本地检索浙大图书馆公开的知识视界历史节目清单。"""
import release_runtime
from pathlib import Path
from openpyxl import load_workbook
FILE = Path(__file__).resolve().parent / '浙大知识视界2018节目清单.xlsx'

def zju_zssj_programs(keyword='', page=1, page_size=20):
    if not isinstance(keyword, str) or len(keyword) > 200:
        raise ValueError('关键词须不超过200字')
    if not isinstance(page, int) or not isinstance(page_size, int) or page < 1 or (not 1 <= page_size <= 100):
        raise ValueError('页码须大于零，每页1到100条')
    w = load_workbook(FILE, read_only=True, data_only=True)
    rows = []
    q = keyword.strip().casefold()
    try:
        for s in w:
            it = s.iter_rows(values_only=True)
            headers = [str(x).strip() if x is not None else '' for x in next(it)]
            for row in it:
                d = {headers[i]: v for i, v in enumerate(row) if i < len(headers) and headers[i]}
                if d.get('节目编号') and d.get('标题') and (not q or any((q in str(v).casefold() for v in d.values() if v is not None))):
                    rows.append({'sheet': s.title, **d})
    finally:
        w.close()
    return {'source': '浙大图书馆知识视界历史节目清单', 'keyword': keyword, 'total': len(rows), 'page': page, 'items': rows[(page - 1) * page_size:page * page_size], 'note': '馆方历史清单本地筛选，非当前完整资源、视频播放或权限验证；时长未提供单位时不得推断。'}
