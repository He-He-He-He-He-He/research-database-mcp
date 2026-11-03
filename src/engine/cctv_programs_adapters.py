"""央视网栏目视频元数据：节目完整期及分段列表。"""
import release_runtime
import argparse
import json
import re
import requests
API = 'https://api.cntv.cn/NewVideo/getVideoListByColumn'
DEFAULT_COLUMN = 'TOPC1451559180488841'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0'

def programs(page=1, page_size=20, mode=0, column_id=DEFAULT_COLUMN, keyword=''):
    if not 1 <= page <= 10000 or not 1 <= page_size <= 100 or mode not in (0, 1, 2):
        raise ValueError('page 须为正整数；page_size 1—100；mode 0、1 或 2')
    if not re.fullmatch('TOPC\\d{16}', column_id):
        raise ValueError('栏目 ID 格式无效')
    params = {'id': column_id, 'n': page_size, 'sort': 'desc', 'p': page, 'mode': mode, 'serviceId': 'tvcctv'}
    r = requests.get(API, params=params, headers={'User-Agent': USER_AGENT}, timeout=30)
    r.raise_for_status()
    if requests.utils.urlparse(r.url).hostname != 'api.cntv.cn':
        raise ValueError('跨域跳转')
    data = r.json()
    if not isinstance(data.get('data'), dict) or not isinstance(data['data'].get('list'), list):
        raise ValueError(f"接口未返回栏目列表: {data.get('msg', '格式变化')}")
    rows = data['data']['list']
    return {'endpoint': API, 'column_id': column_id, 'mode': mode, 'page': page, 'page_size': page_size, 'upstream_total': data['data'].get('total'), 'keyword_scope': '当前页标题或简介', 'items': [x for x in rows if keyword.casefold() in (str(x.get('title', '')) + ' ' + str(x.get('brief', ''))).casefold()]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--page-size', type=int, default=20)
    p.add_argument('--mode', type=int, choices=[0, 1, 2], default=0)
    p.add_argument('--column-id', default=DEFAULT_COLUMN)
    p.add_argument('--keyword', default='')
    a = p.parse_args()
    print(json.dumps(programs(a.page, a.page_size, a.mode, a.column_id, a.keyword), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
