"""乌兹别克斯坦国家统计委员会 SIAT 公开指标目录、元数据及表格。"""
import release_runtime
import argparse
import json
import re
import subprocess
from urllib.parse import urlencode
BASE = 'https://api.siat.stat.uz/sdmx/'
MAX_BYTES = 10000000

def _get(path, params=None):
    url = BASE + path + ('?' + urlencode(params) if params else '')
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), '-H', 'Accept-Language: en', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('SIAT 请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应过大')
    return (url, json.loads(p.stdout))

def _id(value):
    text = str(value)
    if isinstance(value, bool) or not re.fullmatch('[0-9]{1,10}', text):
        raise ValueError('指标或分类编号须为数字')
    return text

def browse(parent=None):
    path = '' if parent is None else _id(parent) + '/children/'
    url, v = _get(path)
    if not isinstance(v, dict) or not isinstance(v.get('results'), list):
        raise ValueError('目录响应异常')
    return {'source': url, 'data': v, 'note': '只读当前返回页，分类可继续向下浏览；不是全站指标全集。'}

def search(keyword, page=1, size=20):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('关键词无效')
    if isinstance(page, bool) or not isinstance(page, int) or (not 1 <= page <= 1000) or isinstance(size, bool) or (not isinstance(size, int)) or (not 1 <= size <= 100):
        raise ValueError('分页无效')
    url, v = _get('search/', {'search': keyword, 'page': page, 'size': size})
    if not isinstance(v, dict) or not isinstance(v.get('results'), list):
        raise ValueError('搜索响应异常')
    return {'source': url, 'data': v, 'note': '官方搜索结果及分页；须核对具体指标和可用权限。'}

def metadata(indicator):
    ident = _id(indicator)
    url, info = _get(ident + '/')
    meta_url, meta = _get(ident + '/metadata/')
    if not isinstance(info, dict) or str(info.get('id')) != ident or (not isinstance(meta, dict)) or (not isinstance(meta.get('meta_data'), list)):
        raise ValueError('指标元数据响应异常')
    return {'source': url, 'metadata_source': meta_url, 'indicator': info, 'metadata': meta, 'note': '保留单位、更新、统计方法与初步标记；不同数据集覆盖与定义不同。'}

def data(indicator, region=None, start=None, end=None):
    ident = _id(indicator)
    if region is not None:
        region = _id(region)
    for x in (start, end):
        if x is not None and (isinstance(x, bool) or not isinstance(x, int) or (not 1900 <= x <= 2100)):
            raise ValueError('年份须为 1900–2100')
    if start is not None and end is not None and (start > end):
        raise ValueError('起始年份晚于结束年份')
    url, value = _get(ident + '/table/')
    if not isinstance(value, list):
        raise ValueError('表数据响应异常')
    out = []
    for row in value:
        if not isinstance(row, dict) or not isinstance(row.get('data'), list):
            raise ValueError('表行结构异常')
        if region is not None and str(row.get('id')) != region:
            continue
        row = dict(row)
        if start is not None or end is not None:
            filtered = []
            for point in row['data']:
                if not isinstance(point, dict):
                    raise ValueError('数据点格式异常')
                filtered.append({k: v for k, v in point.items() if not re.fullmatch('\\d{4}', str(k)) or ((start is None or int(k) >= start) and (end is None or int(k) <= end))})
            row['data'] = [x for x in filtered if x]
        out.append(row)
    return {'source': url, 'indicator': ident, 'rows': out, 'note': '筛选在本地执行；保留原始字段及地区，不等于全库查询。请先读取元数据确认单位、时间周期、初步数据及口径。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('browse')
    q.add_argument('parent', nargs='?', default=None)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--size', type=int, default=20)
    q = s.add_parser('metadata')
    q.add_argument('indicator')
    q = s.add_parser('data')
    q.add_argument('indicator')
    q.add_argument('--region')
    q.add_argument('--start', type=int)
    q.add_argument('--end', type=int)
    a = p.parse_args()
    v = browse(a.parent) if a.cmd == 'browse' else search(a.keyword, a.page, a.size) if a.cmd == 'search' else metadata(a.indicator) if a.cmd == 'metadata' else data(a.indicator, a.region, a.start, a.end)
    print(json.dumps(v, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
