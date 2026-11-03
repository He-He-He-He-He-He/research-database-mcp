"""Local academic-use lookup in the official Davies/Gardner COCA Academic core list."""
import release_runtime
from pathlib import Path
import openpyxl
FILE = Path(__file__).resolve().parent / 'COCA官方学术核心词表_acadCore.xlsx'
SOURCE = 'https://www.academicwords.info/download.asp'
DOWNLOAD = 'https://www.academicwords.info/download/acadCore.xlsx'
DOMAINS = ('HIS', 'EDU', 'SOC', 'LAW', 'HUM', 'PHIL', 'SCI', 'MED', 'BUS')
FIELDS = ('ID', 'word', 'PoS', 'COCA-All', 'COCA-Acad', 'ratio', 'disp', 'range')
SCOPE = 'Davies 与 Gardner 的历史 COCA 学术核心词表，基于 1.2 亿词学术子语料；原表 COCA-All 对应旧版 4.25 亿词整体语料，并非现今 COCA 的全库或当前词频。本地原表有 3015 条；仅供学术用途，不应将完整词表发布在其他网站。'

def search(word, contains=False, limit=10):
    if not isinstance(word, str) or not word.strip() or len(word) > 100:
        raise ValueError('请提供不超过 100 字的英文词')
    if not isinstance(contains, bool):
        raise ValueError('contains 必须为布尔值')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 10):
        raise ValueError('limit 须为 1 至 10')
    query = word.strip().casefold()
    book = openpyxl.load_workbook(FILE, read_only=True, data_only=True)
    try:
        sheet = book['list']
        rows = sheet.iter_rows(values_only=True)
        header = next(rows)
        if tuple(header[:8]) != FIELDS or tuple(header[8:17]) != DOMAINS or tuple(header[17:26]) != DOMAINS:
            raise RuntimeError('官方学术词表列结构变化')
        found = []
        total = 0
        for row in rows:
            if not isinstance(row[0], int):
                continue
            total += 1
            if not isinstance(row[1], str):
                raise RuntimeError('词表词条格式异常')
            lemma = row[1].casefold()
            if query in lemma if contains else query == lemma:
                found.append({'rank': row[0], 'lemma': row[1], 'part_of_speech': row[2], 'coca_all_count_425m': row[3], 'academic_count_120m': row[4], 'academic_to_expected_ratio': row[5], 'dispersion': row[6], 'domain_range': row[7], 'domain_counts': dict(zip(DOMAINS, row[8:17])), 'domain_relative_to_expected': dict(zip(DOMAINS, row[17:26]))})
        if total != 3015:
            raise RuntimeError('官方学术词表词条数异常')
    finally:
        book.close()
    return {'source': 'Davies & Gardner COCA Academic Vocabulary List', 'source_page': SOURCE, 'source_xlsx': DOWNLOAD, 'source_sha256': 'b67e1c7263177d71a576419192e12429e5809a843661d5178623d3b7f62017f3', 'query': word, 'contains': contains, 'matching_lemmas': len(found), 'items': found[:limit], 'domain_codes': list(DOMAINS), 'scope': SCOPE}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('word')
    p.add_argument('--contains', action='store_true')
    p.add_argument('--limit', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(search(a.word, a.contains, a.limit), ensure_ascii=False, indent=2))
