"""Anonymous Pharmacodia drug-card preview; no sign-in or detail access."""
import release_runtime
import re
import requests
URL = 'https://dapi.pharmacodia.com/api/drug/getDrug'

def safe(value):
    if value is None or type(value) is int:
        return value
    if isinstance(value, str) and len(value) <= 1000 and (not re.search('https?://|[?&](?:token|session|key)=', value, re.I)):
        return value
    return None

def search(keyword, page=1, limit=20):
    if not isinstance(keyword, str) or not 1 <= len(keyword.strip()) <= 100 or any((ord(c) < 32 for c in keyword)):
        raise ValueError('关键词须为1至100字单行文本')
    if type(page) is not int or not 1 <= page <= 1000 or type(limit) is not int or (not 1 <= limit <= 20):
        raise ValueError('页码或数量无效')
    try:
        r = requests.post(URL, json={'qs': keyword.strip(), 'page': page, 'size': 20, 'searchType': 'QS'}, timeout=25)
        r.raise_for_status()
        j = r.json()
    except (requests.RequestException, ValueError):
        raise RuntimeError('药渡预览请求失败') from None
    rows = j.get('data') if isinstance(j, dict) and str(j.get('code')) == '0' else None
    if not isinstance(rows, list) or len(rows) > 20:
        raise RuntimeError('药渡预览响应异常')

    def first(obj, key):
        if not isinstance(obj, dict):
            return None
        data = obj.get('data')
        item = data[0] if isinstance(data, list) and data and isinstance(data[0], dict) else {}
        return {'first_raw': safe(item.get(key)), 'site_count_raw': safe(obj.get('count'))}
    items = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('id'), str) or (not re.fullmatch('[0-9]{1,64}', row['id'])):
            raise RuntimeError('药渡预览编号异常')
        cn, en = (safe(row.get('cnName')), safe(row.get('enName')))
        if not cn and (not en):
            raise RuntimeError('药渡预览名称缺失')

        def status(k):
            v = row.get(k)
            return safe(v.get('name')) if isinstance(v, dict) else None
        items.append({'id': row['id'], 'chinese_name': cn, 'english_name': en, 'target_preview': first(row.get('targetVo'), 'enShortName'), 'mechanism_preview': first(row.get('moa'), 'name'), 'first_approval_country_preview': first(row.get('firstApprovalCountry'), 'name'), 'first_approval_year_raw': safe(row.get('firstApprovalDateFilter')), 'origin_company_preview': first(row.get('originCompany'), 'name'), 'active_company_preview': first(row.get('activeCompany'), 'name'), 'active_indication_preview': first(row.get('activeIndication'), 'name'), 'global_highest_status_raw': status('highestStatus'), 'china_highest_status_raw': status('chinaHighestStatus')})
    return {'source': '药渡数据匿名公开卡片预览', 'query': keyword.strip(), 'page': page, 'source_page_items': len(items), 'requested_source_size': 20, 'truncated': len(items) > limit, 'items': items[:limit], 'note': '来源只返回公开预览，未提供总数或回显页码/关键词；结果可匹配名称之外信息且排序可能变化。卡片 count 为站方原值，不能推断总数或完整性；机构、详情和数据权限未验证，信息须回原始药品监管来源核实，不用于诊疗决策。若 truncated 为 true，下一页会遗漏本页余项。'}
