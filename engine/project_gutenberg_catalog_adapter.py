"""Local search over Project Gutenberg's official weekly catalog CSV."""
import release_runtime
import csv
import os
import subprocess
from pathlib import Path
URL = 'https://www.gutenberg.org/cache/epub/feeds/pg_catalog.csv'
DEFAULT = release_runtime.home() / 'Library/Application Support/ResearchDatabaseToolkit/gutenberg/pg_catalog.csv'
FIELDS = ('Text#', 'Type', 'Issued', 'Title', 'Language', 'Authors', 'Subjects', 'LoCC', 'Bookshelves')

def download(path=DEFAULT):
    """Explicitly download one catalog snapshot. Never overwrite an existing file."""
    p = release_runtime.expandpath(Path(path))
    p.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with p.open('xb') as out:
            created = True
            proc = release_runtime.run(['curl', '--compressed', '-fsSL', '--max-time', '60', '--max-filesize', '100000000', URL], stdout=out, stderr=subprocess.PIPE, timeout=65)
            if proc.returncode:
                raise RuntimeError('Catalog download failed: ' + proc.stderr.decode('utf-8', 'replace').strip())
            size = out.tell()
            if size > 100000000:
                raise ValueError('Catalog exceeds 100 MB')
    except Exception:
        if created:
            p.unlink(missing_ok=True)
        raise
    return {'path': str(p), 'bytes': size, 'source': URL, 'note': '一次性官方 CSV 快照，需自行更新；不代表全文权限。'}

def search(query, path=DEFAULT, field='all', offset=0, limit=20):
    if field not in ('all', 'title', 'author', 'subject', 'language'):
        raise ValueError('无效字段')
    if not isinstance(query, str) or not query.strip() or len(query) > 200:
        raise ValueError('请输入1至200字符')
    if not isinstance(offset, int) or offset < 0 or (not isinstance(limit, int)) or (not 1 <= limit <= 100):
        raise ValueError('分页范围无效')
    keys = {'title': ['Title'], 'author': ['Authors'], 'subject': ['Subjects'], 'language': ['Language'], 'all': ['Title', 'Authors', 'Subjects', 'Language', 'Bookshelves']}[field]
    q = query.casefold()
    total = 0
    items = []
    p = release_runtime.expandpath(Path(path))
    with p.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(FIELDS):
            raise ValueError('官方目录字段变更，请核验文件')
        for row in reader:
            if any((q in (row[k] or '').casefold() for k in keys)):
                if offset <= total < offset + limit:
                    row['catalog_url'] = 'https://www.gutenberg.org/ebooks/' + row['Text#'] if row['Text#'].isdigit() else None
                    items.append(row)
                total += 1
    return {'source': 'Project Gutenberg official CSV', 'catalog_url': URL, 'snapshot_file': str(p), 'snapshot_mtime': os.path.getmtime(p), 'query': query, 'field': field, 'offset': offset, 'limit': limit, 'matched': total, 'items': items, 'note': '本地快照中简单包含检索；Issued 为电子书发布日，不是印刷版出版日。美国公版状态不代表其他司法辖区可自由使用。'}
