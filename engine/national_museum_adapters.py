"""中国国家博物馆藏品总目公开分页，只读。"""
import release_runtime
import argparse, json, math, re, sys
from research import fetch
BASE = 'https://www.chnmuseum.cn/portals/0/web/zt/cangpin/'

def museum_page(phase=1, page=1, keyword=''):
    if phase not in (1, 2) or not 1 <= page <= {1: 2516, 2: 3806}[phase]:
        raise ValueError('期次应为 1 或 2，页码应在官网范围内')
    chunk = (page - 1) // 6 + 1
    section = 'cangpin' if phase == 1 else 'cangpin2'
    u = BASE + 'json/' + section + '/cangpin_' + str(chunk) + '.js'
    raw = fetch(u).strip()
    prefix = 'var objs_' + str(chunk) + '='
    if not raw.startswith(prefix):
        raise ValueError('上游数据格式变化')
    try:
        d = json.loads(raw[len(prefix):].rstrip(';'))
    except json.JSONDecodeError:
        raise ValueError('上游数据不是可解析 JSON')
    rows = d.get('objs_' + str(chunk))
    if not isinstance(rows, list):
        raise ValueError('上游未返回数据数组')
    start = (page - 1) % 6 * 100
    selected = rows[start:start + 100]
    items = [{'id': x.get('id'), 'name': x.get('rname'), 'era': x.get('rera'), 'inventory_number': x.get('rnum')} for x in selected if keyword in (x.get('rname') or '')]
    return {'source': '中国国家博物馆藏品总目', 'source_url': BASE + 'colletionlist.html?id=' + str(phase), 'phase': phase, 'page': page, 'items': items, 'note': '仅筛选指定页的最多 100 条；非全库搜索，原官网还可能展示图片。'}

def museum_detail(phase, page, inventory_number):
    if not inventory_number or len(inventory_number) > 60:
        raise ValueError('请提供藏品普查编号')
    result = museum_page(phase, page)
    items = [x for x in result['items'] if x['inventory_number'] == inventory_number]
    if not items:
        raise ValueError('当前页没有此编号；需要指定其所在页')
    return {'source_url': result['source_url'], 'phase': phase, 'page': page, 'item': items[0], 'note': '仅为官网公开的目录字段；不等于完整藏品档案。'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='cmd', required=True)
    q = s.add_parser('page')
    q.add_argument('--phase', type=int, choices=[1, 2], default=1)
    q.add_argument('--page', type=int, default=1)
    q.add_argument('--keyword', default='')
    q = s.add_parser('detail')
    q.add_argument('inventory_number')
    q.add_argument('--phase', type=int, choices=[1, 2], default=1)
    q.add_argument('--page', type=int, default=1)
    a = p.parse_args()
    print(json.dumps(museum_page(a.phase, a.page, a.keyword) if a.cmd == 'page' else museum_detail(a.phase, a.page, a.inventory_number), ensure_ascii=False, indent=2))
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'error': str(e), 'note': '上游失败或结构变化，无自动重试'}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
