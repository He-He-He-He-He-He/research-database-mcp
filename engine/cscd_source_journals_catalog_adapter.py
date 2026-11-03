"""CSCD 2025-26 source journals, public university library spreadsheet."""
import release_runtime
from pathlib import Path
import openpyxl
FILE = Path(__file__).resolve().parent / 'CSCD来源期刊表2025-2026_湖北医药学院图书馆.xlsx'
SOURCE = 'https://lib.hbmu.edu.cn/2025/0922/c2182a92018/page.htm'
DOWNLOAD = 'https://lib.hbmu.edu.cn/_upload/article/files/1d/d5/4183f917491e8a69c132e2ef420e/51e2bcd2-68cc-4d5c-a3f9-4435e17bb09d.xlsx'
SCOPE = '湖北医药学院图书馆公开的 2025—2026 年 CSCD 来源期刊名单，原表 1504 种；仅查来源期刊及核心库／扩展库标识，不是浙大 CSCD 文献、引用检索或全文权限，也不代表其他年份名单。'

def search(keyword, page=1, limit=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为不超过 200 字的非空字符串')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('page 须为正整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit 须为 1 至 50')
    workbook = openpyxl.load_workbook(FILE, read_only=True, data_only=True)
    try:
        sheet = workbook['2025-2026年CSCD来源期刊列表']
        rows = sheet.iter_rows(values_only=True)
        title = next(rows)
        header = next(rows)
        if header[:4] != ('序号', '期刊名称', 'ISSN', '库标识'):
            raise RuntimeError('CSCD 文件表头异常')
        matches = []
        count = 0
        for row in rows:
            count += 1
            if row[0] != count:
                raise RuntimeError('CSCD 文件序号异常')
            if any((keyword.casefold() in str(row[i] or '').casefold() for i in (1, 2))):
                matches.append(dict(zip(header[:4], row[:4])))
        if count != 1504:
            raise RuntimeError('CSCD 来源期刊表数量异常')
    finally:
        workbook.close()
    start = (page - 1) * limit
    return {'source': '湖北医药学院图书馆公开的 CSCD 2025—2026 来源期刊表', 'source_page': SOURCE, 'source_file': DOWNLOAD, 'source_sha256': '2a2c51caff31c94edd0bfcba5178e30f5c464e4b17cb09886b13e85590be682c', 'keyword': keyword, 'matching_journals': len(matches), 'page': page, 'limit': limit, 'items': matches[start:start + limit], 'scope': SCOPE}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--limit', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.limit), ensure_ascii=False, indent=2))
