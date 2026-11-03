"""SciVal 机构/国家研究主题与主题详情；保留原始指标。"""
import release_runtime
import math
import re
from elsevier_scival_official_adapter import _fetch, _text, RANGES
BASE = 'https://api.elsevier.com/analytics/scival/topic/'
DOC = 'https://dev.elsevier.com/documentation/SciValTopicAPI.wadl'

def _id(value, allow_zero=False):
    pattern = '(?:0|[1-9][0-9]{0,11})' if allow_zero else '[1-9][0-9]{0,11}'
    if not isinstance(value, str) or not re.fullmatch(pattern, value):
        raise ValueError('ID 须为有效数字字符串')
    return value

def _item(x, key):
    if not isinstance(x, dict) or type(x.get('id')) is not int or x['id'] < 0:
        raise RuntimeError('SciVal 主题 ID 异常')
    out = {'id': x['id'], 'name': _text(x.get('name'), key)}
    for field in ('prominencePercentile', 'scholarlyOutput', 'overallScholarlyOutput'):
        if field in x:
            v = x[field]
            if v is not None and (type(v) not in (int, float) or not math.isfinite(v)):
                raise RuntimeError('SciVal 主题指标非有效数字')
            out[field] = v
    cluster = x.get('topicCluster')
    if cluster is not None:
        if not isinstance(cluster, dict) or type(cluster.get('id')) is not int or cluster['id'] < 0:
            raise RuntimeError('SciVal 主题簇 ID 异常')
        out['topicCluster'] = {'id': cluster['id'], 'name': _text(cluster.get('name'), key)}
    return out

def list_topics(kind, entity_id, start=1, limit=10, year_range='5yrs'):
    if kind not in ('institution', 'country'):
        raise ValueError('kind 须为 institution 或 country')
    _id(entity_id)
    if type(start) is not int or not 1 <= start <= 1000000 or type(limit) is not int or (not 1 <= limit <= 50) or (year_range not in RANGES):
        raise ValueError('参数范围无效')
    path = ('institutionId/' if kind == 'institution' else 'countryId/') + entity_id
    raw, key = _fetch(path, {'offset': start, 'limit': limit, 'yearRange': year_range}, BASE)
    rows = raw.get('topics')
    total = raw.get('totalCount')
    if not isinstance(rows, list) or len(rows) > limit or type(total) is not int or (total < 0):
        raise RuntimeError('SciVal 主题列表或总数异常')
    items = [_item(x, key) for x in rows]
    return {'source': 'Elsevier SciVal Topic Lookup API', 'documentation': DOC, 'entity_type': kind, 'entity_id': entity_id, 'start': start, 'limit': limit, 'yearRange_requested': year_range, 'total': total, 'items': items, 'next_start': start + len(items) if items and start - 1 + len(items) < total else None, 'note': '2026-11-02 实测 offset 1、3、5 对应每次两条连续位置，与文档页偏移描述不一致；本接口按实测一基位置传递，服务变动时须复核。结果排序和总数可变化；指标、主题名称与范围均为 SciVal/Scopus 口径，不代表全部成果。'}

def detail(topic_id):
    _id(topic_id, True)
    raw, key = _fetch(topic_id, {}, BASE)
    item = _item(raw.get('topic'), key)
    if item['id'] != int(topic_id):
        raise RuntimeError('SciVal 返回主题 ID 不一致')
    return {'source': 'Elsevier SciVal Topic Lookup API', 'documentation': DOC, 'topic': item, 'note': '主题与主题簇来自 SciVal 基于 Scopus 的分类；不是可比拟所有学术研究的完整主题目录。'}
