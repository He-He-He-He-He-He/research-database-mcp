"""Oxford Scholarship Online annual book MARC release, not entire collection."""
import release_runtime
import requests
import oup_scholarship_archive_subjects_adapter as marc_codec
URLS = {2023: 'https://fdslive.oup.com/www.oup.com/academic/marc/upso/oso_2023.mrc', 2024: 'https://fdslive.oup.com/www.oup.com/academic/marc/upso/oso_2024.mrc'}
INFO = 'https://academic.oup.com/pages/institutional-account-management/marc-records/oxford-scholarship-online-archive'

def search(keyword, year=2024, limit=10, timeout=25, *, offset=0):
    if year not in URLS:
        raise ValueError('year must be 2023 or 2024')
    url = URLS[year]
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must contain 1–100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('limit must be 1–20 and offset 0–100000')
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.content
    if len(data) > 5000000:
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
                if tag not in ('245', '100', '700', '020', '024', '856'):
                    continue
                length = int(e[3:7])
                field_offset = int(e[7:12])
                raw = rec[base + field_offset:base + field_offset + length - 1]
                sub = [(chr(v[0]), marc_codec._decode(v[1:], rec[:24]).strip()) for v in raw[2:].split(b'\x1f')[1:] if v]
                fields.setdefault(tag, []).append(sub)
        except UnicodeDecodeError:
            skipped += 1
            i += size
            count += 1
            continue
        values = lambda tag, code: [v for field in fields.get(tag, []) for c, v in field if c == code]
        title = ' '.join(values('245', 'a') + values('245', 'b') + values('245', 'p')).strip()
        if keyword.strip().casefold() in title.casefold():
            rows.append({'title': title, 'responsibility': values('245', 'c'), 'isbn': values('020', 'a'), 'urls': values('856', 'u')})
        i += size
        count += 1
    return {'source': 'Oxford Scholarship Online official annual MARC book records', 'source_url': url, 'info_url': INFO, 'release_year': year, 'record_count': count, 'excluded_undecodable': skipped, 'marc8_decoder_available': marc_codec.marc8_to_unicode is not None, 'keyword': keyword.strip(), 'matches': len(rows), 'limit': limit, 'offset': offset, 'next_offset': offset + limit if offset + limit < len(rows) else None, 'items': rows[offset:offset + limit], 'note': '每次重新下载该年度文件并本地截取，来源文件更新可能改变顺序；仅该年度出版社 MARC 更新包中的图书题录，不是全部图书或学校订购清单；不证明全文权限；含无法按 MARC leader 所示编码解码的相关字段的记录已排除，检索可能不完整。'}
