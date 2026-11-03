"""马来西亚官方开放数据与统计局 OpenDOSM 目录和数据接口。"""
import release_runtime
import argparse
from datetime import date
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.parse import urlencode
from bs4 import BeautifulSoup
SITE = 'https://open.dosm.gov.my/data-catalogue'
API = 'https://api.data.gov.my/'
MAX_BYTES = 8000000

def _fetch(url):
    p = release_runtime.run(['/usr/bin/curl', '--fail', '--silent', '--show-error', '--compressed', '--max-time', '30', '--max-filesize', str(MAX_BYTES), url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('马来西亚官方数据请求失败：' + p.stderr.decode('utf-8', 'replace')[:400])
    if len(p.stdout) > MAX_BYTES:
        raise ValueError('响应超过大小上限')
    return p.stdout

def search(keyword, limit=30):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 150:
        raise ValueError('请输入关键词')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('结果数须为 1–100')
    soup = BeautifulSoup(_fetch(SITE), 'html.parser')
    items = []
    seen = set()
    for a in soup.find_all('a', href=True):
        match = re.fullmatch('/data-catalogue/([a-z0-9_]+)', a['href'])
        if not match or match.group(1) in seen:
            continue
        ident = match.group(1)
        title = a.get_text(' ', strip=True)
        seen.add(ident)
        if keyword.casefold() in (ident + ' ' + title).casefold():
            items.append({'id': ident, 'text': title, 'url': SITE + '/' + ident})
    if not seen:
        raise ValueError('未识别目录链接')
    return {'source': SITE, 'total_visible': len(seen), 'matched': len(items), 'items': items[:limit], 'note': '当前目录 HTML 中可见项目的本地匹配，不保证全部项目、全部页或每项均支持 API。'}

def _id(value):
    if not isinstance(value, str) or not re.fullmatch('[a-z0-9_]{1,100}', value):
        raise ValueError('无效数据集 ID')
    return value

def metadata(dataset):
    url = SITE + '/' + _id(dataset)
    soup = BeautifulSoup(_fetch(url), 'html.parser')
    for e in soup(['script', 'style', 'noscript']):
        e.decompose()
    text = soup.get_text(' ', strip=True)
    if len(text) < 100 or 'Metadata' not in text:
        raise ValueError('未识别公开元数据页面')
    return {'source': url, 'page_title': soup.title.get_text(' ', strip=True) if soup.title else '', 'text': text[:30000], 'note': '页面可见文本提取；可能截断、含导航和动态内容，使用前请核对原站表头、单位、方法和更新日期。'}

def _query_limited(endpoint, url):
    lock_path = Path(tempfile.gettempdir()) / ('zju-research-malaysia-' + str(os.getuid()) + '-' + endpoint + '.lock')
    with open(lock_path, 'a+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        raw = f.read().strip()
        try:
            last = float(raw)
        except ValueError:
            last = 0
        delay = 16 - (time.time() - last)
        if delay > 0:
            time.sleep(min(delay, 16))
        f.seek(0)
        f.truncate()
        f.write(str(time.time()))
        f.flush()
        try:
            return _fetch(url)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def records(dataset, endpoint='data-catalogue', filters=None, start='', end='', date_column='date', limit=100):
    _id(dataset)
    if endpoint not in ('opendosm', 'data-catalogue'):
        raise ValueError('无效数据端点')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 1000):
        raise ValueError('limit 须在 1–1000')
    if not isinstance(date_column, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', date_column):
        raise ValueError('日期列无效')
    if bool(start) != bool(end):
        raise ValueError('起止日期须同时提供')
    params = {'id': dataset, 'limit': limit}
    if start:
        try:
            a = date.fromisoformat(start)
            b = date.fromisoformat(end)
        except (TypeError, ValueError):
            raise ValueError('日期须为 YYYY-MM-DD')
        if a > b:
            raise ValueError('起止日期顺序错误')
        params['date_start'] = start + '@' + date_column
        params['date_end'] = end + '@' + date_column
    if filters:
        if not isinstance(filters, dict) or len(filters) > 8:
            raise ValueError('过滤条件无效')
        values = []
        for key, value in filters.items():
            if not isinstance(key, str) or not re.fullmatch('[A-Za-z0-9_]{1,80}', key) or (not isinstance(value, str)) or (not value) or (len(value) > 100) or (',' in value) or ('@' in value):
                raise ValueError('精确筛选字段或值无效')
            values.append(value + '@' + key)
        params['filter'] = ','.join(values)
    url = API + endpoint + '/?' + urlencode(params)
    data = json.loads(_query_limited(endpoint, url))
    if not isinstance(data, list):
        raise ValueError('数据响应不是记录列表，请核对数据集及筛选字段')
    return {'source': url, 'dataset': dataset, 'returned': len(data), 'limit': limit, 'records': data, 'note': '结果上限是截断条件，达到上限不代表全集；请查元数据确认单位、统计口径、日期和过滤字段。未实现分页或总数。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--limit', type=int, default=30)
    q = s.add_parser('metadata')
    q.add_argument('dataset')
    q = s.add_parser('records')
    q.add_argument('dataset')
    q.add_argument('--endpoint', choices=['data-catalogue', 'opendosm'], default='data-catalogue')
    q.add_argument('--filters', default='{}')
    q.add_argument('--start', default='')
    q.add_argument('--end', default='')
    q.add_argument('--date-column', default='date')
    q.add_argument('--limit', type=int, default=100)
    a = p.parse_args()
    x = search(a.keyword, a.limit) if a.cmd == 'search' else metadata(a.dataset) if a.cmd == 'metadata' else records(a.dataset, a.endpoint, json.loads(a.filters), a.start, a.end, a.date_column, a.limit)
    print(json.dumps(x, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
