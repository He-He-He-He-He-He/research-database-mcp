"""Bounded NBS regional annual indicator discovery in a chosen category subtree."""
import release_runtime
from collections import deque
import nbs_new_regional_annual_adapter as api

def search(scope, keyword, start_year, end_year, parent_id='', node_kind='branch', max_requests=8):
    if type(start_year) is not int or type(end_year) is not int or (not 1900 <= start_year <= end_year <= 2100):
        raise ValueError('年份范围无效')
    if scope not in ('province', 'city') or not isinstance(keyword, str) or (not keyword.strip()) or (len(keyword) > 100):
        raise ValueError('频率或关键词无效')
    if node_kind not in ('branch', 'leaf') or type(max_requests) is not int or (not 1 <= max_requests <= 20):
        raise ValueError('节点类型或请求上限无效')
    if not parent_id and node_kind != 'branch':
        raise ValueError('叶节点搜索需要 parent_id')
    if parent_id:
        api._id(parent_id)
        queue = deque([(node_kind, parent_id, [])])
        used = 0
    else:
        root = api.categories(scope)
        used = 1
        if not isinstance(root, list) or len(root) != 1:
            raise RuntimeError('目录根节点异常')
        queue = deque([('branch', api._id(root[0].get('_id')), [root[0].get('_name')])])
    seen = set()
    matches = []
    partial_leaves = []
    visited = []
    failed = []
    while queue and used < max_requests:
        kind, ident, path = queue.popleft()
        if (kind, ident) in seen:
            raise RuntimeError('目录出现重复节点')
        seen.add((kind, ident))
        used += 1
        if kind == 'branch':
            try:
                children = api.categories(scope, ident)
            except Exception as e:
                failed.append({'node_kind': kind, 'id': ident, 'path': path, 'error': type(e).__name__})
                continue
            if not isinstance(children, list):
                raise RuntimeError('目录响应异常')
            for x in children:
                cid = api._id(x.get('_id'))
                name = x.get('_name')
                leaf = x.get('isLeaf')
                if not isinstance(name, str) or type(leaf) is not bool:
                    raise RuntimeError('目录节点异常')
                queue.append(('leaf' if leaf else 'branch', cid, path + [name]))
        else:
            try:
                obj = api.indicators(ident, start_year, end_year, keyword.strip())
            except Exception as e:
                failed.append({'node_kind': kind, 'id': ident, 'path': path, 'error': type(e).__name__})
                continue
            items = obj.get('list') if isinstance(obj, dict) else None
            total = obj.get('total') if isinstance(obj, dict) else None
            if not isinstance(items, list) or not isinstance(total, int):
                raise RuntimeError('指标目录响应异常')
            visited.append({'category_id': ident, 'path': path, 'source_total': total, 'returned': len(items)})
            if total > len(items):
                partial_leaves.append({'category_id': ident, 'path': path, 'source_total': total, 'returned': len(items)})
            for row in items:
                if not isinstance(row, dict):
                    raise RuntimeError('指标数据格式异常')
                title = ' '.join((str(row.get(k) or '') for k in ('_name', 'i_showname', 'ek_name')))
                matches.append({'category_id': ident, 'category_path': path, 'literal_keyword_in_name': keyword.casefold() in title.casefold(), 'indicator': row})
    return {'source': '国家统计局国家数据新版地区年度指标', 'scope': scope, 'years': {'start': start_year, 'end': end_year}, 'keyword': keyword, 'requests_used': used, 'visited_leaves': visited, 'matches': matches, 'incomplete_source_leaves': partial_leaves, 'failed_nodes': failed, 'pending_nodes': [{'node_kind': k, 'id': i, 'path': p} for k, i, p in queue], 'complete_within_subtree': not queue and (not partial_leaves) and (not failed), 'note': '有限请求遍历，仅搜索已访问叶节点；待查节点可按其类型和 ID 继续，路径从该节点重新开始。指标匹配由上游执行，实测某些包含关键词的名称也可能未返回，不能将空结果视为不存在；literal_keyword_in_name 只说明名称是否含原词；上游可能截断，若 total 大于返回项会显式标注。失败节点可重试；指定节点未验证属于所选省份或城市目录，查看指标原始单位、注释和统计期。'}
