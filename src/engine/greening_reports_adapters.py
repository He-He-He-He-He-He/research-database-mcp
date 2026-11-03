"""国家林业和草原局国土绿化报告公开栏目。"""
import release_runtime
import argparse, json, sys
from forestry_reports_adapters import Catalog, Body, fetch
INDEX = 'https://www.forestry.gov.cn/c/www/gtlhbg.jhtml'

def greening_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(INDEX))
    if not p.items:
        raise ValueError('未识别国土绿化报告目录')
    return {'source': '国家林业和草原局国土绿化报告', 'source_url': INDEX, 'items': [i for i in p.items if keyword in i['title']], 'note': '当前目录首页标题筛选，不是完整林草调查数据库。'}

def greening_report_detail(path):
    matches = [i for i in greening_reports()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别公报正文')
    return {'source': '国家林业和草原局国土绿化报告', **matches[0], 'text': text, 'note': '提取正文文字；图表、口径与数据请以原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(greening_reports(a.keyword) if a.cmd == 'list' else greening_report_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
