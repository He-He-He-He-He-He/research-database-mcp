"""OCHA HAPI v2 parameterised thematic data queries; whitelist from 2026-11-02 OpenAPI."""
import release_runtime
import re
from ocha_hapi_adapter import _get
THEMES = {'baseline-population': ('geography-infrastructure/baseline-population', ['gender', 'age_range', 'population_min', 'population_max', 'has_hrp', 'in_gho', 'start_date', 'end_date', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level']), 'conflict-events': ('coordination-context/conflict-events', ['event_type', 'has_hrp', 'in_gho', 'start_date', 'end_date', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level']), 'food-prices-market-monitor': ('food-security-nutrition-poverty/food-prices-market-monitor', ['market_code', 'market_name', 'commodity_code', 'commodity_category', 'commodity_name', 'price_flag', 'price_type', 'price_min', 'price_max', 'has_hrp', 'in_gho', 'start_date', 'end_date', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level']), 'food-security': ('food-security-nutrition-poverty/food-security', ['ipc_phase', 'ipc_type', 'has_hrp', 'in_gho', 'start_date', 'end_date', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level']), 'funding': ('coordination-context/funding', ['appeal_code', 'appeal_type', 'location_code', 'location_name', 'has_hrp', 'in_gho', 'start_date', 'end_date']), 'humanitarian-needs': ('affected-people/humanitarian-needs', ['category', 'sector_code', 'population_status', 'population_min', 'population_max', 'sector_name', 'has_hrp', 'in_gho', 'start_date', 'end_date', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level']), 'idps': ('affected-people/idps', ['has_hrp', 'in_gho', 'start_date', 'end_date', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level']), 'national-risk': ('coordination-context/national-risk', ['risk_class', 'global_rank_min', 'global_rank_max', 'overall_risk_min', 'overall_risk_max', 'hazard_exposure_risk_min', 'hazard_exposure_risk_max', 'vulnerability_risk_min', 'vulnerability_risk_max', 'coping_capacity_risk_min', 'coping_capacity_risk_max', 'location_code', 'location_name', 'has_hrp', 'in_gho', 'start_date', 'end_date']), 'operational-presence': ('coordination-context/operational-presence', ['sector_code', 'sector_name', 'org_acronym', 'org_name', 'has_hrp', 'in_gho', 'start_date', 'end_date', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level']), 'poverty-rate': ('food-security-nutrition-poverty/poverty-rate', ['mpi_min', 'mpi_max', 'has_hrp', 'in_gho', 'start_date', 'end_date', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin_level']), 'rainfall': ('climate/rainfall', ['aggregation_period', 'version', 'has_hrp', 'in_gho', 'start_date', 'end_date', 'location_code', 'location_name', 'admin1_code', 'admin1_name', 'admin2_code', 'admin2_name', 'admin_level']), 'refugees-persons-of-concern': ('affected-people/refugees-persons-of-concern', ['population_group', 'population_min', 'population_max', 'gender', 'age_range', 'origin_location_code', 'origin_location_name', 'origin_has_hrp', 'origin_in_gho', 'asylum_location_code', 'asylum_location_name', 'asylum_has_hrp', 'asylum_in_gho', 'start_date', 'end_date']), 'returnees': ('affected-people/returnees', ['population_group', 'gender', 'age_range', 'min_age', 'max_age', 'origin_location_code', 'origin_location_name', 'origin_has_hrp', 'origin_in_gho', 'asylum_location_code', 'asylum_location_name', 'asylum_has_hrp', 'asylum_in_gho', 'start_date', 'end_date'])}

def describe():
    return {'documentation': 'https://hapi.humdata.org/docs', 'themes': {k: {'endpoint': v[0], 'filters': v[1]} for k, v in THEMES.items()}, 'note': '字段清单根据 2026-11-02 官方 OpenAPI 快照；以实时官方文档为准。'}

def query(theme, filters, limit=20, offset=0):
    if theme not in THEMES:
        raise ValueError('未知主题，请先读取主题目录')
    path, allowed = THEMES[theme]
    if not isinstance(filters, dict) or not filters or len(filters) > 15 or any((k not in allowed for k in filters)):
        raise ValueError('过滤条件应为该主题允许字段组成的 JSON 对象')
    if not any((filters.get(k) for k in ('location_code', 'origin_location_code', 'asylum_location_code'))):
        raise ValueError('请指定国家代码；跨国迁移应明确来源国或庇护国')
    for k, v in filters.items():
        if not isinstance(v, (str, int, float, bool)) or len(str(v)) > 150:
            raise ValueError('过滤值必须为长度受限的标量')
        if k in ('location_code', 'origin_location_code', 'asylum_location_code') and (not re.fullmatch('[A-Z]{3}', str(v))):
            raise ValueError('国家代码须为三个大写字母')
    if isinstance(limit, bool) or not isinstance(limit, int) or (not 1 <= limit <= 100):
        raise ValueError('每页须为 1 至 100')
    if isinstance(offset, bool) or not isinstance(offset, int) or (not 0 <= offset <= 100000):
        raise ValueError('起始位置超限')
    params = {**filters, 'limit': limit, 'offset': offset, 'output_format': 'json'}
    out = _get(path, params)
    out['theme'] = theme
    out['note'] = '结果保留上游原始字段和来源资源 ID；缺失不是零。时间筛选及统计期、人口角色、地理范围、币种、单位、估计或预测属性须结合数据源定义。接口为当前版本，历史值可能已修订，不能仅凭观察年份认定历史可得。'
    return out
