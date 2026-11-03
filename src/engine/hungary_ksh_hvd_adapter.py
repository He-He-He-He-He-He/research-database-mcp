"""Hungarian Central Statistical Office HVD catalogue, RDF distributions and CSV rows."""
import release_runtime
import argparse, csv, io, json, re, subprocess, xml.etree.ElementTree as ET
from urllib.parse import urlparse
BASE = 'https://data.ksh.hu/'
UUID = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

def _uuid(s):
    if not isinstance(s, str) or not re.fullmatch(UUID, s):
        raise ValueError('无效 UUID')
    return s

def _get(url):
    u = urlparse(url)
    if u.scheme != 'https' or u.hostname != 'data.ksh.hu':
        raise ValueError('仅允许统计局 HTTPS 域名')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', '10000000', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('HVD 请求失败：' + p.stderr.decode('utf-8', 'replace')[:300])
    if len(p.stdout) > 10000000:
        raise ValueError('响应过大')
    return p.stdout

def catalogue(query=''):
    if not isinstance(query, str) or len(query) > 100:
        raise ValueError('关键词无效')
    rows = json.loads(_get(BASE + 'datasets.json'))
    if not isinstance(rows, list):
        raise ValueError('目录格式异常')
    found = [x for x in rows if query.casefold() in json.dumps(x, ensure_ascii=False).casefold()]
    return {'source': BASE + 'datasets.json', 'total': len(found), 'datasets': found, 'note': 'HVD 目录并非统计局全部统计数据。'}

def metadata(dataset):
    dataset = _uuid(dataset)
    url = BASE + 'datasets/' + dataset + '/metadata.rdf'
    root = ET.fromstring(_get(url))
    rdf = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
    lang = '{http://www.w3.org/XML/1998/namespace}lang'
    ds = []
    description = []
    for e in root.iter():
        if e.tag.endswith('description') and e.attrib.get(lang) == 'en':
            description.append(e.text or '')
        if e.tag.endswith('Distribution'):
            titles = {x.attrib.get(lang, ''): x.text for x in e if x.tag.endswith('title')}
            downloads = [x.text for x in e if x.tag.endswith('downloadURL') and x.text]
            ds.append({'titles': titles, 'download_urls': downloads, 'about': e.attrib.get(rdf + 'about')})
    return {'source': url, 'dataset': dataset, 'descriptions_en': description, 'distributions': ds, 'note': '必须核对资源内容和标题；官方 Fertility 数据集首个分发资源标题与内容存在疑点。'}

def rows(dataset, resource, filters=None, limit=20, encoding='utf-8-sig'):
    dataset = _uuid(dataset)
    resource = _uuid(resource)
    if not 1 <= limit <= 100:
        raise ValueError('limit 应为 1–100')
    filters = filters or {}
    if not isinstance(filters, dict) or len(filters) > 8 or any((not isinstance(k, str) or not isinstance(v, str) or len(k) > 100 or (len(v) > 100) for k, v in filters.items())):
        raise ValueError('筛选条件无效')
    meta = metadata(dataset)
    url = BASE + 'datasets/' + dataset + '/data/' + resource + '.csv'
    matched = [x for x in meta['distributions'] if url in x['download_urls']]
    if len(matched) != 1:
        raise ValueError('CSV 资源不在该数据集 RDF 目录中')
    if encoding not in ('utf-8-sig', 'cp1250'):
        raise ValueError('encoding 仅支持 utf-8-sig 或 cp1250')
    raw = _get(url)
    text = raw.decode(encoding)
    reader = csv.DictReader(io.StringIO(text), delimiter=';')
    if not reader.fieldnames or any((k not in reader.fieldnames for k in filters)):
        raise ValueError('筛选字段不在 CSV 表头')
    out = []
    count = 0
    for row in reader:
        if any((row.get(k) != v for k, v in filters.items())):
            continue
        count += 1
        if len(out) < limit:
            out.append(row)
    return {'source': url, 'dataset': dataset, 'distribution': matched[0], 'encoding': encoding, 'filters': filters, 'matching_rows': count, 'rows': out, 'note': '全量 CSV 下载后本地筛选，值与逗号小数原样保留；编码需核对源文件，资源标题、单位和指标口径需对照元数据和统计局原始资料。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('catalogue')
    q.add_argument('query', nargs='?', default='')
    q = s.add_parser('metadata')
    q.add_argument('dataset')
    q = s.add_parser('rows')
    q.add_argument('dataset')
    q.add_argument('resource')
    q.add_argument('--filters', default='{}')
    q.add_argument('--limit', type=int, default=20)
    q.add_argument('--encoding', choices=['utf-8-sig', 'cp1250'], default='utf-8-sig')
    a = p.parse_args()
    o = catalogue(a.query) if a.cmd == 'catalogue' else metadata(a.dataset) if a.cmd == 'metadata' else rows(a.dataset, a.resource, json.loads(a.filters), a.limit, a.encoding)
    print(json.dumps(o, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
