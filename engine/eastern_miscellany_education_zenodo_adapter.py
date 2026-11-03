"""Search a 108-article researcher-curated Eastern Miscellany subset."""
import release_runtime
import csv
from pathlib import Path
FILE = Path(__file__).resolve().parent / '东方杂志_教育文化基金会主题_108篇.csv'
SOURCE = 'https://zenodo.org/records/17952862'
DOI = 'https://doi.org/10.5281/zenodo.17952862'
SCOPE = '研究者整理的《东方杂志》1924—1947 年中华教育文化基金会专题资料，共 108 条；不是全刊总目、浙大馆藏服务或完整全文。按原文件字形匹配，原文可能存在识读或切分误差，元数据中的 NA 等占位值按原样保留；引用与使用须遵循该资料集 CC BY 4.0。'

def search(keyword, limit=10, page=1, include_text=False):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词须为不超过 200 字的非空字符串')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 30):
        raise ValueError('limit 须为 1 至 30')
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise ValueError('页码须为正整数')
    if not isinstance(include_text, bool):
        raise ValueError('include_text 必须是布尔值')
    with FILE.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = {'DocId', 'Title', 'authors', 'category', 'volume', 'issue', 'Year', 'text_seg'}
        if not fields.issubset(reader.fieldnames or []):
            raise RuntimeError('东方杂志专题文件字段异常')
        rows = list(reader)
    if len(rows) != 108:
        raise RuntimeError('东方杂志专题文件条数异常')
    keyword = keyword.strip()
    found = []
    for row in rows:
        if any((keyword.casefold() in (row.get(k) or '').casefold() for k in ('Title', 'authors', 'text_seg'))):
            item = {k: row[k] for k in ('DocId', 'Title', 'authors', 'category', 'volume', 'issue', 'Year')}
            if include_text:
                item['text_seg'] = row['text_seg']
            found.append(item)
    start = (page - 1) * limit
    return {'source': 'Cécile Armand 研究资料集，Zenodo 17952862', 'source_url': SOURCE, 'doi': DOI, 'license': 'CC BY 4.0', 'source_md5': '2ec9b539e811d2f7caf147805100628a', 'keyword': keyword, 'matching_records': len(found), 'page': page, 'limit': limit, 'items': found[start:start + limit], 'scope': SCOPE}
if __name__ == '__main__':
    import argparse, json
    p = argparse.ArgumentParser()
    p.add_argument('keyword')
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--include-text', action='store_true')
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.limit, a.page, a.include_text), ensure_ascii=False, indent=2))
