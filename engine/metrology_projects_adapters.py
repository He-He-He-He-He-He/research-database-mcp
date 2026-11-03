"""国家计量科学数据中心公开科研项目目录；仅查询元数据。"""
import release_runtime
import html
import json
import re
import subprocess
from urllib.parse import urlencode, urljoin
BASE = 'https://www.nmdc.ac.cn'
LIST = BASE + '/dcs/front/project/list'

def search(keyword='', page=1, page_size=30):
    if not 1 <= int(page) <= 10000 or not 1 <= int(page_size) <= 100:
        raise ValueError('页码须为正数；每页数量须为 1–100')
    url = LIST + '?' + urlencode({'proName': keyword, 'pageNo': page, 'pageSize': page_size})
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', url], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('计量中心请求失败: ' + p.stderr.strip())
    source = p.stdout
    if 'ky-list xm-list' not in source:
        raise RuntimeError('计量中心响应不是预期的项目列表，可能站点已变化')
    section = source.split('ky-list xm-list', 1)[1].split('</ul>', 1)[0]
    records = []
    for block in re.findall('<li class="item">(.*?)</li>', section, re.S):
        link = re.search('<a href="([^"]+)"[^>]*class="title">(.*?)</a>', block, re.S)
        if not link:
            continue
        clean = lambda x: html.unescape(re.sub('<[^>]*>', '', x)).strip()
        item = {'title': clean(link.group(2)), 'url': urljoin(BASE, html.unescape(link.group(1)))}
        for name, value in re.findall('<span><em>(.*?)</em>(.*?)</span>', block, re.S):
            item[clean(name).rstrip('：:')] = clean(value)
        records.append(item)
    total = re.search('共\\s*(\\d+)\\s*条', source)
    if total is None:
        raise RuntimeError('未找到分页总数，站点响应格式可能变化')
    return {'source': '国家计量科学数据中心科研项目列表', 'keyword': keyword, 'page': int(page), 'page_size': int(page_size), 'total': int(total.group(1)), 'items': records}
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('keyword', nargs='?', default='')
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--page-size', type=int, default=30)
    args = parser.parse_args()
    print(json.dumps(search(args.keyword, args.page, args.page_size), ensure_ascii=False, indent=2))
