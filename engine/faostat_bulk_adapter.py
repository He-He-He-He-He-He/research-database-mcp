"""FAOSTAT 官方批量下载目录与 ZIP 数据表筛选，公开只读。"""
import release_runtime
import argparse
import csv
import io
import json
import re
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit
BASE = 'https://bulks-faostat.fao.org/production/'
MANIFEST = BASE + 'datasets_E.xml'
MAX_ZIP = 65000000
MAX_CSV = 750000000

def _fetch(url, limit, timeout=120):
    p = urlsplit(url)
    if p.scheme != 'https' or p.netloc != 'bulks-faostat.fao.org' or (not p.path.startswith('/production/')) or p.query or p.fragment:
        raise ValueError('只接受 FAOSTAT 官方批量数据地址')
    r = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', str(timeout), '--max-filesize', str(limit), url], capture_output=True, timeout=timeout + 5)
    if r.returncode:
        raise RuntimeError('FAOSTAT 上游请求失败：' + r.stderr.decode('utf-8', 'replace')[:400])
    if len(r.stdout) > limit:
        raise ValueError('文件超过大小限制')
    return r.stdout

def catalog(keyword=''):
    if not isinstance(keyword, str) or len(keyword) > 150:
        raise ValueError('关键词长度错误')
    root = ET.fromstring(_fetch(MANIFEST, 5000000, 30))
    items = []
    for el in root.findall('Dataset'):
        x = {c.tag: c.text or '' for c in el}
        if keyword.casefold() in (x.get('DatasetCode', '') + ' ' + x.get('DatasetName', '') + ' ' + x.get('Topic', '')).casefold():
            items.append(x)
    if len(root) < 1:
        raise ValueError('目录为空或格式变化')
    return {'source': MANIFEST, 'total_catalog': len(root), 'matched': len(items), 'datasets': items, 'note': 'FAOSTAT 官方批量目录；名称、更新日期、文件大小和说明由上游提供。'}

def data(dataset, filters, limit=30, offset=0):
    if not isinstance(dataset, str) or not re.fullmatch('[A-Za-z0-9_]{1,30}', dataset):
        raise ValueError('无效数据集代码')
    if not isinstance(filters, dict) or not filters or len(filters) > 8 or any((not isinstance(k, str) or not isinstance(v, str) or (not k) or (not v) or (len(k) > 100) or (len(v) > 200) for k, v in filters.items())):
        raise ValueError('至少指定一个非空列名和完整匹配值')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('结果数须为 1–100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 10000000):
        raise ValueError('offset 须为 0–10000000 的整数')
    cat = catalog(dataset)
    selected = [x for x in cat['datasets'] if x.get('DatasetCode', '').casefold() == dataset.casefold()]
    if len(selected) != 1:
        raise ValueError('目录中找不到唯一数据集')
    meta = selected[0]
    url = meta.get('FileLocation', '')
    if not url.endswith('(Normalized).zip'):
        raise ValueError('暂仅支持目录中的 Normalized ZIP')
    with zipfile.ZipFile(io.BytesIO(_fetch(url, MAX_ZIP))) as archive:
        files = [i for i in archive.infolist() if i.filename.endswith('(Normalized).csv') and '/' not in i.filename]
        if len(files) != 1:
            raise ValueError('压缩包中未识别唯一主表')
        info = files[0]
        if info.file_size > MAX_CSV:
            raise ValueError('主表超过解压大小限制')
        with archive.open(info) as stream:
            reader = csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig', newline=''))
            columns = reader.fieldnames or []
            if any((k not in columns for k in filters)):
                raise ValueError('筛选列不存在；可用列：' + ', '.join(columns))
            rows = []
            matched = 0
            for row in reader:
                if all((row.get(k, '').casefold() == v.casefold() for k, v in filters.items())):
                    matched += 1
                    if offset < matched <= offset + limit:
                        rows.append(row)
    return {'source': url, 'dataset': meta, 'columns': columns, 'filters': filters, 'matched': matched, 'returned': len(rows), 'offset': offset, 'next_offset': offset + len(rows) if offset + len(rows) < matched else None, 'rows': rows, 'note': '原值均为字符串，保留单位、年份、标记和说明；匹配是列值不区分大小写的完整匹配。偏移为本地结果位置，每次重新下载完整源表，来源更新或排序变化时跨次拼页可能不一致；大表按大小上限可能被拒绝。须核对指标定义与单位。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('catalog')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('data')
    q.add_argument('dataset')
    q.add_argument('--filters', required=True, help='JSON 对象，列名与值精确匹配')
    q.add_argument('--limit', type=int, default=30)
    q.add_argument('--offset', type=int, default=0)
    a = p.parse_args()
    print(json.dumps(catalog(a.keyword) if a.cmd == 'catalog' else data(a.dataset, json.loads(a.filters), a.limit, a.offset), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
