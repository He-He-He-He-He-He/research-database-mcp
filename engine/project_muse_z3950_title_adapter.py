"""Project MUSE official Z39.50 title search (bounded)."""
import release_runtime
import base64
import io
import html
import re
import subprocess
import tempfile
from pathlib import Path
from oup_scholarship_archive_subjects_adapter import _LOCAL_DEPS
from pymarc import MARCReader
CLIENT = Path(__file__).resolve().parent / '.local_yaz/bin/yaz-client'
HOST = 'z3950.muse.jhu.edu:210/MUSE'
INFO = 'https://about.muse.jhu.edu/resources/faq/'

def search(keyword, limit=2, timeout=30, field='title', page=1):
    fields = {'title': 4, 'author': 1003, 'subject': 21, 'year': 31, 'any': 1016}
    if field not in fields:
        raise ValueError('field must be title, author, subject, year, or any')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 100):
        raise ValueError('page must be 1–100')
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100 or re.search('["\\\\\\r\\n\\x00-\\x1f]', keyword):
        raise ValueError('keyword must be 1–100 chars, without quotes, backslash or control characters')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 5):
        raise ValueError('limit must be 1–5')
    if not CLIENT.is_file():
        raise RuntimeError('local YAZ client is unavailable')
    commands = f'open {HOST}\nfind @attr 1={fields[field]} "{keyword.strip()}"\nshow {(page - 1) * limit + 1}+{limit}\nquit\n'
    with tempfile.TemporaryDirectory(prefix='muse-z3950-') as tmp:
        rawfile = Path(tmp) / 'records.mrc'
        proc = release_runtime.run([str(CLIENT), '-m', str(rawfile)], input=commands.encode('utf-8'), capture_output=True, timeout=timeout)
        text = proc.stdout.decode('utf-8', 'replace')
        if proc.returncode or 'Connection accepted' not in text or 'Search was a success.' not in text:
            raise RuntimeError('Z39.50 connection or search failed')
        match = re.search('Number of hits:\\s*(\\d+)', text)
        if not match:
            raise RuntimeError('Z39.50 result count unavailable')
        reported = int(match.group(1))
        data = rawfile.read_bytes() if rawfile.exists() else b''
        if reported and (page - 1) * limit < reported and (not data):
            raise RuntimeError('server did not deliver requested records')
        rows = []
        i = 0
        while i < len(data):
            if not data[i:i + 5].isdigit():
                raise ValueError('invalid MARC record leader')
            n = int(data[i:i + 5])
            raw = data[i:i + n]
            if len(raw) != n or raw[-1:] != b'\x1d':
                raise ValueError('truncated MARC record')
            record = next(MARCReader(io.BytesIO(raw), to_unicode=True))
            if record is None:
                raise ValueError('MARC decoding failed')

            def val(tag, code):
                return [v for f in record.get_fields(tag) for v in f.get_subfields(code)]
            title_raw = ' '.join(val('245', 'a') + val('245', 'b'))
            title = html.unescape(re.sub('</?(?:i|b|em|strong|sub|sup)>', '', title_raw, flags=re.IGNORECASE))
            rows.append({'title': title, 'title_raw': title_raw, 'authors': val('100', 'a') + val('700', 'a'), 'issn': val('022', 'a'), 'issue_statement': val('362', 'a'), 'publication': val('440', 'a'), 'publication_note': 'MARC 440$a 来源或丛刊标题，不是出版社。', 'publisher': val('260', 'b') + val('264', 'b'), 'date': val('260', 'c') + val('264', 'c'), 'urls': val('856', 'u'), 'marc_base64': base64.b64encode(raw).decode('ascii')})
            i += n
        if len(rows) > limit:
            raise ValueError('server returned more records than requested')
    return {'source': 'Project MUSE official Z39.50', 'source_info': INFO, 'query': keyword.strip(), 'search_field': field, 'page': page, 'page_size': limit, 'server_reported_hits': reported, 'items': rows, 'note': '服务器报告的命中数可能受上限或索引设置影响；原始 MARC 以 base64 保留，编码按 leader 解析。部分服务端原始 MARC 标题本身含乱码，保留原始内容、不自动纠正；不代表学校订购范围或全文权限。Z39.50 连接未加密，避免输入敏感查询；year 为服务端年份索引，可能不等于 MARC 出版日期。'}
