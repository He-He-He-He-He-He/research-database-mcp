"""NARA public S3 snapshot: bounded listing and per-object title search."""
import release_runtime
import json, re, subprocess, xml.etree.ElementTree as ET
from urllib.parse import urlencode, quote
BUCKET = 'https://nara-national-archives-catalog.s3.amazonaws.com/'
INFO = 'https://www.archives.gov/developer/national-archives-catalog-dataset'
NS = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}

def _group(g):
    if not isinstance(g, str) or not re.fullmatch('[1-9][0-9]{0,3}', g):
        raise ValueError('馆藏组编号须为1—4位正整数')
    return 'descriptions/record-groups/rg_' + g + '/'

def _fetch(url, maxbytes=6000000):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '40', '--max-filesize', str(maxbytes), url], capture_output=True, timeout=45)
    if p.returncode:
        raise RuntimeError('NARA 数据请求失败: ' + p.stderr.decode('utf8', 'replace').strip())
    if len(p.stdout) > maxbytes:
        raise RuntimeError('NARA 文件大于上限')
    return p.stdout

def objects(group, limit=10, start_after=''):
    prefix = _group(group)
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 50):
        raise ValueError('limit须为1—50')
    if start_after and (not isinstance(start_after, str) or not re.fullmatch(re.escape(prefix) + '[A-Za-z0-9_.-]*', start_after)):
        raise ValueError('start_after必须为本组已返回的文件名')
    p = {'list-type': '2', 'prefix': prefix, 'max-keys': limit}
    if start_after:
        p['start-after'] = start_after
    url = BUCKET + '?' + urlencode(p)
    root = ET.fromstring(_fetch(url, 2000000))
    out = []
    last_key = None
    if root.findtext('s:Prefix', namespaces=NS) != prefix:
        raise RuntimeError('NARA 返回的目录前缀不符')
    for x in root.findall('s:Contents', NS):
        key = x.findtext('s:Key', namespaces=NS)
        if key and key.startswith(prefix):
            last_key = key
        if not key or not re.fullmatch(re.escape(prefix) + 'rg_' + re.escape(group) + '-[0-9]+\\.jsonl', key):
            continue
        out.append({'key': key, 'bytes': int(x.findtext('s:Size', default='0', namespaces=NS)), 'last_modified': x.findtext('s:LastModified', namespaces=NS)})
    return {'source': 'NARA public S3 dataset', 'source_page': INFO, 'record_group': group, 'source_url': url, 'objects': out, 'truncated': root.findtext('s:IsTruncated', namespaces=NS) == 'true', 'next_start_after': last_key, 'note': '按 S3 对象名的字典序列出文件，不是档案记录列表；接续使用 next_start_after。对象可能超单次读取上限。'}

def file_search(group, file_number, keyword='', offset=0, limit=10):
    prefix = _group(group)
    if isinstance(file_number, bool) or not isinstance(file_number, int) or (not 0 <= file_number <= 999999):
        raise ValueError('文件编号无效')
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('关键词超限')
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0 or isinstance(limit, bool) or (not isinstance(limit, int)) or (not 1 <= limit <= 30):
        raise ValueError('分页无效')
    key = prefix + 'rg_' + group + '-' + str(file_number) + '.jsonl'
    url = BUCKET + quote(key, safe='/')
    raw = _fetch(url)
    matches = []
    n = 0
    total = 0
    for line in raw.splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        r = d.get('record')
        if not isinstance(r, dict):
            raise RuntimeError('NARA 记录格式异常')
        total += 1
        title = r.get('title') or ''
        if not isinstance(title, str):
            raise RuntimeError('NARA 标题格式异常')
        if keyword.casefold() not in title.casefold():
            continue
        if offset <= n < offset + limit:
            ident = r.get('naId')
            matches.append({'naId': ident, 'title': title, 'description_level': r.get('levelOfDescription'), 'start': r.get('inclusiveStartDate'), 'end': r.get('inclusiveEndDate'), 'access_restriction': r.get('accessRestriction'), 'record_types': r.get('generalRecordsTypes'), 'catalog_url': 'https://catalog.archives.gov/id/' + str(ident) if isinstance(ident, int) else None})
        n += 1
    return {'source': 'NARA public S3 dataset', 'source_page': INFO, 'record_group': group, 'object_key': key, 'source_url': url, 'query': keyword, 'file_records': total, 'file_matches': n, 'offset': offset, 'items': matches, 'note': '仅对单个文件标题做不区分大小写的子串筛选；不是完整馆藏检索或原文，允许词中匹配。快照可能修订；未扫描其他对象。各记录开放及版权状态以档案原页为准。'}
