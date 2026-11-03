"""Discover OCHA HAPI data availability, geographies and related metadata."""
import release_runtime
import re
from ocha_hapi_adapter import _get
ALLOWED = {'dataset': {'dataset_hdx_id', 'dataset_hdx_stub', 'dataset_hdx_title', 'hdx_provider_stub', 'hdx_provider_name'}, 'resource': {'resource_hdx_id', 'format', 'update_date_min', 'update_date_max', 'dataset_hdx_id', 'dataset_hdx_stub', 'dataset_hdx_title', 'dataset_hdx_provider_stub', 'dataset_hdx_provider_name'}, 'location': {'id', 'code', 'name', 'has_hrp', 'in_gho', 'start_date', 'end_date'}, 'admin1': {'id', 'location_ref', 'code', 'name', 'location_code', 'location_name', 'start_date', 'end_date'}, 'admin2': {'id', 'admin1_ref', 'location_ref', 'code', 'name', 'admin1_code', 'admin1_name', 'location_code', 'location_name', 'start_date', 'end_date'}, 'currency': {'code'}, 'org': {'acronym', 'name', 'org_type_code', 'org_type_description'}, 'org-type': {'code', 'description'}, 'sector': {'code', 'name'}, 'wfp-commodity': {'code', 'category', 'name'}, 'wfp-market': {'code', 'name', 'has_hrp', 'in_gho', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level'}, 'data-availability': {'category', 'subcategory', 'hapi_updated_date_min', 'hapi_updated_date_max', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level'}}

def discover(kind, filters=None, limit=20, offset=0):
    if kind not in ALLOWED:
        raise ValueError('未知元数据类别')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('每页须为 1 至 100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('起始位置超限')
    if filters is None:
        filters = {}
    if not isinstance(filters, dict) or len(filters) > 10 or any((k not in ALLOWED[kind] for k in filters)):
        raise ValueError('无效筛选字段；请查阅该类别的可选字段')
    for k, v in filters.items():
        if not isinstance(v, (str, int, bool)) or len(str(v)) > 200:
            raise ValueError('筛选值无效')
    p = {**filters, 'limit': limit, 'offset': offset, 'output_format': 'json'}
    x = _get('metadata/' + kind, p)
    x['kind'] = kind
    x['allowed_filters'] = sorted(ALLOWED[kind])
    x['note'] = '当前 HAPI 元数据和可用性，不代表历史时点已公开，也不保证全国或全部数据覆盖。可用性更新时间不是观察日期；请进一步读取资源来源、许可、报告期和数据定义。'
    return x
