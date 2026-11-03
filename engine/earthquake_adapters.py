"""中国地震台网最新地震目录，只读单次查询。"""
import release_runtime
import argparse, json, re, sys
from research import get
URL = 'https://www.ceic.ac.cn/data/data.json'

def _data():
    d = get(URL)
    if not isinstance(d, list):
        raise ValueError('地震目录响应结构变化')
    return [x for x in d if not ((x.get('location') or '').startswith('北京') and isinstance(x.get('magnitude'), (int, float)) and (x['magnitude'] < 2))]

def earthquake_list(keyword='', limit=30):
    if not 1 <= limit <= 100:
        raise ValueError('limit 必须为 1–100')
    d = _data()
    items = [x for x in d if keyword in (x.get('location') or '')]
    return {'source': '中国地震台网', 'source_url': 'https://www.ceic.ac.cn/', 'time_zone': '北京时间', 'scope': '官网当前数据文件，本地按参考位置筛选', 'matched': len(items), 'items': items[:limit], 'note': '目录动态更新，速报可能修订；不是历史全目录，也不能作为紧急预警。'}

def earthquake_detail(id):
    if not re.fullmatch('[A-Za-z0-9.\\-_]{5,80}', id):
        raise ValueError('地震记录 ID 格式错误')
    rows = [x for x in _data() if x.get('id') == id]
    if not rows:
        raise ValueError('当前数据文件中没有此记录，可能已更新或移出')
    return {'source': '中国地震台网', 'source_url': 'https://www.ceic.ac.cn/', 'time_zone': '北京时间', 'item': rows[0], 'note': '当前速报记录可能修订；不提供完整历史。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('list')
    q.add_argument('keyword', nargs='?', default='')
    q.add_argument('--limit', type=int, default=30)
    q = s.add_parser('detail')
    q.add_argument('id')
    a = p.parse_args()
    print(json.dumps(earthquake_list(a.keyword, a.limit) if a.cmd == 'list' else earthquake_detail(a.id), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
