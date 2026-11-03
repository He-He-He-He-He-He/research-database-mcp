"""司法部法通网区域国别法务指南。"""
import release_runtime
import re
from lexcom_cases_adapters import _json, pdf_text

def guides(page=1, size=10, country_code=''):
    """按国家代码分页查询，返回网站原始字段。"""
    page, size = (int(page), int(size))
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('页码须大于 0，每页数量为 1—100')
    params = {'current': page, 'size': size}
    if country_code:
        params['countryCode'] = country_code
    return _json('guide/country/page', params)

def detail(guide_id):
    if not re.fullmatch('\\d+', str(guide_id)):
        raise ValueError('指南 ID 须为数字')
    return _json('guide/country/query', {'id': guide_id})
