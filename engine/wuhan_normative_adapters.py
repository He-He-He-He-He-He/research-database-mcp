"""武汉市行政规范性文件统一发布平台：读取公开目录并本地筛选。"""
import release_runtime
import json
import re
import subprocess
URL = 'https://www.wuhan.gov.cn/gfk/index.jsonp'
PREFIX = 'pushInfoJsonpCallBack('

def search(keyword='', page=1, page_size=20, agency='', status='', number=''):
    if not 1 <= int(page) <= 10000 or not 1 <= int(page_size) <= 100:
        raise ValueError('页码须为正整数，每页数量须为 1–100')
    p = release_runtime.run(['curl', '--fail', '--silent', '--show-error', '--location', '--max-time', '30', URL], capture_output=True, text=True, timeout=35)
    if p.returncode:
        raise RuntimeError('武汉文件库请求失败: ' + p.stderr.strip())
    body = p.stdout.strip()
    if not body.startswith(PREFIX) or not re.search('\\)\\s*;?\\s*$', body):
        raise RuntimeError('响应不符合预期的目录格式')
    decoder = json.JSONDecoder()
    records = []
    for match in re.finditer('\\{\\s*"tit"\\s*:', body):
        try:
            item, _ = decoder.raw_decode(body, match.start())
        except ValueError as exc:
            raise RuntimeError('文件库目录记录解析失败，站点可能已变化') from exc
        if not isinstance(item, dict) or not all((k in item for k in ('tit', 'url', 'pub', 'num', 'es'))):
            raise RuntimeError('文件库目录字段已变化')
        if keyword in str(item['tit']) and agency in str(item['pub']) and (number in str(item['num'])) and (not status or status == item['es']):
            records.append(item)
    if not re.search('\\{\\s*"tit"\\s*:', body):
        raise RuntimeError('未在目录中找到记录，站点可能已变化')
    records.sort(key=lambda item: str(item.get('tim', '')), reverse=True)
    start = (int(page) - 1) * int(page_size)
    return {'source': '武汉市行政规范性文件统一发布平台', 'keyword': keyword, 'page': int(page), 'page_size': int(page_size), 'total': len(records), 'items': records[start:start + int(page_size)]}
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('keyword', nargs='?', default='')
    parser.add_argument('--page', type=int, default=1)
    parser.add_argument('--page-size', type=int, default=20)
    parser.add_argument('--agency', default='')
    parser.add_argument('--status', default='')
    parser.add_argument('--number', default='')
    args = parser.parse_args()
    print(json.dumps(search(args.keyword, args.page, args.page_size, args.agency, args.status, args.number), ensure_ascii=False, indent=2))
