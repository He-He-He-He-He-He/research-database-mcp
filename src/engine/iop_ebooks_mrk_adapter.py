"""Search fixed publisher MARC text snapshots; not ZJU entitlement."""
import release_runtime
import re
from pathlib import Path
ROOT = release_runtime.home() / 'Library/Application Support/ResearchDatabaseToolkit/iop'
FILES = {'legacy': ROOT / 'legacy_all_collections.mrk', '2025': ROOT / '2025_collection_base.mrk'}
URL = 'https://iopscience.iop.org/bookListInfo/MARC-records'

def search(keyword, collection='2025', field='all', offset=0, limit=20):
    if collection not in FILES:
        raise ValueError('collection 只能是 legacy 或 2025')
    if field not in ('all', 'title', 'author'):
        raise ValueError('无效检索字段')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 200:
        raise ValueError('关键词为空或过长')
    if not isinstance(offset, int) or offset < 0 or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('分页无效')
    path = FILES[collection]
    raw = path.read_text(encoding='ascii')
    parts = re.split('(?m)(?=^=LDR  )', raw)
    items = []
    total = 0
    bad = 0
    for part in parts:
        if not part.startswith('=LDR  '):
            continue
        fields = {}
        for line in part.splitlines():
            m = re.match('^=([0-9A-Z]{3})  (.*)$', line)
            if m:
                fields.setdefault(m.group(1), []).append(m.group(2))
        titles = fields.get('245', [])
        authors = fields.get('100', []) + fields.get('700', [])
        if not titles:
            bad += 1
            continue
        target = {'title': titles, 'author': authors, 'all': titles + authors + fields.get('650', [])}[field]
        if any((keyword.casefold() in x.casefold() for x in target)):
            if offset <= total < offset + limit:
                items.append({'title_raw': titles, 'author_raw': authors, 'identifier_raw': fields.get('020', []), 'publication_raw': fields.get('264', []) + fields.get('260', []), 'links_raw': fields.get('856', []), 'control_number': fields.get('001', []), 'source_marc_text': part})
            total += 1
    return {'source': 'IOP official MRK snapshot', 'source_info': URL, 'collection': collection, 'file': str(path), 'total_records': len(parts) - 1, 'malformed_or_missing_title': bad, 'matched': total, 'offset': offset, 'limit': limit, 'items': items, 'note': '固定出版社公开书目快照，本地包含检索；原始 MARC 子字段和转义保留，非学校订购或全文权限证明。2025全量文件包含本次核对14份增量全部85个001标识，但部分字段不同；legacy 不含 Physics World Discovery。'}
