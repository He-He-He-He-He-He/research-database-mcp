"""Oxford Scholarship Online historical subject MARC sets; not current institutional holdings."""
import release_runtime
import requests
import sys
from pathlib import Path
_LOCAL_DEPS = Path(__file__).resolve().parent / '.local_dependencies'
if (_LOCAL_DEPS / 'pymarc').is_dir():
    sys.path.insert(0, str(_LOCAL_DEPS))
try:
    from pymarc.marc8 import marc8_to_unicode
except ImportError:
    marc8_to_unicode = None

def _decode(raw, leader):
    if leader[9:10] == b'a':
        return raw.decode('utf-8')
    if leader[9:10] != b' ':
        raise UnicodeDecodeError('marc', raw, 0, len(raw), 'unknown MARC character coding')
    if raw.isascii():
        return raw.decode('ascii')
    if marc8_to_unicode is None:
        raise UnicodeDecodeError('marc8', raw, 0, len(raw), 'pymarc required')
    text = marc8_to_unicode(raw)
    if '�' in text:
        raise UnicodeDecodeError('marc8', raw, 0, len(raw), 'replacement character')
    return text
URLS = {'law': 'https://fdslive.oup.com/www.oup.com/academic/marc/oso-archive/oso_law_all_052022.mrc', 'history': 'https://fdslive.oup.com/www.oup.com/academic/marc/upso-archive/oso_history_all.mrc', 'politics': 'https://fdslive.oup.com/www.oup.com/academic/marc/upso-archive/oso_politics_all.mrc', 'economics': 'https://fdslive.oup.com/www.oup.com/academic/marc/upso-archive/oso_economicsfinance_all.mrc'}
INFO = 'https://academic.oup.com/pages/institutional-account-management/marc-records/oxford-scholarship-online-archive'

def search(keyword, subject='law', limit=10, timeout=25, *, offset=0):
    if subject not in URLS:
        raise ValueError('subject must be law, history, politics or economics')
    url = URLS[subject]
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword must contain 1–100 characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 20) or (type(offset) is not int) or (not 0 <= offset <= 100000):
        raise ValueError('limit must be 1–20 and offset 0–100000')
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.content
    if len(data) > 10000000:
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
                sub = [(chr(v[0]), _decode(v[1:], rec[:24]).strip()) for v in raw[2:].split(b'\x1f')[1:] if v]
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
    return {'source': 'Oxford Scholarship Online official historical subject MARC records', 'source_url': url, 'info_url': INFO, 'subject': subject, 'record_count': count, 'excluded_undecodable': skipped, 'marc8_decoder_available': marc8_to_unicode is not None, 'keyword': keyword.strip(), 'matches': len(rows), 'limit': limit, 'offset': offset, 'next_offset': offset + limit if offset + limit < len(rows) else None, 'items': rows[offset:offset + limit], 'note': '每次重取来源文件并本地截取，文件更新可能改变顺序；仅出版社历史专题存档文件中的图书题录，不代表当下全部书籍、学校订购或全文权限；按 leader 标记使用 UTF-8 或 pymarc 的 MARC-8 转换；无法解码的记录排除，检索可能不完整。'}
