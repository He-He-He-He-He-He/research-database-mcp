"""OFAC SDN primary names, aliases and remarks; not a screening decision."""
import release_runtime
import csv
import hashlib
import io
import requests
from concurrent.futures import ThreadPoolExecutor
BASE = 'https://www.treasury.gov/ofac/downloads/'

def _file(name):
    try:
        with requests.get(BASE + name, timeout=45, stream=True, allow_redirects=True) as r:
            if not r.ok:
                raise RuntimeError('OFAC source returned HTTP ' + str(r.status_code))
            content = bytearray()
            for part in r.iter_content(65536):
                content.extend(part)
                if len(content) > 12000000:
                    raise RuntimeError('OFAC file exceeds 12 MB')
        return bytes(content)
    except requests.RequestException as e:
        raise RuntimeError('OFAC network error: ' + type(e).__name__) from None

def search(keyword, offset=0, limit=20):
    if not isinstance(keyword, str) or not 2 <= len(keyword.strip()) <= 100:
        raise ValueError('Keyword must contain 2–100 characters')
    if any((isinstance(v, bool) or not isinstance(v, int) for v in (offset, limit))) or offset < 0 or (not 1 <= limit <= 100):
        raise ValueError('Invalid pagination')
    with ThreadPoolExecutor(max_workers=2) as p:
        primary, alt = list(p.map(_file, ('sdn.csv', 'alt.csv')))

    def rows(data):
        return csv.reader(io.StringIO(data.rstrip(b'\x1a\r\n').decode('utf-8-sig')))
    target = keyword.casefold().strip()
    matches = {}
    for row in rows(primary):
        if len(row) < 12 or not row[0].strip().isdigit():
            raise RuntimeError('Unexpected OFAC primary CSV format')
        why = []
        if target in row[1].casefold():
            why.append('primary_name')
        if target in row[11].casefold():
            why.append('remarks')
        if why:
            matches[row[0].strip()] = {'uid': row[0].strip(), 'primary_row_original': row, 'matched_in': why, 'matched_alias_rows': []}
    matched_alias = {}
    for row in rows(alt):
        if len(row) < 5 or not row[0].strip().isdigit():
            raise RuntimeError('Unexpected OFAC alias CSV format')
        if target in row[3].casefold():
            matched_alias.setdefault(row[0].strip(), []).append(row)
    if matched_alias:
        for row in rows(primary):
            uid = row[0].strip()
            if uid in matched_alias:
                item = matches.setdefault(uid, {'uid': uid, 'primary_row_original': row, 'matched_in': [], 'matched_alias_rows': []})
                item['matched_in'].append('alias')
                item['matched_alias_rows'] = matched_alias[uid]
    values = sorted(matches.values(), key=lambda x: int(x['uid']))
    return {'source': 'U.S. Treasury OFAC Specially Designated Nationals (SDN) CSV', 'source_info': 'https://ofac.treasury.gov/sanctions-list-service', 'source_files': [BASE + 'sdn.csv', BASE + 'alt.csv'], 'sha256': {'sdn': hashlib.sha256(primary).hexdigest(), 'alt': hashlib.sha256(alt).hexdigest()}, 'bytes': len(primary) + len(alt), 'keyword': keyword, 'matched_total': len(values), 'offset': offset, 'items': values[offset:offset + limit], 'note': '仅搜索 SDN 主名称、备注和单列别名的子串，不含所有非 SDN 清单、地址、证件或未匹配别名；存在不同文件更新时间不一致的可能。名称匹配不代表身份一致，未匹配不代表安全或不受制裁；核对 OFAC 原始记录、别名和身份信息及现行规则，不能据此单独作合规判断。-0- 是上游空值标记，不是零。'}
