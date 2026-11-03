"""Bounded keyword discovery for the NBS national time-series category tree."""
import release_runtime
from collections import deque
import nbs_new_national_timeseries_adapter as api

def categories(frequency, keyword, parent_id='', max_requests=5):
    if frequency not in api.CODES or not isinstance(keyword, str) or (not keyword.strip()) or (len(keyword) > 100) or (type(max_requests) is not int) or (not 1 <= max_requests <= 20):
        raise ValueError('频率、关键词或请求上限无效')
    if parent_id:
        api._id(parent_id)
        queue = deque([(parent_id, [])])
        count = 0
    else:
        root = api.categories(frequency)
        count = 1
        if not isinstance(root, list) or len(root) != 1:
            raise RuntimeError('统计局目录根节点异常')
        api._id(root[0].get('_id'))
        queue = deque([(root[0]['_id'], [root[0].get('_name')])])
    seen = set()
    found = []
    while queue and count < max_requests:
        parent, path = queue.popleft()
        if parent in seen:
            raise RuntimeError('目录存在重复节点，停止遍历')
        seen.add(parent)
        children = api.categories(frequency, parent)
        count += 1
        if not isinstance(children, list):
            raise RuntimeError('统计局目录响应异常')
        for x in children:
            ident = api._id(x.get('_id'))
            name = x.get('_name')
            leaf = x.get('isLeaf')
            if not isinstance(name, str) or type(leaf) is not bool:
                raise RuntimeError('统计局目录节点异常')
            item = {'id': ident, 'name': name, 'is_leaf': leaf, 'path': path + [name]}
            if keyword.casefold() in name.casefold():
                found.append(item)
            if not leaf:
                queue.append((ident, path + [name]))
    return {'source': '国家统计局国家数据新版全国时间序列分类树', 'source_url': api.BASE + 'new/queryIndexTreeAsync', 'frequency': frequency, 'keyword': keyword, 'parent_id': parent_id or None, 'requests_used': count, 'complete_within_subtree': not queue, 'pending_parents': [{'id': i, 'path': p} for i, p in queue], 'matches': found, 'note': '仅搜索已访问的分类名称，不搜索指标名称；结果不完整时请按待查父节点继续。指定 parent_id 尚不证明其属于所选频率；查到叶级分类后使用全国指标查询，核对单位、注释及年度/月度/季度口径。目录可能更新。'}
