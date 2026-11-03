"""Search one page, then retrieve one explicitly selected result."""
import release_runtime
import re
from drcnet_ip_catalog_adapter import search, detail_reference
from drcnet_institution_article_adapter import article

def search_article(keyword, page=1, limit=5, selection=1, field='title', start_date=None, end_date=None, source=''):
    if isinstance(selection, bool) or not isinstance(selection, int) or selection < 1 or (selection > limit):
        raise ValueError('selection 须为当前页中从 1 开始的序号')
    results = search(keyword, page, limit, field, start_date, end_date, source)
    if selection > len(results['items']):
        raise ValueError('所选序号超出当前页实际结果')
    item = results['items'][selection - 1]
    code = str(item.get('code') or '')
    ref=detail_reference(item)
    if ref is None:raise RuntimeError('检索结果缺少可核验的文章或栏目编号')
    detail=article(ref['doc_id'],ref['leaf_id'],ref['channel_id'],ref['expected_title'])
    if detail['article_code'] != code:
        raise RuntimeError('详情编号与所选检索结果不一致')
    return {'query': results['query'], 'page': page, 'selection': selection, 'search_total': results['total'], 'search_total_relation': results['total_relation'], 'selected_item': item, 'article': detail, 'note': '检索排序可能变化，序号对应本次实时查询结果；仅返回选中的一篇。'}
