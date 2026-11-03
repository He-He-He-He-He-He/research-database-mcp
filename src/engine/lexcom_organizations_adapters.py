"""司法部法通网涉外法律服务机构公开查询。"""
import release_runtime
import re
from lexcom_cases_adapters import _json

def organizations(keyword='', page=1, size=10, province=''):
    """搜索公开机构目录，字段和空值保持官网原始形式。"""
    page, size = (int(page), int(size))
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('页码须大于 0，每页数量为 1—100')
    params = {'current': page, 'size': size}
    if keyword:
        params['keyword'] = keyword
    if province:
        params['province'] = province
    return _json('portal/lr/org/page', params)

def detail(org_id):
    if not re.fullmatch('\\d+', str(org_id)):
        raise ValueError('机构 ID 须为数字')
    return _json('portal/lr/org/query', {'id': org_id})
