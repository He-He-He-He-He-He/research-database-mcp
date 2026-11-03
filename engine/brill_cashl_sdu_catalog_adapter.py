"""Public Brill-CASHL 2018–2025 ebook list published by Shandong University Weihai Library."""
import release_runtime
from pathlib import Path
import openpyxl
FILE = Path(__file__).resolve().parent / 'Brill-CASHL电子书列表2018-2025_山东大学威海馆.xlsx'
SOURCE = 'https://dnlib.wh.sdu.edu.cn/md/dn/show.aspx?dbid=236&file=show'
DOWNLOAD = 'https://library.sdu.edu.cn/dataBank/file/591.html'
HEADERS = ('E-ISBN', 'p-ISBN', '书名（主标题）', '书名（副标题）', '作者', '出版商', 'Brill学科分类', '订购年', '出版年', '价格', '主要语言', '教图爱学术平台URL', '中图易阅通URL')
SCOPE = '山东大学（威海）图书馆公开的 Brill-CASHL 2018—2025 电子书清单，按其馆方页面反映山东大学可访问范围；不是浙大全部馆藏或 CASHL 全部资源，不能证明浙大对具体条目有全文权限。原表价格仅按原值呈现，不推断币种或当前价格。'

def search(keyword, page=1, limit=10):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为不超过 200 字的非空字符串')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('page 必须为正整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 30):
        raise ValueError('limit 须为 1 至 30')
    book = openpyxl.load_workbook(FILE, read_only=True, data_only=True)
    try:
        rows = book['Sheet1'].iter_rows(values_only=True)
        if tuple(next(rows)[:13]) != HEADERS:
            raise RuntimeError('书目表头变化')
        matches = []
        count = 0
        query = keyword.strip().casefold()
        for row in rows:
            if not row[2]:
                continue
            count += 1
            if any((query in str(row[i] or '').casefold() for i in (0, 1, 2, 3, 4))):
                matches.append(dict(zip(HEADERS, row[:13])))
        if count != 7066:
            raise RuntimeError('书目数据行数量异常')
    finally:
        book.close()
    start = (page - 1) * limit
    return {'source': '山东大学（威海）图书馆公开 Brill-CASHL 电子书清单', 'source_page': SOURCE, 'source_xlsx': DOWNLOAD, 'source_sha256': '8ab3f0c1c2ee22404254046361be3d59be800dac63ccef244d28aaf95c92e28a', 'keyword': keyword, 'matching_books': len(matches), 'page': page, 'limit': limit, 'items': matches[start:start + limit], 'scope': SCOPE}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--limit', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.limit), ensure_ascii=False, indent=2, default=str))
