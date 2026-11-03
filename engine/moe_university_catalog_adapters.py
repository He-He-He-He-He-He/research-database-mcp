"""教育部最新公布全国高校名单，读取原始 XLS 并筛选。"""
import release_runtime
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin
sys.path.insert(0, str(Path(__file__).resolve().parent / 'vendor'))
import xlrd
INDEX = 'https://www.moe.gov.cn/jyb_xxgk/s5743/s5744/A03/'

def fetch(url):
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', url], capture_output=True, timeout=35)
    if p.returncode:
        raise RuntimeError('教育部数据请求失败: ' + p.stderr.decode(errors='replace').strip())
    return p.stdout

def search(keyword='', province='', category='all', page=1, page_size=20):
    if category not in ('all', '普通', '成人') or not 1 <= int(page) <= 10000 or (not 1 <= int(page_size) <= 100):
        raise ValueError('类型须为 all、普通或成人；页码须为正数，每页数量须为 1–100')
    index = fetch(INDEX).decode('utf-8')
    match = re.search('<a\\s+href="([^"]+)"[^>]*title="全国高等学校名单"', index)
    if not match:
        raise RuntimeError('未找到最新全国高等学校名单公告')
    announcement = urljoin(INDEX, html.unescape(match.group(1)))
    source = fetch(announcement).decode('utf-8')
    files = {}
    for href, title in re.findall('<a\\b[^>]*href="([^"]+\\.xls)"[^>]*>(.*?)</a>', source, re.S | re.I):
        title = html.unescape(re.sub('<[^>]+>', '', title))
        for kind in ('普通', '成人'):
            if '全国' + kind + '高等学校名单' in title:
                files[kind] = urljoin(announcement, html.unescape(href))
    if len(files) != 2:
        raise RuntimeError('最新公告缺少预期的两个 XLS 名单')
    items = []
    for kind in ('普通', '成人'):
        if category not in ('all', kind):
            continue
        sheet = xlrd.open_workbook(file_contents=fetch(files[kind])).sheet_by_index(0)
        header_idx = next((i for i in range(min(sheet.nrows, 10)) if '学校名称' in sheet.row_values(i) and '学校标识码' in sheet.row_values(i)), None)
        if header_idx is None:
            raise RuntimeError('高校名单表头已变化')
        headers = [str(x).strip() for x in sheet.row_values(header_idx)]
        region = ''
        for r in range(header_idx + 1, sheet.nrows):
            row = sheet.row_values(r)
            if not row[1] and isinstance(row[0], str):
                region = re.sub('[（(].*', '', row[0]).strip()
                continue
            if not row[1]:
                continue
            record = dict(zip(headers, row))
            if not record.get('学校名称') or not record.get('学校标识码'):
                continue
            code = record['学校标识码']
            record['学校标识码'] = str(int(code)) if isinstance(code, float) and code.is_integer() else str(code).strip()
            record['序号'] = int(record['序号']) if isinstance(record['序号'], float) and record['序号'].is_integer() else record['序号']
            record['省级地区'] = region
            record['名单类别'] = kind
            if keyword in str(record['学校名称']) and province in region:
                items.append(record)
    start = (int(page) - 1) * int(page_size)
    return {'source': '教育部全国高等学校名单', 'announcement_url': announcement, 'file_urls': files, 'category': category, 'keyword': keyword, 'province': province, 'page': int(page), 'page_size': int(page_size), 'total': len(items), 'items': items[start:start + int(page_size)]}
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword', nargs='?', default='')
    p.add_argument('--province', default='')
    p.add_argument('--category', choices=('all', '普通', '成人'), default='all')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--page-size', type=int, default=20)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.province, a.category, a.page, a.page_size), ensure_ascii=False, indent=2))
