"""Lookup a bounded result from publisher's free COCA frequency sample."""
import release_runtime
from pathlib import Path
import openpyxl
FILE = Path(__file__).resolve().parent / 'COCA官方词频免费样表_wordFrequency.xlsx'
SOURCE = 'https://www.wordfrequency.info/samples.asp'
DOWNLOAD = 'https://www.wordfrequency.info/samples/wordFrequency.xlsx'
HEADERS = ('rank', 'lemma', 'PoS', 'freq', 'perMil', '%caps', '%allC', 'range', 'disp', 'blog', 'web', 'TVM', 'spok', 'fic', 'mag', 'news', 'acad', 'blogPM', 'webPM', 'TVMPM', 'spokPM', 'ficPM', 'magPM', 'newsPM', 'acadPM')
SCOPE = 'COCA 发布者免费词频样表中词元表的历史快照，源站标称约 5000 条，文件实有 5050 条；基于 10 亿词版本，非完整或实时 COCA，也非语料原文。原表频次及每百万词频字段原样返回；词元列的 Excel 布尔值保留原值，并提供归一化检索文字。'

def search(word, contains=False, limit=10):
    if not isinstance(word, str) or not word.strip() or len(word) > 100:
        raise ValueError('请输入不超过 100 字的词')
    if not isinstance(contains, bool):
        raise ValueError('contains 必须为布尔值')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('limit 须为 1 至 10')
    query = word.strip().casefold()
    book = openpyxl.load_workbook(FILE, read_only=True, data_only=True)
    try:
        sheet = book['1 lemmas']
        rows = sheet.iter_rows(values_only=True)
        if tuple(next(rows)[:25]) != HEADERS:
            raise RuntimeError('COCA 样表表头异常')
        found = []
        count = 0
        for row in rows:
            if not isinstance(row[0], int):
                continue
            count += 1
            if not isinstance(row[1], (str, bool)):
                raise RuntimeError('COCA 样表词元异常')
            w = str(row[1]).casefold()
            if query in w if contains else query == w:
                item = dict(zip(HEADERS, row[:25]))
                item['lemma_search_text'] = w
                found.append(item)
        if count != 5050:
            raise RuntimeError('COCA 样表词元数异常')
    finally:
        book.close()
    return {'source': 'COCA 发布者公开免费词频样表', 'source_page': SOURCE, 'source_xlsx': DOWNLOAD, 'source_sha256': 'a7420c6c2739e94eee1ed1867d611978631d7cd18acbe412d86e1adc277b17df', 'word': word, 'contains': contains, 'matching_lemmas': len(found), 'items': found[:limit], 'scope': SCOPE, 'field_documentation': 'https://www.wordfrequency.info/files.asp'}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('word')
    p.add_argument('--contains', action='store_true')
    p.add_argument('--limit', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(search(a.word, a.contains, a.limit), ensure_ascii=False, indent=2))
