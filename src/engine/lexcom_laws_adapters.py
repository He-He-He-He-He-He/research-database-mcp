"""司法部法通网涉外法律法规与域外法律译本索引。"""
import release_runtime
import re
from urllib.parse import urlencode
from lexcom_cases_adapters import BASE, _json, pdf_text

def chinese_laws(keyword='', page=1, size=10, mode='title'):
    """检索国内涉外法律法规；保留平台返回的原始状态和日期。"""
    page, size = (int(page), int(size))
    if page < 1 or not 1 <= size <= 100 or mode not in ('title', 'content'):
        raise ValueError('页码、每页数量或检索模式无效')
    p = {'current': page, 'size': size}
    if keyword:
        p.update(keyword=keyword, searchType=mode)
    result = _json('law/chinese/page', p)
    if not isinstance(result, dict) or not isinstance(result.get('records'), list):
        raise RuntimeError('涉外法律目录结构变化')
    return {**result, 'toolkit_source_url': BASE + 'law/chinese/page?' + urlencode(p), 'toolkit_note': '目录状态和日期为平台记录；应核验官方法律正文及现行效力。源更新可能改变跨页顺序。'}

def chinese_detail(law_id):
    if not re.fullmatch('\\d+', str(law_id)):
        raise ValueError('法律 ID 须为数字')
    return _json('law/chinese/query', {'id': law_id})

def foreign_laws(page=1, size=10, country_code=''):
    """查询域外法律译本目录（国家代码为平台采用的代码）。"""
    page, size = (int(page), int(size))
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('页码须大于 0、每页数量须为 1—100')
    p = {'current': page, 'size': size}
    if country_code:
        p['countryCode'] = country_code
    result = _json('law/foreign/translation/page', p)
    if not isinstance(result, dict) or not isinstance(result.get('records'), list):
        raise RuntimeError('域外译本目录结构变化')
    return {**result, 'toolkit_source_url': BASE + 'law/foreign/translation/page?' + urlencode(p), 'toolkit_note': '译本目录非该国官方现行法律的证明；须核验原文、翻译时间和效力。源更新可能改变跨页顺序。'}

def foreign_detail(law_id):
    if not re.fullmatch('\\d+', str(law_id)):
        raise ValueError('法律 ID 须为数字')
    return _json('law/foreign/translation/query', {'id': law_id})
