"""湖北省科学技术厅公开政策文件数据，只读。"""
import release_runtime
import argparse, json, sys
from research import get
URL = 'https://kjt.hubei.gov.cn/fzlm/xxgkgzfzlm/zc/zclist.json'

def search(keyword='', category='', status='', page=1, size=10):
    if not 1 <= page <= 10000 or not 1 <= size <= 50:
        raise ValueError('页码必须大于零，每页 1 至 50 条')
    payload = get(URL)
    if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
        raise ValueError('上游响应不是预期的政策文件列表')
    rows = payload['data']
    selected = []
    for x in rows:
        if not isinstance(x, dict):
            continue
        if keyword.casefold() not in str(x.get('DOCTITLE', '')).casefold():
            continue
        if category and category != x.get('channel'):
            continue
        if status and status != x.get('Effectivestate'):
            continue
        selected.append(x)
    start = (page - 1) * size
    return {'source': URL, 'total_source': len(rows), 'total_matched': len(selected), 'page': page, 'size': size, 'scope': '上游静态数据集本地标题筛选，状态以数据文件为准', 'items': selected[start:start + size]}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('keyword', nargs='?', default='')
    p.add_argument('--category', default='')
    p.add_argument('--status', default='')
    p.add_argument('--page', type=int, default=1)
    p.add_argument('--size', type=int, default=10)
    a = p.parse_args()
    print(json.dumps(search(a.keyword, a.category, a.status, a.page, a.size), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
