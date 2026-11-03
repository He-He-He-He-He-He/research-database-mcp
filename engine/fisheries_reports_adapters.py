"""农业农村部渔业渔政管理局工作动态与渔业统计公报。"""
import release_runtime
import argparse, json, sys
from farm_reclamation_adapters import Catalog, Body, fetch
BASE = 'https://yyj.moa.gov.cn/gzdt/'

def fisheries_reports(keyword=''):
    p = Catalog()
    p.feed(fetch(BASE))
    if not p.items:
        raise ValueError('未识别渔业渔政工作动态')
    return {'source': '农业农村部渔业渔政管理局工作动态', 'source_url': BASE, 'items': [dict(i, url=BASE + i['path']) for i in p.items.values() if keyword in i['title']], 'note': '仅筛选当前首页标题，不是全部渔业数据或全站检索。'}

def fisheries_report_detail(path):
    matches = [i for i in fisheries_reports()['items'] if i['path'] == path]
    if not matches:
        raise ValueError('路径不在当前目录首页')
    p = Body()
    p.feed(fetch(matches[0]['url']))
    text = '\n'.join((x.strip() for x in ''.join(p.parts).splitlines() if x.strip()))
    if not text:
        raise ValueError('未识别正文')
    return {'source': '农业农村部渔业渔政管理局工作动态', **matches[0], 'text': text, 'note': '只提取文字；图表、附件及统计口径请核对原文。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q = s.add_parser('detail')
    q.add_argument('path')
    a = p.parse_args()
    print(json.dumps(fisheries_reports(a.keyword) if a.cmd == 'list' else fisheries_report_detail(a.path), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或网页结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
