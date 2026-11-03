"""财政部国有企业经济运行数据。"""
import release_runtime
import argparse, json, sys
from treasury_statistics_adapters import Catalog, Body, fetch
BASE = 'https://zcgls.mof.gov.cn/qiyeyunxingdongtai/'

def soe_economy_list(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别国企运行目录')
    return {'source': '财政部国有企业运行情况专栏', 'source_url': BASE, 'items': [dict(i, url=BASE + i['path']) for i in p.items.values() if keyword in i['title']], 'note': '仅当前目录首页标题筛选，不是逐企业数据。'}

def soe_economy_detail(path):
    matches = [i for i in soe_economy_list()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not p.title or not text:
        raise ValueError('未识别正文')
    return {'source': '财政部国有企业运行情况专栏', 'title': p.title, 'url': matches[0]['url'], 'text': text, 'note': '保留原统计注释；数据范围和可比性以原文为准，不含国有一级金融企业及其所属企业。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(soe_economy_list(a.keyword) if a.cmd == 'list' else soe_economy_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
