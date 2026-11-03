"""Cambridge Core public journal MARC title list, not institution holdings."""
import release_runtime
import re
import requests
URL = 'https://www.cambridge.org/core/services/aop-file-manager/file/5e4401f6a9b1d7bb0a3fcb4d/Journals-records.txt'

def search(keyword, limit=10, timeout=25, *, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must contain 1–100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('limit must be 1–20 and offset 0–100000')
    response = requests.get(URL, timeout=timeout)
    response.raise_for_status()
    if len(response.content) > 5000000:
        raise ValueError('unexpectedly large MARC file')
    records = re.split(b'(?m)(?=^=LDR  )', response.content)
    if len(records) < 2:
        raise ValueError('unexpected MARC file format')
    rows = []
    skipped_unreadable = 0
    for record in records:
        if not record:
            continue
        try:
            selected = b'\n'.join((line for line in record.splitlines() if line.startswith((b'=245  ', b'=022  ', b'=856  ')))).decode('utf-8')
        except UnicodeDecodeError:
            skipped_unreadable += 1
            continue

        def values(tag, code):
            out = []
            for line in selected.splitlines():
                if line.startswith('=' + tag + '  '):
                    out += [m.group(1).strip() for m in re.finditer('\\$' + re.escape(code) + '([^$]*)', line)]
            return out
        parts = values('245', 'a') + values('245', 'b')
        title = ' '.join(parts).strip()
        if not title or keyword.strip().casefold() not in title.casefold():
            continue
        rows.append({'title': title, 'issn': values('022', 'a'), 'url': next((x for x in values('856', 'u') if x.startswith('https://www.cambridge.org/')), None)})
    return {'source': 'Cambridge Core official public journals MARC', 'source_url': URL, 'keyword': keyword.strip(), 'records_in_file': len(records) - 1, 'matches': len(rows), 'excluded_records_with_unreadable_fields': skipped_unreadable, 'limit': limit, 'offset': offset, 'next_offset': offset + limit if offset + limit < len(rows) else None, 'items': rows[offset:offset + limit], 'note': '每次重新下载来源文件并本地截取，文件更新可能改变顺序。出版社期刊目录，不代表学校订购、文章检索或全文授权；标题保留 MARC 标点；题名、ISSN 或链接含非 UTF-8 字节的记录已排除，匹配数不完整；须核对原站。'}
