"""Library-published historical inventory related to ZJU database 1854."""
import release_runtime
from pathlib import Path
import openpyxl
BASE = Path(__file__).resolve().parent
FILE = BASE / '中国近现代本土文学作品_深圳大学城馆书目.xlsx'
ORIGINAL = BASE / '中国近现代本土文学作品_深圳大学城馆书目.xls'
SOURCE = 'https://utszlib.edu.cn/dataBank/view/3903.html'
DOWNLOAD = 'https://utszlib.edu.cn/dataBank/download/1031.html'
LIBRARY = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1854'
HEADERS = ['序號', '題名', '著者', '出版社', '出版年', '页码', '册数', '种数']

def search(keyword, page=1, limit=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为不超过 200 字的非空字符串')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码必须为正整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('每页条数须为 1 至 50')
    book = openpyxl.load_workbook(FILE, read_only=True, data_only=True)
    try:
        sheet = book['中国近现代本土文学作品']
        rows = sheet.iter_rows(values_only=True)
        if list(next(rows)[:8]) != HEADERS:
            raise RuntimeError('馆方清单表头变化')
        records = []
        expected = 1
        for row in rows:
            if not isinstance(row[0], int):
                continue
            if row[0] != expected:
                raise RuntimeError('馆方清单序号异常')
            expected += 1
            item = dict(zip(HEADERS, row[:8]))
            if any((keyword.casefold() in str(item[field] or '').casefold() for field in ('題名', '著者', '出版社', '出版年'))):
                records.append(item)
        if expected != 2782:
            raise RuntimeError('馆方清单记录数异常')
    finally:
        book.close()
    start = (page - 1) * limit
    return {'source': '深圳大学城图书馆公开的中国近现代本土文学作品总清单', 'source_page': SOURCE, 'source_download': DOWNLOAD, 'zju_related_collection': LIBRARY, 'keyword': keyword, 'total': len(records), 'page': page, 'limit': limit, 'items': records[start:start + limit], 'scope': '本地检索该馆公开历史清单，共 2652 种、2781 册，保留原表字段及原字形；浙大馆方介绍为 2654 种、2783 册，版本有差异。仅供查找相关题录，不代表浙大当前完整馆藏或全文可访问；关键词按原字形匹配。', 'source_xls_sha256': 'a06dcb0ec79d65f936c0789054e9ded0e2427d06a21505d65dacbe2499749315'}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--limit', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.limit), ensure_ascii=False, indent=2, default=str))
