"""全国标准信息公共服务平台行业标准，只读。"""
import release_runtime
import argparse, json, re, sys
from research import get, fetch
from local_standards_adapters import Detail
BASE = 'https://std.samr.gov.cn/'

def industry_search(keyword, page=1):
    if not keyword.strip() or not 1 <= page <= 100:
        raise ValueError('请输入关键词及 1–100 的页码')
    data = get(BASE + 'hb/search/hbPage', {'searchText': keyword, 'op': '', 'ISSUE_DATE': '', 'pageNumber': page, 'pageSize': 10})
    if not isinstance(data.get('rows'), list):
        raise ValueError('行业标准查询响应结构变化')
    items = []
    for row in data['rows']:
        item = dict(row)
        id = item.get('id', '')
        if re.fullmatch('[0-9a-fA-F]{32}', id):
            item['detail_url'] = BASE + 'hb/search/stdHBDetailed?id=' + id
        items.append(item)
    return {'source': '全国标准信息公共服务平台行业标准', 'source_url': BASE + 'hb/hbQuery', 'keyword': keyword, 'page': page, 'total': data.get('total'), 'items': items, 'note': '返回行业标准题录；效力状态、全文与适用范围以官方详情为准。'}

def industry_detail(id):
    if not re.fullmatch('[0-9a-fA-F]{32}', id):
        raise ValueError('行业标准 ID 应为 32 位十六进制')
    u = BASE + 'hb/search/stdHBDetailed?id=' + id
    p = Detail()
    p.feed(fetch(u))
    if not p.title or not p.fields:
        raise ValueError('未识别标准详情，页面可能改版')
    return {'source_url': u, 'title': p.title.strip(), 'fields': p.fields, 'note': '基础题录，状态和全文请核对官网。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword')
    q.add_argument('--page', type=int, default=1)
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(industry_search(a.keyword, a.page) if a.cmd == 'search' else industry_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
