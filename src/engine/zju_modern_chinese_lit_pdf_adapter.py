"""Page-level text search of a public institutional PDF catalogue related to ZJU collection 1854."""
import release_runtime
from pathlib import Path
import fitz
FILE = Path(__file__).resolve().parent / '中国近现代本土文学作品_深圳职大馆2654种清单.pdf'
SOURCE = 'https://library.szpu.edu.cn/databaseguide/detail/3121'
PDF = 'https://libfile.szpu.edu.cn/contentdelivery/20211115/F7BFA13DF4AFCC0234FA75257F72C976_24606AAB16AD9060C1E9978AA82D5B9F.pdf'
ZJU = 'https://libdb.zju.edu.cn/s/lib/libtb/show/1854'
SHA256 = '388e2ba58ff79eb0d60f6046e8fcd028d6ecb81621988b5bb86e4680b5804d80'

def search(keyword, page=1, limit=3):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 120:
        raise ValueError('关键词须为不超过 120 字的非空字符串')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码必须为正整数')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('每页结果数须为 1 至 10')
    doc = fitz.open(FILE)
    try:
        if doc.page_count != 57:
            raise RuntimeError('公开清单 PDF 页数异常')
        matches = []
        for index in range(doc.page_count):
            text = doc[index].get_text('text')
            if keyword.casefold() in text.casefold():
                matches.append({'pdf_page': index + 1, 'source_url': PDF + '#page=' + str(index + 1), 'page_text': text})
    finally:
        doc.close()
    start = (page - 1) * limit
    return {'source': '深圳职业技术大学图书馆公开的中国近现代本土文学作品清单', 'source_page': SOURCE, 'source_pdf': PDF, 'zju_related_collection': ZJU, 'source_pdf_sha256': SHA256, 'keyword': keyword, 'matching_pdf_pages': len(matches), 'page': page, 'limit': limit, 'items': matches[start:start + limit], 'scope': '按 PDF 提取文本匹配页码，命中数是页数而非图书数。来源 PDF 标示 2654 种、2783 册，与浙大介绍数量相同，但未核实逐项一致；不代表浙大完整馆藏或全文权限。PDF 文本提取可能跨行、错序或漏字，请对照原页，关键词按原字形匹配。'}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--limit', type=int, default=3)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.page, a.limit), ensure_ascii=False, indent=2))
