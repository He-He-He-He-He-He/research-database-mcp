"""SciVal Topic Cluster 机构/国家目录与详情。"""
import release_runtime
from scival_topics_adapter import _id, _item
from elsevier_scival_official_adapter import _fetch, RANGES
BASE = 'https://api.elsevier.com/analytics/scival/topicCluster/'
DOC = 'https://dev.elsevier.com/documentation/SciValTopicClusterAPI.wadl'

def list_clusters(kind, entity_id, start=1, limit=10, year_range='5yrs'):
    if kind not in ('institution', 'country'):
        raise ValueError('kind 须为 institution 或 country')
    _id(entity_id)
    if type(start) is not int or not 1 <= start <= 1000000 or type(limit) is not int or (not 1 <= limit <= 50) or (year_range not in RANGES):
        raise ValueError('参数范围无效')
    path = ('institutionId/' if kind == 'institution' else 'countryId/') + entity_id
    raw, key = _fetch(path, {'offset': start, 'limit': limit, 'yearRange': year_range}, BASE)
    rows = raw.get('topicClusters')
    total = raw.get('totalCount')
    if not isinstance(rows, list) or len(rows) > limit or type(total) is not int or (total < 0):
        raise RuntimeError('SciVal 主题簇列表或总数异常')
    items = [_item(x, key) for x in rows]
    return {'source': 'Elsevier SciVal Topic Cluster Lookup API', 'documentation': DOC, 'entity_type': kind, 'entity_id': entity_id, 'start': start, 'limit': limit, 'yearRange_requested': year_range, 'total': total, 'items': items, 'next_start': start + len(items) if items and start - 1 + len(items) < total else None, 'note': '2026-11-02 机构样例每两条用 offset 1、3 连续得到不同结果，按实测一基位置传参；与官方文档页偏移描述不一致，其他页及服务变动须复核。结果排序和总数可变化；主题簇及指标为 SciVal/Scopus 口径，不代表全部成果。'}

def detail(cluster_id):
    _id(cluster_id, True)
    raw, key = _fetch(cluster_id, {}, BASE)
    item = _item(raw.get('topicCluster'), key)
    if item['id'] != int(cluster_id):
        raise RuntimeError('SciVal 返回主题簇 ID 不一致')
    return {'source': 'Elsevier SciVal Topic Cluster Lookup API', 'documentation': DOC, 'topicCluster': item, 'note': '主题簇及指标来自 SciVal 基于 Scopus 的分类，单项指标口径和数据覆盖需结合官方定义核对。'}
