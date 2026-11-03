"""Search one page, then retrieve one explicitly selected result."""
import release_runtime
import re
from drcnet_ip_catalog_adapter import search
from drcnet_institution_article_adapter import article

def search_article(keyword, page=1, limit=5, selection=1, field='title', start_date=None, end_date=None, source=''):
    if isinstance(selection, bool) or not isinstance(selection, int) or selection < 1 or (selection > limit):
        raise ValueError('selection 须为当前页中从 1 开始的序号')
    results = search(keyword, page, limit, field, start_date, end_date, source)
    if selection > len(results['items']):
        raise ValueError('所选序号超出当前页实际结果')
    item = results['items'][selection - 1]
    code = str(item.get('code') or '')
    match = re.fullmatch('[A-Za-z0-9]+_([0-9]{1,12})', code)
    leaves = str(item.get('leafIds') or '').split()
    paths = [p.split('_') for p in str(item.get('chnidPath') or '').split()]
    candidates = [p for p in paths if len(p) > 1 and p[-1] in leaves and all((re.fullmatch('[0-9]{1,12}', x) for x in p))]
    if not match or not candidates:
        raise RuntimeError('检索结果缺少可核验的文章或栏目编号')
    path = candidates[0]
    detail = article(match.group(1), path[-1], path[-2], item['title'])
    if detail['article_code'] != code:
        raise RuntimeError('详情编号与所选检索结果不一致')
    return {'query': results['query'], 'page': page, 'selection': selection, 'search_total': results['total'], 'search_total_relation': results['total_relation'], 'selected_item': item, 'article': detail, 'note': '检索排序可能变化，序号对应本次实时查询结果；仅返回选中的一篇。'}
