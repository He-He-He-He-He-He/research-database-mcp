"""教育部2026年普通高校名单本地快照：关键词检索与学校标识码详情。"""
import release_runtime
import argparse, json, re, sys
from pathlib import Path
DATA = Path(__file__).with_name('高校名单_普通高校_20260617.json')

def _load():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    if data.get('count') != len(data.get('items', [])):
        raise ValueError('高校名单快照条目数不一致')
    return data

def university_search(keyword='', region='', level=''):
    if level not in ('', '本科', '专科'):
        raise ValueError('办学层次应为本科或专科')
    d = _load()
    items = [x for x in d['items'] if keyword.casefold() in x['name'].casefold() and region in x['region'] and (not level or level == x['level'])]
    return {'source': d['source'], 'source_url': d['source_url'], 'source_sha256': d['source_sha256'], 'snapshot_total': d['count'], 'count': len(items), 'items': items, 'note': '本地快照，不包括成人高校；学校变化请核对教育部最新名单。'}

def university_detail(code):
    if not re.fullmatch('\\d{10}', code):
        raise ValueError('学校标识码须为 10 位数字')
    d = _load()
    items = [x for x in d['items'] if x['code'] == code]
    if not items:
        raise ValueError('当前快照中未找到该学校标识码')
    return {'source': d['source'], 'source_url': d['source_url'], 'item': items[0], 'note': '本地快照，不代表学校当前状态。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('search')
    q.add_argument('keyword', nargs='?', default='')
    q.add_argument('--region', default='')
    q.add_argument('--level', choices=['本科', '专科'], default='')
    q = s.add_parser('detail')
    q.add_argument('code')
    a = p.parse_args()
    print(json.dumps(university_search(a.keyword, a.region, a.level) if a.cmd == 'search' else university_detail(a.code), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
