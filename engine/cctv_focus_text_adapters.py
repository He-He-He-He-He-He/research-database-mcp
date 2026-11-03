"""央视《焦点访谈》整期分页和视频页面配套文字。"""
import release_runtime
import argparse
import datetime
import json
from cctv_programs_adapters import programs
from cctv_xwlb_text_adapters import article
COLUMN = 'TOPC1451558976694518'

def episodes(page=1, page_size=20, date='', keyword=''):
    if date:
        datetime.date.fromisoformat(date)
    result = programs(page=page, page_size=page_size, mode=0, column_id=COLUMN, keyword=keyword)
    if date:
        result['items'] = [x for x in result['items'] if str(x.get('time', '')).startswith(date)]
    result['date_filter'] = date or None
    result['filter_scope'] = '仅当前页的上游标题、简介及时间，不是全库检索'
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    e = sub.add_parser('episodes')
    e.add_argument('--page', type=int, default=1)
    e.add_argument('--page-size', type=int, default=20)
    e.add_argument('--date', default='')
    e.add_argument('--keyword', default='')
    a = sub.add_parser('article')
    a.add_argument('url')
    x = p.parse_args()
    result = episodes(x.page, x.page_size, x.date, x.keyword) if x.command == 'episodes' else article(x.url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
if __name__ == '__main__':
    main()
