"""央视网历史滚动新闻 JSON 日期索引；分页、标题和栏目筛选。"""
import release_runtime
import argparse
import datetime
import json
import requests
ROOT = 'https://news.cntv.cn/update/data/'

def day(date, page=1, page_size=20, keyword='', category=''):
    d = datetime.date.fromisoformat(date)
    if page < 1 or not 1 <= page_size <= 100:
        raise ValueError('page 须大于零，page_size 须在 1 到 100 之间')
    url = f'{ROOT}{d:%Y%m%d}.json'
    r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
    r.raise_for_status()
    if requests.utils.urlparse(r.url).hostname != 'news.cntv.cn':
        raise ValueError('跨域跳转，停止读取')
    obj = r.json()
    records = obj.get('rollData')
    if not isinstance(records, list):
        raise ValueError('滚动新闻格式发生变化')
    rows = [x for x in records if isinstance(x, dict) and keyword.casefold() in str(x.get('title', '')).casefold() and (category in str(x.get('brief', '')))]
    start = (page - 1) * page_size
    return {'date': date, 'source_url': url, 'total_before_filter': len(records), 'total_after_filter': len(rows), 'page': page, 'page_size': page_size, 'scope': '网站该日期 JSON；标题与栏目本地筛选', 'items': rows[start:start + page_size]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('date')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--page-size', type=int, default=20)
    p.add_argument('--keyword', default='')
    p.add_argument('--category', default='')
    a = p.parse_args()
    print(json.dumps(day(a.date, a.page, a.page_size, a.keyword, a.category), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
