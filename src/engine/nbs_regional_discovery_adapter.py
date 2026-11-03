"""Bounded category and geography discovery for NBS regional annual data."""
import release_runtime
from collections import deque
import nbs_new_regional_annual_adapter as api

def category_search(scope, keyword, parent_id='', max_requests=5):
    if scope not in ('province', 'city') or not isinstance(keyword, str) or (not keyword.strip()) or (len(keyword) > 100) or (type(max_requests) is not int) or (not 1 <= max_requests <= 20):
        raise ValueError('invalid scope, keyword or request limit')
    if parent_id:
        api._id(parent_id)
        queue = deque([(parent_id, [])])
        count = 0
    else:
        root = api.categories(scope)
        count = 1
        if len(root) != 1 or not api._id(root[0].get('_id')):
            raise RuntimeError('unexpected root')
        queue = deque([(root[0]['_id'], [root[0].get('_name')])])
    seen = set()
    found = []
    while queue and count < max_requests:
        parent, path = queue.popleft()
        if parent in seen:
            raise RuntimeError('repeated catalog node')
        seen.add(parent)
        children = api.categories(scope, parent)
        count += 1
        if not isinstance(children, list):
            raise RuntimeError('invalid catalog response')
        for x in children:
            id = api._id(x.get('_id'))
            name = x.get('_name')
            leaf = x.get('isLeaf')
            if not isinstance(name, str) or type(leaf) is not bool:
                raise RuntimeError('invalid catalog node')
            item = {'id': id, 'name': name, 'is_leaf': leaf, 'path': path + [name]}
            if keyword.casefold() in name.casefold():
                found.append(item)
            if not leaf:
                queue.append((id, path + [name]))
    return {'scope': scope, 'keyword': keyword, 'parent_id': parent_id or None, 'requests_used': count, 'complete_within_subtree': not queue, 'pending_parents': [{'id': i, 'path': p} for i, p in queue], 'matches': found, 'note': '仅匹配已访问目录名称，不搜索指标名称；限制请求量，若 pending_parents 非空则未遍历完整子树。可指定待查父节点继续；目录动态更新。'}

def areas(category_id, keyword='', region_category_id=''):
    api._id(category_id)
    if not isinstance(keyword, str) or len(keyword) > 100:
        raise ValueError('invalid keyword')
    tree = api.region_categories(category_id)
    if not isinstance(tree, list):
        raise RuntimeError('invalid area categories')

    def walk(nodes):
        for n in nodes:
            yield n
            yield from walk(n.get('children') or [])
    nodes = list(walk(tree))
    if region_category_id:
        api._id(region_category_id)
        hits = [x for x in nodes if x.get('_id') == region_category_id]
    else:
        hits = [x for x in nodes if x.get('_name') == '全部地区']
    if len(hits) != 1:
        raise ValueError('choose an explicit region category from official area tree')
    group = hits[0]
    items = api.regions(group['_id'])
    if not isinstance(items, list):
        raise RuntimeError('invalid area records')
    rows = [x for x in items if keyword.casefold() in (str(x.get('name_text', '')) + ' ' + str(x.get('name_value', ''))).casefold()]
    return {'category_id': category_id, 'region_category_id': group['_id'], 'region_category_name': group.get('_name'), 'matched': len(rows), 'areas': rows, 'note': '来自选定指标目录的官方地区分类；只代表地区可选，不保证指标与年份有观测。地区分类若未找到请先查原始分类树。'}
