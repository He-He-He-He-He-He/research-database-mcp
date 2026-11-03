"""财政部债务管理司地方政府债券与债务统计栏目。"""
import release_runtime
import argparse, json, sys
from treasury_statistics_adapters import Catalog, Body, fetch
BASE = 'https://zwgls.mof.gov.cn/tjsj/'

def local_debt_list(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别债务统计目录')
    return {'source': '财政部债务管理司统计数据', 'source_url': BASE, 'items': [dict(i, url=BASE + i['path']) for i in p.items.values() if keyword in i['title']], 'note': '仅当前首页标题筛选，非全国债券逐笔数据库或全站检索。'}

def local_debt_detail(path):
    matches = [i for i in local_debt_list()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别正文')
    return {'source': '财政部债务管理司统计数据', 'title': p.title, 'url': matches[0]['url'], 'text': text, 'note': '保留原始统计文字；非结构化数据。年度执行中地方政府债务余额为地方统计数据，口径以原文为准。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(local_debt_list(a.keyword) if a.cmd == 'list' else local_debt_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
