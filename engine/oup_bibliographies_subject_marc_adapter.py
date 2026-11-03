"""Official Oxford Bibliographies MARC subject collection snapshot (not article search)."""
import release_runtime
import requests
URL = 'https://fdslive.oup.com/www.oup.com/academic/marc/obo/OBO_MarcRecord_06252026.mrc'
INFO = 'https://academic.oup.com/pages/for-librarians/marc-records/oxford-bibliographies-marc-records'

def search(keyword, limit=10, timeout=25, *, offset=0):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must contain 1–100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('limit must be 1–20 and offset 0–100000')
    r = requests.get(URL, timeout=timeout)
    r.raise_for_status()
    data = r.content
    if len(data) > 2000000:
        raise ValueError('unexpected file size')
    i = 0
    count = 0
    skipped = 0
    rows = []
    while i < len(data):
        if not data[i:i + 5].isdigit():
            raise ValueError('unexpected MARC leader')
        size = int(data[i:i + 5])
        rec = data[i:i + size]
        if len(rec) != size or rec[-1:] != b'\x1d':
            raise ValueError('truncated MARC record')
        base = int(rec[12:17])
        directory = rec[24:base - 1]
        if len(directory) % 12 or rec[base - 1] != 30:
            raise ValueError('unexpected MARC directory')
        fields = {}
        try:
            for j in range(0, len(directory), 12):
                e = directory[j:j + 12]
                tag = e[:3].decode('ascii')
                if tag not in ('245', '856'):
                    continue
                length = int(e[3:7])
                field_offset = int(e[7:12])
                raw = rec[base + field_offset:base + field_offset + length - 1]
                sub = [(chr(v[0]), v[1:].decode('utf-8').strip()) for v in raw[2:].split(b'\x1f')[1:] if v]
                fields.setdefault(tag, []).append(sub)
        except UnicodeDecodeError:
            skipped += 1
            i += size
            count += 1
            continue
        values = lambda tag, code: [v for field in fields.get(tag, []) for c, v in field if c == code]
        subject = ' '.join(values('245', 'p'))
        title = ' '.join(values('245', 'a') + [subject]).strip()
        if keyword.strip().casefold() in title.casefold():
            rows.append({'title': title, 'subject': subject, 'editor': values('245', 'c'), 'urls': values('856', 'u')})
        i += size
        count += 1
    return {'source': 'Oxford Bibliographies official MARC subject records', 'source_url': URL, 'info_url': INFO, 'snapshot': '2026-06-25', 'record_count': count, 'excluded_non_utf8': skipped, 'keyword': keyword.strip(), 'matches': len(rows), 'limit': limit, 'offset': offset, 'next_offset': offset + limit if offset + limit < len(rows) else None, 'items': rows[offset:offset + limit], 'note': '每次重取来源文件并本地截取，文件更新可能改变顺序；本文件是各学科专题集合题录，不是专题内单篇文章或全文检索；不证明学校订购或访问权限。'}
